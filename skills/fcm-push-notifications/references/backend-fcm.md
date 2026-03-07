# FCM — Setup Backend NestJS con firebase-admin

## Fuente

https://firebase.google.com/docs/admin/setup#initialize-sdk

---

## 1. Instalación

```bash
npm install firebase-admin
```

---

## 2. Inicialización segura (un solo singleton)

```typescript
// src/infrastructure/firebase/firebase.service.ts
import { Injectable, OnModuleInit, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as admin from 'firebase-admin';

@Injectable()
export class FirebaseService implements OnModuleInit {
  private readonly logger = new Logger(FirebaseService.name);

  constructor(private readonly config: ConfigService) {}

  onModuleInit() {
    if (admin.apps.length > 0) return; // Ya inicializado

    const serviceAccountJson = this.config.get<string>('FCM_SERVICE_ACCOUNT');
    if (!serviceAccountJson) {
      this.logger.warn('FCM_SERVICE_ACCOUNT not set — push notifications disabled');
      return;
    }

    try {
      const serviceAccount = JSON.parse(serviceAccountJson);
      admin.initializeApp({
        credential: admin.credential.cert(serviceAccount),
      });
      this.logger.log('Firebase Admin initialized');
    } catch (error) {
      this.logger.error('Failed to initialize Firebase Admin', error);
    }
  }

  get messaging(): admin.messaging.Messaging | null {
    if (!admin.apps.length) return null;
    return admin.messaging();
  }

  isInitialized(): boolean {
    return admin.apps.length > 0;
  }
}
```

```typescript
// src/infrastructure/firebase/firebase.module.ts
import { Global, Module } from '@nestjs/common';
import { FirebaseService } from './firebase.service';

@Global()
@Module({
  providers: [FirebaseService],
  exports: [FirebaseService],
})
export class FirebaseModule {}
```

---

## 3. Variable de entorno — formato del Service Account

El valor de `FCM_SERVICE_ACCOUNT` debe ser el contenido del JSON del service account
de Firebase, comprimido en una sola línea:

```env
# .env (desarrollo — nunca commitear)
FCM_SERVICE_ACCOUNT={"type":"service_account","project_id":"hada-app","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"firebase-adminsdk@hada-app.iam.gserviceaccount.com","client_id":"...","auth_uri":"...","token_uri":"..."}
```

En producción, el valor se almacena en **GCP Secret Manager** y se inyecta en Cloud Run
como variable de entorno en tiempo de despliegue.

---

## 4. Obtener el Service Account JSON

1. Ir a [Firebase Console](https://console.firebase.google.com/) → Proyecto HADA
2. Configuración del proyecto → Cuentas de servicio
3. Generar nueva clave privada → Descargar JSON
4. El archivo descargado es `FCM_SERVICE_ACCOUNT` (nunca commitear)
