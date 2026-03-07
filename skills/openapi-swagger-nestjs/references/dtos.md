# OpenAPI — DTOs Documentados de HADA

---

## Auth

```typescript
export class RegisterDto {
  @ApiProperty({ example: 'María García' }) nombre: string;
  @ApiProperty({ example: 'maria@email.com' }) email: string;
  @ApiProperty({ example: 'password123', minLength: 8 }) password: string;
  @ApiPropertyOptional({ example: '1990-05-15' }) birthdayDate?: string;
}

export class AuthResponseDto {
  @ApiProperty() accessToken: string;
  @ApiProperty() refreshToken: string;
  @ApiProperty({ type: UserDto }) user: UserDto;
}
```

## Circles

```typescript
export class CreateCircleDto {
  @ApiProperty({ example: 'Familia García' }) nombre: string;
}

export class InviteLinkResponseDto {
  @ApiProperty({ example: 'https://hada.app/join/ABC123' }) inviteUrl: string;
  @ApiProperty({ example: '2026-02-25T00:00:00Z' }) expiresAt: Date;
}
```

## Reservations — con @ApiHideProperty obligatorio

```typescript
export class GiftStatusResponseDto {
  @ApiProperty() giftId: string;
  @ApiProperty({ enum: ['AVAILABLE', 'RESERVED', 'RECEIVED'] }) estado: string;
  @ApiPropertyOptional() reservadoEn?: Date;
  @ApiPropertyOptional({ description: 'Solo visible para el propio reservante' }) puedesLiberar?: boolean;

  @ApiHideProperty()  // ⚠️ Invariante HADA: NUNCA en el contrato
  reservedById?: string;
}
```
