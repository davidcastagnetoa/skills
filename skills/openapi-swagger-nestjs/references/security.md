# OpenAPI — Seguridad JWT en Swagger

## Fuente: https://docs.nestjs.com/openapi/security

---

## Configuración de BearerAuth para endpoints protegidos

```typescript
// En main.ts ya configurado:
.addBearerAuth({ type: 'http', scheme: 'bearer', bearerFormat: 'JWT' }, 'accessToken')

// En cada controller que requiera auth:
@ApiBearerAuth('accessToken')
@UseGuards(JwtAuthGuard)
@Controller('circles')
export class CirclesController { ... }

// Para endpoints mixtos (algunos públicos, algunos protegidos):
@Controller('lists')
export class ListsController {
  @Get('public/:id')
  @ApiOperation({ summary: 'Vista pública de lista (si aplica)' })
  // Sin @ApiBearerAuth — endpoint público

  @Post()
  @ApiBearerAuth('accessToken')  // ← Solo este requiere auth
  @UseGuards(JwtAuthGuard)
  create() { ... }
}
```

## Documentar respuestas de error de autenticación globalmente

```typescript
// En el DocumentBuilder, añadir respuestas globales:
// O bien, en un decorador personalizado:
export const ApiAuth = () => applyDecorators(
  ApiBearerAuth('accessToken'),
  UseGuards(JwtAuthGuard),
  ApiUnauthorizedResponse({ description: 'Token inválido o expirado' }),
);

// Uso simplificado en controllers:
@ApiAuth()
@Post()
create() { ... }
```
