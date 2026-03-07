# Migración Bull → GCP Cloud Tasks (Producción)

## Fuentes

- Cloud Tasks docs: https://cloud.google.com/tasks/docs
- Cloud Tasks HTTP targets: https://cloud.google.com/tasks/docs/creating-http-target-tasks
- Cloud Tasks con NestJS: https://cloud.google.com/tasks/docs/creating-http-target-tasks#node.js

---

## Estrategia: misma interfaz, diferente implementación

La clave es abstraer la cola detrás de una interfaz común para que el código de negocio
(RemindersService, NotificationsService) no sepa si está usando Bull o Cloud Tasks.

```
Desarrollo:   NestJS → Bull → Redis local
Producción:   NestJS → Cloud Tasks → Cloud Run endpoint
```

---

## 1. Interfaz abstracta de scheduler

```typescript
// src/infrastructure/scheduler/scheduler.interface.ts
export interface ScheduleJobOptions {
  jobId?: string;
  delayMs?: number;
  attempts?: number;
}

export abstract class SchedulerService {
  abstract schedule(
    queueName: string,
    jobName: string,
    data: Record<string, unknown>,
    options?: ScheduleJobOptions,
  ): Promise<void>;

  abstract cancel(queueName: string, jobId: string): Promise<void>;
}
```

---

## 2. Implementación Bull (desarrollo)

```typescript
// src/infrastructure/scheduler/bull-scheduler.service.ts
import { Injectable } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { SchedulerService, ScheduleJobOptions } from './scheduler.interface';

@Injectable()
export class BullSchedulerService extends SchedulerService {
  constructor(
    @InjectQueue('reminders') private remindersQueue: Queue,
    @InjectQueue('notifications') private notificationsQueue: Queue,
  ) {
    super();
  }

  private getQueue(name: string): Queue {
    const queues: Record<string, Queue> = {
      reminders: this.remindersQueue,
      notifications: this.notificationsQueue,
    };
    return queues[name];
  }

  async schedule(queueName: string, jobName: string, data: any, options?: ScheduleJobOptions) {
    const queue = this.getQueue(queueName);
    await queue.remove(options?.jobId ?? '').catch(() => {});
    await queue.add(jobName, data, {
      jobId: options?.jobId,
      delay: options?.delayMs,
      attempts: options?.attempts ?? 3,
      backoff: { type: 'exponential', delay: 1000 },
    });
  }

  async cancel(queueName: string, jobId: string) {
    const queue = this.getQueue(queueName);
    const job = await queue.getJob(jobId);
    if (job) await job.remove();
  }
}
```

---

## 3. Implementación Cloud Tasks (producción)

```bash
npm install @google-cloud/tasks
```

```typescript
// src/infrastructure/scheduler/cloud-tasks-scheduler.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { CloudTasksClient } from '@google-cloud/tasks';
import { ConfigService } from '@nestjs/config';
import { SchedulerService, ScheduleJobOptions } from './scheduler.interface';

@Injectable()
export class CloudTasksSchedulerService extends SchedulerService {
  private readonly logger = new Logger(CloudTasksSchedulerService.name);
  private readonly client = new CloudTasksClient();

  constructor(private readonly config: ConfigService) {
    super();
  }

  async schedule(queueName: string, jobName: string, data: any, options?: ScheduleJobOptions) {
    const project = this.config.get('GCP_PROJECT_ID');
    const location = this.config.get('GCP_REGION', 'europe-west1');
    const apiUrl = this.config.get('API_BASE_URL');  // URL del Cloud Run

    const parent = this.client.queuePath(project, location, queueName);

    // Calcular scheduleTime si hay delay
    let scheduleTime;
    if (options?.delayMs && options.delayMs > 0) {
      const scheduleDate = new Date(Date.now() + options.delayMs);
      scheduleTime = {
        seconds: Math.floor(scheduleDate.getTime() / 1000),
        nanos: 0,
      };
    }

    const task = {
      name: options?.jobId
        ? `${parent}/tasks/${options.jobId.replace(/[^a-zA-Z0-9-_]/g, '-')}`
        : undefined,
      httpRequest: {
        url: `${apiUrl}/internal/jobs/${queueName}/${jobName}`,
        httpMethod: 'POST' as const,
        headers: {
          'Content-Type': 'application/json',
          // Auth interna entre Cloud Tasks y Cloud Run
          Authorization: `Bearer ${await this.getInternalToken()}`,
        },
        body: Buffer.from(JSON.stringify({ jobName, data, jobId: options?.jobId })).toString('base64'),
      },
      ...(scheduleTime ? { scheduleTime } : {}),
    };

    try {
      await this.client.createTask({ parent, task });
      this.logger.log(`Task scheduled: ${queueName}/${jobName}`);
    } catch (error: any) {
      if (error.code === 6) {
        // ALREADY_EXISTS — task con ese ID ya existe, es idempotente
        this.logger.log(`Task ${options?.jobId} already exists, skipping`);
      } else {
        throw error;
      }
    }
  }

  async cancel(queueName: string, jobId: string) {
    const project = this.config.get('GCP_PROJECT_ID');
    const location = this.config.get('GCP_REGION', 'europe-west1');
    const taskName = this.client.taskPath(
      project, location, queueName,
      jobId.replace(/[^a-zA-Z0-9-_]/g, '-')
    );
    await this.client.deleteTask({ name: taskName }).catch(() => {});
  }

  private async getInternalToken(): Promise<string> {
    // En Cloud Run, usar el metadata service para obtener un ID token
    const metadataUrl = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity';
    const audience = this.config.get('API_BASE_URL');
    const response = await fetch(`${metadataUrl}?audience=${audience}`, {
      headers: { 'Metadata-Flavor': 'Google' },
    });
    return response.text();
  }
}
```

---

## 4. Selector por entorno en el módulo

```typescript
// src/infrastructure/scheduler/scheduler.module.ts
import { Module } from '@nestjs/common';
import { SchedulerService } from './scheduler.interface';
import { BullSchedulerService } from './bull-scheduler.service';
import { CloudTasksSchedulerService } from './cloud-tasks-scheduler.service';

@Module({
  providers: [
    {
      provide: SchedulerService,
      useClass: process.env.NODE_ENV === 'production'
        ? CloudTasksSchedulerService
        : BullSchedulerService,
    },
  ],
  exports: [SchedulerService],
})
export class SchedulerModule {}
```

---

## 5. Endpoint interno para recibir Cloud Tasks

```typescript
// src/internal/jobs.controller.ts
// Este endpoint solo acepta peticiones de Cloud Tasks (validar Authorization header)
@Controller('internal/jobs')
export class InternalJobsController {
  constructor(
    private readonly remindersProcessor: RemindersProcessor,
    private readonly notificationsProcessor: NotificationsProcessor,
  ) {}

  @Post(':queue/:jobName')
  async handleJob(
    @Param('queue') queue: string,
    @Param('jobName') jobName: string,
    @Body() body: { data: any; jobId: string },
  ) {
    if (queue === 'reminders') {
      await this.remindersProcessor.process({ name: jobName, data: body.data } as any);
    } else if (queue === 'notifications') {
      await this.notificationsProcessor.process({ name: jobName, data: body.data } as any);
    }
    return { processed: true };
  }
}
```
