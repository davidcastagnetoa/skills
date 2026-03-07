# Bull/BullMQ + NestJS — Setup y Configuración

## Fuentes

- @nestjs/bull: https://docs.nestjs.com/techniques/queues
- BullMQ Docs: https://docs.bullmq.io/
- Redis connection: https://docs.bullmq.io/guide/connections

---

## 1. Instalación

```bash
# BullMQ (versión moderna, recomendada)
npm install @nestjs/bullmq bullmq

# O Bull (legacy, ampliamente usado)
npm install @nestjs/bull bull
npm install -D @types/bull
```

---

## 2. Variables de entorno

```env
REDIS_URL=redis://localhost:6379          # Desarrollo local
# En producción GCP, Memorystore no expone URL pública — usar IP privada
REDIS_HOST=10.0.0.5
REDIS_PORT=6379
```

---

## 3. Configuración del módulo global (BullMQ)

```typescript
// src/infrastructure/queues/queues.module.ts
import { Global, Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { ConfigService } from '@nestjs/config';

export const REMINDERS_QUEUE = 'reminders';
export const NOTIFICATIONS_QUEUE = 'notifications';

@Global()
@Module({
  imports: [
    BullModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get('REDIS_HOST', 'localhost'),
          port: config.get<number>('REDIS_PORT', 6379),
          // En producción con Memorystore (GCP): usar enableOfflineQueue: false
          enableOfflineQueue: config.get('NODE_ENV') !== 'production',
          maxRetriesPerRequest: null, // Requerido por BullMQ
        },
        defaultJobOptions: {
          attempts: 3,
          backoff: { type: 'exponential', delay: 1000 },
          removeOnComplete: { count: 100 },  // Mantener últimos 100 completados para debug
          removeOnFail: { count: 500 },      // Mantener últimos 500 fallidos para análisis
        },
      }),
    }),

    // Registrar las colas del proyecto
    BullModule.registerQueue(
      { name: REMINDERS_QUEUE },
      { name: NOTIFICATIONS_QUEUE },
    ),
  ],
  exports: [BullModule],
})
export class QueuesModule {}
```

---

## 4. Configuración para desarrollo con Bull (legacy)

```typescript
// Si se usa @nestjs/bull en lugar de @nestjs/bullmq:
import { BullModule } from '@nestjs/bull';

BullModule.forRootAsync({
  inject: [ConfigService],
  useFactory: (config: ConfigService) => ({
    redis: {
      host: config.get('REDIS_HOST', 'localhost'),
      port: config.get<number>('REDIS_PORT', 6379),
    },
  }),
}),
```

---

## 5. Bull Board — dashboard de monitorización (solo desarrollo)

```bash
npm install @bull-board/api @bull-board/nestjs @bull-board/express
```

```typescript
// Añadir en AppModule (solo en development)
import { BullBoardModule } from '@bull-board/nestjs';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';

// En AppModule imports:
...(process.env.NODE_ENV === 'development' ? [
  BullBoardModule.forRoot({ route: '/queues', adapter: ExpressAdapter }),
  BullBoardModule.forFeature(
    { name: REMINDERS_QUEUE, adapter: BullMQAdapter },
    { name: NOTIFICATIONS_QUEUE, adapter: BullMQAdapter },
  ),
] : []),
```

Accesible en `http://localhost:3000/queues` durante el desarrollo.
Referencia: https://github.com/felixmosh/bull-board

---

## 6. Estructura recomendada de archivos

```
src/modules/reminders/
├── reminders.module.ts          ← Importa BullModule.registerQueue
├── reminders.service.ts         ← Producer (añade jobs a la cola)
├── reminders.processor.ts       ← Consumer (procesa los jobs)
└── dto/
    └── reminder-job.dto.ts      ← Tipado del payload del job
```
