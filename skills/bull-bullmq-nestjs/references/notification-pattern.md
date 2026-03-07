# Bull/BullMQ — Cola de Notificaciones Push (FCM)

## Fuentes

- Firebase Admin SDK: https://firebase.google.com/docs/admin/setup
- FCM send messages: https://firebase.google.com/docs/cloud-messaging/send-message
- BullMQ concurrency: https://docs.bullmq.io/guide/workers/concurrency

---

## 1. Servicio de notificaciones (producer + Firebase)

```bash
npm install firebase-admin
```

```typescript
// src/modules/notifications/notifications.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import * as admin from 'firebase-admin';
import { PrismaService } from '../../infrastructure/database/prisma.service';

export const NOTIFICATIONS_QUEUE = 'notifications';
export const PUSH_NOTIFICATION_JOB = 'push-notification';

export interface PushNotificationPayload {
  tokens: string[];
  title: string;
  body: string;
  data?: Record<string, string>;  // Deep link y metadata
}

@Injectable()
export class NotificationsService {
  private readonly logger = new Logger(NotificationsService.name);

  constructor(
    @InjectQueue(NOTIFICATIONS_QUEUE) private readonly notificationsQueue: Queue,
    private readonly prisma: PrismaService,
  ) {
    // Inicializar Firebase Admin si no está inicializado
    if (!admin.apps.length) {
      admin.initializeApp({
        credential: admin.credential.cert(
          JSON.parse(process.env.FCM_SERVICE_ACCOUNT!)
        ),
      });
    }
  }

  // Encolar notificación (no bloquea el caller)
  async sendPushNotification(payload: PushNotificationPayload): Promise<void> {
    await this.notificationsQueue.add(PUSH_NOTIFICATION_JOB, payload, {
      attempts: 3,
      backoff: { type: 'exponential', delay: 2000 },
    });
  }

  // Envío directo a FCM (llamado desde el processor)
  async deliverToFCM(payload: PushNotificationPayload): Promise<void> {
    if (payload.tokens.length === 0) return;

    const message: admin.messaging.MulticastMessage = {
      tokens: payload.tokens,
      notification: {
        title: payload.title,
        body: payload.body,
      },
      data: payload.data,
      android: {
        priority: 'high',
        notification: { sound: 'default' },
      },
      apns: {
        payload: { aps: { sound: 'default', badge: 1 } },
      },
    };

    const response = await admin.messaging().sendEachForMulticast(message);

    this.logger.log(
      `FCM: ${response.successCount} sent, ${response.failureCount} failed`
    );

    // Gestionar tokens inválidos/expirados
    if (response.failureCount > 0) {
      const invalidTokens: string[] = [];

      response.responses.forEach((resp, idx) => {
        if (!resp.success) {
          const errorCode = resp.error?.code;
          if (
            errorCode === 'messaging/registration-token-not-registered' ||
            errorCode === 'messaging/invalid-registration-token'
          ) {
            invalidTokens.push(payload.tokens[idx]);
          } else {
            this.logger.warn(`FCM error for token ${payload.tokens[idx]}: ${errorCode}`);
          }
        }
      });

      // Limpiar tokens inválidos de la base de datos
      if (invalidTokens.length > 0) {
        await this.removeInvalidFcmTokens(invalidTokens);
      }
    }
  }

  // Registrar token FCM de un dispositivo
  async registerFcmToken(userId: string, token: string): Promise<void> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { fcmTokens: true },
    });

    if (!user) return;

    // Evitar duplicados en el array
    if (!user.fcmTokens.includes(token)) {
      await this.prisma.user.update({
        where: { id: userId },
        data: { fcmTokens: { push: token } },
      });
    }
  }

  private async removeInvalidFcmTokens(tokens: string[]): Promise<void> {
    // Buscar y limpiar tokens inválidos de todos los usuarios
    const users = await this.prisma.user.findMany({
      where: { fcmTokens: { hasSome: tokens } },
      select: { id: true, fcmTokens: true },
    });

    await Promise.all(
      users.map(user =>
        this.prisma.user.update({
          where: { id: user.id },
          data: { fcmTokens: user.fcmTokens.filter(t => !tokens.includes(t)) },
        })
      )
    );

    this.logger.log(`Removed ${tokens.length} invalid FCM tokens`);
  }
}
```

---

## 2. Processor de notificaciones

```typescript
// notifications.processor.ts
import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Job } from 'bullmq';
import { Logger } from '@nestjs/common';
import { NotificationsService, NOTIFICATIONS_QUEUE, PUSH_NOTIFICATION_JOB, PushNotificationPayload } from './notifications.service';

@Processor(NOTIFICATIONS_QUEUE, {
  concurrency: 5,  // Procesar hasta 5 notificaciones en paralelo
})
export class NotificationsProcessor extends WorkerHost {
  private readonly logger = new Logger(NotificationsProcessor.name);

  constructor(private readonly notificationsService: NotificationsService) {
    super();
  }

  async process(job: Job<PushNotificationPayload>): Promise<void> {
    if (job.name === PUSH_NOTIFICATION_JOB) {
      await this.notificationsService.deliverToFCM(job.data);
    }
  }

  @OnWorkerEvent('failed')
  onFailed(job: Job, error: Error) {
    if (job.attemptsMade >= (job.opts.attempts ?? 3)) {
      this.logger.error(
        `Notification job ${job.id} permanently failed after ${job.attemptsMade} attempts: ${error.message}`
      );
      // Aquí se podría enviar alerta a Cloud Monitoring o Slack
    }
  }
}
```

---

## 3. Módulo de notificaciones

```typescript
// notifications.module.ts
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { NOTIFICATIONS_QUEUE } from './notifications.service';
import { NotificationsService } from './notifications.service';
import { NotificationsProcessor } from './notifications.processor';
import { NotificationsController } from './notifications.controller';

@Module({
  imports: [BullModule.registerQueue({ name: NOTIFICATIONS_QUEUE })],
  controllers: [NotificationsController],
  providers: [NotificationsService, NotificationsProcessor],
  exports: [NotificationsService],
})
export class NotificationsModule {}
```

---

## 4. Endpoint para registrar token FCM desde la app móvil

```typescript
// notifications.controller.ts
import { Controller, Post, Body, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { CurrentUser } from '../auth/decorators/current-user.decorator';
import { NotificationsService } from './notifications.service';
import { IsString } from 'class-validator';

class RegisterTokenDto {
  @IsString()
  token: string;
}

@Controller('notifications')
@UseGuards(JwtAuthGuard)
export class NotificationsController {
  constructor(private readonly service: NotificationsService) {}

  @Post('token')
  async registerToken(
    @CurrentUser() userId: string,
    @Body() dto: RegisterTokenDto,
  ) {
    await this.service.registerFcmToken(userId, dto.token);
    return { registered: true };
  }
}
```
