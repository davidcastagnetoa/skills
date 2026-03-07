# FCM — Gestión del Ciclo de Vida de Tokens

## Fuente

https://firebase.google.com/docs/cloud-messaging/manage-tokens

---

## 1. Registro y actualización de token desde el backend

```typescript
// src/modules/notifications/token.service.ts
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../infrastructure/database/prisma.service';

@Injectable()
export class TokenService {
  constructor(private readonly prisma: PrismaService) {}

  async registerToken(userId: string, token: string): Promise<void> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { fcmTokens: true },
    });
    if (!user) return;

    if (!user.fcmTokens.includes(token)) {
      await this.prisma.user.update({
        where: { id: userId },
        data: { fcmTokens: { push: token } },
      });
    }
  }

  async removeToken(userId: string, token: string): Promise<void> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { fcmTokens: true },
    });
    if (!user) return;

    await this.prisma.user.update({
      where: { id: userId },
      data: { fcmTokens: user.fcmTokens.filter(t => t !== token) },
    });
  }

  // Llamar al hacer logout — eliminar el token del dispositivo actual
  async removeTokenOnLogout(userId: string, token: string): Promise<void> {
    await this.removeToken(userId, token);
  }
}
```

---

## 2. Cuándo se invalida un token FCM

| Evento                                              | Token status                                                |
| --------------------------------------------------- | ----------------------------------------------------------- |
| Usuario desinstala la app                           | Inválido — FCM responde `registration-token-not-registered` |
| Usuario limpia datos de la app (Android)            | Inválido                                                    |
| Token no usado en 270 días                          | FCM puede invalidarlo silenciosamente                       |
| Nueva instalación de la app en el mismo dispositivo | Nuevo token generado                                        |
| Usuario hace logout                                 | Token sigue válido pero debe eliminarse de la BD            |

**Regla:** limpiar tokens inválidos **siempre** que FCM responda con error de registro.

---

## 3. Limpieza periódica de tokens obsoletos (job programado)

```typescript
// Añadir a RemindersModule como job de mantenimiento (cron semanal)
@Cron('0 3 * * 0')  // Cada domingo a las 3 AM
async cleanupStaleTokens(): Promise<void> {
  // Estrategia: enviar un mensaje silencioso de prueba a tokens antiguos
  // y eliminar los que fallen. Aquí simplemente limitamos el array a los
  // N más recientes si hay demasiados (evitar arrays infinitamente crecientes).
  const MAX_TOKENS_PER_USER = 5;

  const usersWithManyTokens = await this.prisma.user.findMany({
    where: {
      fcmTokens: { isEmpty: false },
    },
    select: { id: true, fcmTokens: true },
  });

  for (const user of usersWithManyTokens) {
    if (user.fcmTokens.length > MAX_TOKENS_PER_USER) {
      // Mantener solo los N más recientes (están al final del array por push)
      await this.prisma.user.update({
        where: { id: user.id },
        data: { fcmTokens: user.fcmTokens.slice(-MAX_TOKENS_PER_USER) },
      });
    }
  }
}
```
