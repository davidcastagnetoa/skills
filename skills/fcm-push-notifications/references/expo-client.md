# FCM — Token Management

## 1. Registro y almacenamiento de tokens

```typescript
// src/modules/notifications/token.service.ts
@Injectable()
export class TokenService {
  constructor(private readonly prisma: PrismaService) {}

  async registerToken(userId: string, token: string): Promise<void> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId }, select: { fcmTokens: true }
    });
    if (!user || user.fcmTokens.includes(token)) return;

    await this.prisma.user.update({
      where: { id: userId },
      data: { fcmTokens: { push: token } },
    });
  }

  async getTokensByCircleId(circleId: string): Promise<string[]> {
    const members = await this.prisma.circleMember.findMany({
      where: { circleId },
      include: { user: { select: { fcmTokens: true } } },
    });
    return [...new Set(members.flatMap(m => m.user.fcmTokens).filter(Boolean))];
  }

  async removeInvalidTokens(tokens: string[]): Promise<void> {
    if (tokens.length === 0) return;
    const users = await this.prisma.user.findMany({
      where: { fcmTokens: { hasSome: tokens } },
      select: { id: true, fcmTokens: true },
    });
    await Promise.all(users.map(u =>
      this.prisma.user.update({
        where: { id: u.id },
        data: { fcmTokens: u.fcmTokens.filter(t => !tokens.includes(t)) },
      })
    ));
  }
}
```
