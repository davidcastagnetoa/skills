# OpenAPI/Swagger — Setup en NestJS

## Fuente: https://docs.nestjs.com/openapi/introduction

---

## 1. Instalación

```bash
npm install @nestjs/swagger
```

---

## 2. Configuración en main.ts

```typescript
// src/main.ts
import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.setGlobalPrefix('v1');
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

  // Swagger solo en entornos no-producción
  if (process.env.NODE_ENV !== 'production') {
    const config = new DocumentBuilder()
      .setTitle('HADA API')
      .setDescription(
        'API de coordinación privada de regalos. ' +
        '⚠️ NOTA: Los endpoints de reserva nunca exponen la identidad del reservante.'
      )
      .setVersion('1.0.0')
      .addBearerAuth(
        { type: 'http', scheme: 'bearer', bearerFormat: 'JWT', in: 'header' },
        'accessToken',
      )
      .addTag('auth', 'Autenticación y gestión de sesiones')
      .addTag('circles', 'Círculos privados e invitaciones')
      .addTag('profiles', 'Perfiles principales y subperfiles familiares')
      .addTag('lists', 'Listas de deseos')
      .addTag('gifts', 'Regalos y estados')
      .addTag('reservations', 'Reservas privadas (sin identidad del reservante)')
      .addTag('reminders', 'Recordatorios y notificaciones push')
      .build();

    const document = SwaggerModule.createDocument(app, config);
    SwaggerModule.setup('docs', app, document, {
      swaggerOptions: {
        persistAuthorization: true,       // Mantener el JWT entre recargas
        tagsSorter: 'alpha',
        operationsSorter: 'method',
      },
    });

    console.log(`Swagger UI: http://localhost:${process.env.PORT ?? 3000}/docs`);
  }

  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();
```

---

## 3. Generación del contrato OpenAPI en CI/CD

```typescript
// scripts/generate-openapi.ts
import { NestFactory } from '@nestjs/core';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { writeFileSync, mkdirSync } from 'fs';
import { AppModule } from '../src/app.module';

async function generate() {
  const app = await NestFactory.create(AppModule, { logger: false });

  const config = new DocumentBuilder()
    .setTitle('HADA API')
    .setVersion('1.0.0')
    .addBearerAuth({ type: 'http', scheme: 'bearer', bearerFormat: 'JWT' }, 'accessToken')
    .build();

  const document = SwaggerModule.createDocument(app, config);

  mkdirSync('./docs', { recursive: true });
  writeFileSync('./docs/openapi.json', JSON.stringify(document, null, 2));
  console.log('✅ OpenAPI spec generated: ./docs/openapi.json');

  await app.close();
}
generate();
```

```json
// package.json
{
  "scripts": {
    "generate:openapi": "ts-node scripts/generate-openapi.ts"
  }
}
```

El archivo `docs/openapi.json` se versiona en el repositorio para que el equipo móvil
genere tipos TypeScript automáticamente con `openapi-typescript`.
