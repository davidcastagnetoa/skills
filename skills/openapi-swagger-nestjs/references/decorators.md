# OpenAPI — Decoradores de Controllers y DTOs

## Fuente: https://docs.nestjs.com/openapi/decorators

---

## 1. Decoradores de controller

```typescript
import {
  ApiTags, ApiOperation, ApiResponse, ApiParam,
  ApiBody, ApiQuery, ApiBearerAuth, ApiCreatedResponse,
  ApiNotFoundResponse, ApiForbiddenResponse, ApiConflictResponse,
} from '@nestjs/swagger';

@ApiTags('reservations')
@ApiBearerAuth('accessToken')   // ← Indica que requiere JWT
@Controller('gifts')
export class ReservationsController {

  @Post(':id/reserve')
  @ApiOperation({
    summary: 'Reservar un regalo ("Lo compro yo")',
    description:
      'Marca el regalo como Reservado. ' +
      '⚠️ La respuesta nunca incluye la identidad del reservante, ' +
      'aunque el propietario de la lista sea quien consulte.',
  })
  @ApiParam({ name: 'id', description: 'ID del regalo', type: String })
  @ApiResponse({ status: 200, description: 'Regalo reservado', type: GiftStatusResponseDto })
  @ApiResponse({ status: 200, description: 'Ya estaba reservado (idempotente)', type: GiftStatusResponseDto })
  @ApiForbiddenResponse({ description: 'No perteneces al círculo o intentas reservar tu propio regalo' })
  @ApiConflictResponse({ description: 'El regalo ya fue recibido (estado terminal)' })
  @ApiNotFoundResponse({ description: 'Regalo no encontrado' })
  async reserve(@Param('id') id: string, @CurrentUser() userId: string) { ... }

  @Post(':id/release')
  @ApiOperation({ summary: 'Liberar tu reserva', description: 'Solo el reservante puede liberarla.' })
  @ApiResponse({ status: 200, description: 'Reserva cancelada, regalo disponible de nuevo' })
  @ApiForbiddenResponse({ description: 'No tienes una reserva activa en este regalo' })
  async release(@Param('id') id: string, @CurrentUser() userId: string) { ... }
}
```

---

## 2. Decoradores de DTO — @ApiProperty completo

```typescript
import { ApiProperty, ApiPropertyOptional, ApiHideProperty } from '@nestjs/swagger';
import { IsString, IsOptional, IsUrl, IsNumber, Min } from 'class-validator';

export class CreateGiftDto {
  @ApiProperty({ description: 'Título del regalo', example: 'Auriculares Sony WH-1000XM5' })
  @IsString()
  titulo: string;

  @ApiPropertyOptional({ description: 'Descripción adicional', example: 'Color negro, con cancelación de ruido' })
  @IsOptional()
  @IsString()
  descripcion?: string;

  @ApiPropertyOptional({ description: 'URL del producto en tienda online', example: 'https://amazon.es/...' })
  @IsOptional()
  @IsUrl()
  url?: string;

  @ApiPropertyOptional({ description: 'Precio estimado en euros', example: 299.99, minimum: 0 })
  @IsOptional()
  @IsNumber()
  @Min(0)
  precioEstimado?: number;
}

// DTO de respuesta — con @ApiHideProperty para campos privados
export class GiftStatusResponseDto {
  @ApiProperty({ example: 'uuid-gift-123' })
  giftId: string;

  @ApiProperty({ enum: ['AVAILABLE', 'RESERVED', 'RECEIVED'], example: 'RESERVED' })
  estado: string;

  @ApiPropertyOptional({ description: 'Cuándo fue reservado', example: '2026-02-18T09:00:00Z' })
  reservadoEn?: Date;

  @ApiHideProperty()   // ← NUNCA exponer — invariante de privacidad HADA
  reservedById?: string;
}
```

---

## 3. Enum documentado

```typescript
import { ApiProperty } from '@nestjs/swagger';

enum GiftStatus { AVAILABLE = 'AVAILABLE', RESERVED = 'RESERVED', RECEIVED = 'RECEIVED' }

export class GiftResponseDto {
  @ApiProperty({ enum: GiftStatus, enumName: 'GiftStatus' })
  estado: GiftStatus;
}
```

---

## 4. Arrays y respuestas paginadas

```typescript
export class ListWithGiftsDto {
  @ApiProperty({ type: [GiftResponseDto] })
  gifts: GiftResponseDto[];

  @ApiProperty({ example: 5 })
  total: number;
}
```
