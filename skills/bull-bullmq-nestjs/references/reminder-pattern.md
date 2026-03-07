# Bull/BullMQ — Patrón de Recordatorios de Cumpleaños (Algoritmo 3 HADA)

## Fuentes

- Delayed jobs: https://docs.bullmq.io/guide/jobs/delayed
- Job IDs: https://docs.bullmq.io/guide/jobs/job-ids
- Removing jobs: https://docs.bullmq.io/guide/jobs/removing-jobs

---

## Implementación completa del Algoritmo 3

### 1. DTO del job — tipado del payload

```typescript
// dto/reminder-job.dto.ts
export interface ReminderJobData {
  profileId: string;
  profileNombre: string;
  birthdayDate: string;           // ISO string de la fecha de cumpleaños
  scheduledAt: number;            // timestamp — para idempotencia
  circleIds: string[];            // Círculos a notificar
}

export const REMINDER_JOB_NAME = 'birthday-reminder';
```

---

### 2. Producer — servicio que programa recordatorios

```typescript
// reminders.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '../../infrastructure/database/prisma.service';
import { REMINDERS_QUEUE, REMINDER_JOB_NAME, ReminderJobData } from './dto/reminder-job.dto';

@Injectable()
export class RemindersService {
  private readonly logger = new Logger(RemindersService.name);

  constructor(
    @InjectQueue(REMINDERS_QUEUE) private readonly remindersQueue: Queue,
    private readonly prisma: PrismaService,
  ) {}

  /**
   * Algoritmo 3: Programar o reprogramar el recordatorio de un perfil.
   * Llamar cuando se crea o actualiza birthdayDate.
   */
  async scheduleReminder(
    profileId: string,
    birthdayDate: Date,
    offsetDays = 7,
  ): Promise<void> {
    // Paso 1: Calcular la próxima fecha de recordatorio
    const reminderDate = this.calculateNextReminderDate(birthdayDate, offsetDays);
    const delay = reminderDate.getTime() - Date.now();

    this.logger.log(`Scheduling reminder for profile ${profileId} at ${reminderDate.toISOString()}`);

    // Paso 2: jobId determinístico — evita duplicados automáticamente
    // Si ya existe un job con este ID, Bull lo reemplaza
    const jobId = `reminder:${profileId}:${reminderDate.getFullYear()}`;

    // Paso 3: Obtener datos del perfil para el payload del job
    const profile = await this.prisma.profile.findUnique({
      where: { id: profileId },
      select: {
        nombre: true,
        lists: {
          select: { circleId: true },
        },
      },
    });

    if (!profile) {
      this.logger.warn(`Profile ${profileId} not found, skipping reminder scheduling`);
      return;
    }

    const circleIds = [...new Set(profile.lists.map(l => l.circleId))];

    const jobData: ReminderJobData = {
      profileId,
      profileNombre: profile.nombre,
      birthdayDate: birthdayDate.toISOString(),
      scheduledAt: reminderDate.getTime(),
      circleIds,
    };

    // Paso 4: Cancelar job previo si existe, encolar nuevo
    await this.remindersQueue.remove(jobId).catch(() => {
      // Ignorar error si el job no existía
    });

    await this.remindersQueue.add(REMINDER_JOB_NAME, jobData, {
      jobId,
      delay: Math.max(delay, 0),  // Nunca negativo
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 },
    });

    // Paso 5: Persistir la fecha programada en el perfil
    await this.prisma.profile.update({
      where: { id: profileId },
      data: { reminderScheduledAt: reminderDate },
    });
  }

  async cancelReminder(profileId: string): Promise<void> {
    const now = new Date();
    const jobId = `reminder:${profileId}:${now.getFullYear()}`;
    await this.remindersQueue.remove(jobId).catch(() => {});

    await this.prisma.profile.update({
      where: { id: profileId },
      data: { reminderScheduledAt: null },
    });
  }

  private calculateNextReminderDate(birthdayDate: Date, offsetDays: number): Date {
    const now = new Date();
    const thisYear = now.getFullYear();

    // Crear fecha de recordatorio para este año
    let reminderDate = new Date(thisYear, birthdayDate.getMonth(), birthdayDate.getDate());
    reminderDate.setDate(reminderDate.getDate() - offsetDays);
    reminderDate.setHours(9, 0, 0, 0); // Enviar a las 9:00 AM

    // Si la fecha ya pasó este año, calcular para el siguiente
    if (reminderDate <= now) {
      reminderDate = new Date(thisYear + 1, birthdayDate.getMonth(), birthdayDate.getDate());
      reminderDate.setDate(reminderDate.getDate() - offsetDays);
      reminderDate.setHours(9, 0, 0, 0);
    }

    return reminderDate;
  }
}
```

---

### 3. Processor — worker que procesa el job

```typescript
// reminders.processor.ts
import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { Logger } from '@nestjs/common';
import { PrismaService } from '../../infrastructure/database/prisma.service';
import { NotificationsService } from '../notifications/notifications.service';
import { REMINDERS_QUEUE, REMINDER_JOB_NAME, ReminderJobData } from './dto/reminder-job.dto';

@Processor(REMINDERS_QUEUE)
export class RemindersProcessor extends WorkerHost {
  private readonly logger = new Logger(RemindersProcessor.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly notifications: NotificationsService,
  ) {
    super();
  }

  async process(job: Job<ReminderJobData>): Promise<void> {
    this.logger.log(`Processing reminder job ${job.id} for profile ${job.data.profileId}`);

    // Idempotencia: verificar que el job sigue siendo válido
    const profile = await this.prisma.profile.findUnique({
      where: { id: job.data.profileId },
      select: { reminderScheduledAt: true, nombre: true },
    });

    if (!profile) {
      this.logger.warn(`Profile ${job.data.profileId} deleted, skipping reminder`);
      return;
    }

    // Si el timestamp programado no coincide, el recordatorio fue reprogramado
    if (profile.reminderScheduledAt?.getTime() !== job.data.scheduledAt) {
      this.logger.log(`Reminder for ${job.data.profileId} was rescheduled, skipping stale job`);
      return;
    }

    // Obtener tokens FCM de todos los miembros de los círculos
    const members = await this.prisma.circleMember.findMany({
      where: { circleId: { in: job.data.circleIds } },
      include: { user: { select: { fcmTokens: true } } },
    });

    const tokens = [...new Set(
      members.flatMap(m => m.user.fcmTokens).filter(Boolean)
    )];

    if (tokens.length === 0) {
      this.logger.log(`No FCM tokens found for circles of profile ${job.data.profileId}`);
      return;
    }

    // Enviar notificación
    const birthday = new Date(job.data.birthdayDate);
    const daysUntil = Math.ceil((birthday.getTime() - Date.now()) / (1000 * 60 * 60 * 24));

    await this.notifications.sendPushNotification({
      tokens,
      title: `🎁 Cumpleaños de ${job.data.profileNombre}`,
      body: daysUntil <= 0
        ? `¡Hoy es el cumpleaños de ${job.data.profileNombre}! ¿Ya tienes su regalo?`
        : `El cumpleaños de ${job.data.profileNombre} es en ${daysUntil} días`,
      data: {
        type: 'birthday_reminder',
        profileId: job.data.profileId,
        // Deep link para la app móvil
        deepLink: `hada://profiles/${job.data.profileId}/lists`,
      },
    });

    this.logger.log(`Reminder sent for profile ${job.data.profileId} to ${tokens.length} devices`);
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job<ReminderJobData>, error: Error) {
    this.logger.error(
      `Reminder job ${job.id} failed (attempt ${job.attemptsMade}): ${error.message}`,
      error.stack,
    );
  }

  @OnWorkerEvent('completed')
  onCompleted(job: Job<ReminderJobData>) {
    this.logger.log(`Reminder job ${job.id} completed successfully`);
  }
}
```

---

### 4. Módulo completo

```typescript
// reminders.module.ts
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { REMINDERS_QUEUE } from './dto/reminder-job.dto';
import { RemindersService } from './reminders.service';
import { RemindersProcessor } from './reminders.processor';
import { RemindersController } from './reminders.controller';
import { NotificationsModule } from '../notifications/notifications.module';

@Module({
  imports: [
    BullModule.registerQueue({ name: REMINDERS_QUEUE }),
    NotificationsModule,
  ],
  controllers: [RemindersController],
  providers: [RemindersService, RemindersProcessor],
  exports: [RemindersService],
})
export class RemindersModule {}
```
