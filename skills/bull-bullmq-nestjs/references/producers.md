# Bull/BullMQ — Producers: Encolado de Jobs

## Fuente

- BullMQ adding jobs: https://docs.bullmq.io/guide/jobs

---

## 1. Tipos de jobs y cuándo usar cada uno

| Tipo              | Cuándo usar                    | Código                                               |
| ----------------- | ------------------------------ | ---------------------------------------------------- |
| **Inmediato**     | Procesar lo antes posible      | `queue.add(name, data)`                              |
| **Delayed**       | Ejecutar en fecha/hora futura  | `queue.add(name, data, { delay: ms })`               |
| **Repeatable**    | Ejecutar periódicamente (cron) | `queue.add(name, data, { repeat: { cron: '...' } })` |
| **Con prioridad** | Procesar antes que otros       | `queue.add(name, data, { priority: 1 })`             |

---

## 2. Jobs inmediatos (notificaciones de unirse a círculo)

```typescript
// Notificación bienvenida al unirse a un círculo
await this.notificationsQueue.add('welcome-to-circle', {
  userId: newMemberId,
  circleName: circle.nombre,
  tokens: [user.fcmToken],
});
```

---

## 3. Jobs delayed (recordatorios de cumpleaños)

```typescript
const delayMs = targetDate.getTime() - Date.now();

await this.remindersQueue.add(
  'birthday-reminder',
  { profileId, profileNombre, circleIds },
  {
    jobId: `reminder:${profileId}:${targetDate.getFullYear()}`,  // Determinístico
    delay: delayMs,
    attempts: 3,
    backoff: { type: 'exponential', delay: 1000 },
    removeOnComplete: true,
    removeOnFail: false,   // Mantener fallidos para diagnóstico
  }
);
```

---

## 4. Inspeccionar y gestionar jobs

```typescript
// Ver jobs en espera
const waiting = await queue.getWaiting();

// Ver jobs delayed (programados para el futuro)
const delayed = await queue.getDelayed();

// Ver jobs fallidos
const failed = await queue.getFailed();

// Cancelar un job específico por ID
const job = await queue.getJob('reminder:profile-123:2026');
if (job) await job.remove();

// Vaciar todos los jobs de un estado (cuidado en producción)
await queue.clean(0, 100, 'completed');
```

---

## 5. Verificar si un job ya existe (para idempotencia manual)

```typescript
async scheduleIfNotExists(profileId: string, delay: number): Promise<void> {
  const jobId = `reminder:${profileId}:${new Date().getFullYear()}`;

  const existingJob = await this.queue.getJob(jobId);

  if (existingJob) {
    const state = await existingJob.getState();
    this.logger.log(`Job ${jobId} already exists in state: ${state}`);

    // Si el delay cambió significativamente (>1h), reprogramar
    const currentDelay = existingJob.opts.delay ?? 0;
    if (Math.abs(currentDelay - delay) > 3600000) {
      await existingJob.remove();
      this.logger.log(`Rescheduling job ${jobId} due to delay change`);
    } else {
      return; // Job ya existe con delay similar, no hacer nada
    }
  }

  await this.queue.add('birthday-reminder', { profileId }, { jobId, delay });
}
```
