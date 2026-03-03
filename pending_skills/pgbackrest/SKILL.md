---
name: pgbackrest
description: Backup y restore de PostgreSQL con pgBackRest para proteger los datos del pipeline KYC
type: Tool
priority: Esencial
mode: Self-hosted
---

# pgbackrest

pgBackRest es la solución de backup y restore para PostgreSQL del sistema de verificación de identidad KYC. Proporciona backups completos, diferenciales e incrementales con compresión y cifrado, almacenamiento en repositorios locales o S3-compatible (MinIO), y restauración point-in-time (PITR) para recuperar el estado exacto de la base de datos ante cualquier incidente.

## When to use

Usar cuando se necesite configurar la estrategia de backup del cluster PostgreSQL que almacena las sesiones de verificación, resultados de decisión, logs de auditoría y configuración de umbrales. Pertenece al **database_agent** y se integra con el cluster Patroni para realizar backups sin impactar el rendimiento del pipeline. Aplicar desde el inicio del despliegue de la base de datos en cualquier entorno (desarrollo, staging, producción).

## Instructions

1. Instalar pgBackRest en los nodos del cluster PostgreSQL:
```bash
# Debian/Ubuntu
apt-get install pgbackrest

# O en el Dockerfile del nodo Patroni
RUN apt-get update && apt-get install -y pgbackrest
```

2. Configurar pgBackRest para el cluster KYC (`/etc/pgbackrest/pgbackrest.conf`):
```ini
[global]
# Repositorio principal en MinIO (S3-compatible)
repo1-type=s3
repo1-s3-endpoint=minio:9000
repo1-s3-bucket=verifid-pg-backups
repo1-s3-region=us-east-1
repo1-s3-key=minio_access_key
repo1-s3-key-secret=minio_secret_key
repo1-s3-uri-style=path
repo1-s3-verify-tls=n

# Cifrado de backups (AES-256-CBC)
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=backup_encryption_passphrase

# Compresión
compress-type=zst
compress-level=3

# Retención
repo1-retention-full=4
repo1-retention-diff=14

# Paralelismo
process-max=4

# Logging
log-level-console=info
log-level-file=detail
log-path=/var/log/pgbackrest

[verifid-kyc]
pg1-path=/var/lib/postgresql/16/data
pg1-port=5432
pg1-user=verifid_admin
```

3. Configurar PostgreSQL para WAL archiving:
```yaml
# En patroni.yml, sección bootstrap.dcs.postgresql.parameters
postgresql:
  parameters:
    archive_mode: 'on'
    archive_command: 'pgbackrest --stanza=verifid-kyc archive-push %p'
    archive_timeout: 60
  recovery_conf:
    restore_command: 'pgbackrest --stanza=verifid-kyc archive-get %f %p'
```

4. Inicializar el stanza y verificar la configuración:
```bash
# Crear el stanza
pgbackrest --stanza=verifid-kyc stanza-create

# Verificar la configuración
pgbackrest --stanza=verifid-kyc check

# Ver información del stanza
pgbackrest --stanza=verifid-kyc info
```

5. Definir la estrategia de backup para el pipeline KYC:
```yaml
backup_strategy:
  full_backup:
    schedule: "Domingos 02:00 UTC"
    cron: "0 2 * * 0"
    retention: 4  # Mantener 4 backups completos (1 mes)
    command: "pgbackrest --stanza=verifid-kyc --type=full backup"

  differential_backup:
    schedule: "Diario 02:00 UTC (excepto domingos)"
    cron: "0 2 * * 1-6"
    retention: 14  # Mantener 14 diferenciales (2 semanas)
    command: "pgbackrest --stanza=verifid-kyc --type=diff backup"

  wal_archiving:
    mode: "Continuo"
    description: "Cada segmento WAL se archiva automáticamente"
    pitr_window: "14 días"
```

6. Automatizar backups con cron o Kubernetes CronJob:
```yaml
# Kubernetes CronJob para backup diferencial diario
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pgbackrest-diff-backup
  namespace: verifid
spec:
  schedule: "0 2 * * 1-6"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: pgbackrest
              image: verifid/pgbackrest:latest
              command:
                - pgbackrest
                - --stanza=verifid-kyc
                - --type=diff
                - backup
              volumeMounts:
                - name: pgbackrest-config
                  mountPath: /etc/pgbackrest
          restartPolicy: OnFailure
          volumes:
            - name: pgbackrest-config
              configMap:
                name: pgbackrest-config
```

7. Procedimientos de restauración:
```bash
# Restauración completa (último backup)
pgbackrest --stanza=verifid-kyc --delta restore

# Restauración point-in-time (a un momento específico)
pgbackrest --stanza=verifid-kyc --delta \
  --type=time "--target=2026-03-03 10:30:00+00" \
  --target-action=promote \
  restore

# Restauración a un punto antes de un error conocido
pgbackrest --stanza=verifid-kyc --delta \
  --type=lsn "--target=0/1A00000" \
  restore

# Verificar la integridad de un backup
pgbackrest --stanza=verifid-kyc --set=20260303-020000F verify
```

8. Monitorizar los backups con métricas Prometheus:
```python
# Exportar métricas de pgBackRest a Prometheus
from prometheus_client import Gauge, Info
import subprocess
import json

backup_age_seconds = Gauge(
    'pgbackrest_last_backup_age_seconds',
    'Seconds since last successful backup',
    ['stanza', 'type']
)

backup_size_bytes = Gauge(
    'pgbackrest_backup_size_bytes',
    'Size of the last backup in bytes',
    ['stanza', 'type']
)

def collect_pgbackrest_metrics():
    result = subprocess.run(
        ['pgbackrest', '--stanza=verifid-kyc', '--output=json', 'info'],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    # Parsear y exponer métricas...
```

9. Configurar alertas para fallos de backup:
```yaml
# Alertmanager rules
groups:
  - name: pgbackrest
    rules:
      - alert: PgBackRestBackupFailed
        expr: pgbackrest_last_backup_age_seconds{type="full"} > 604800  # 7 días
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "pgBackRest full backup has not completed in over 7 days"

      - alert: PgBackRestWalArchivingLag
        expr: pg_stat_archiver_failed_count > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "WAL archiving failures detected"
```

## Notes

- Ejecutar los backups siempre desde una réplica (standby) del cluster Patroni para no impactar el rendimiento del nodo primario que atiende las escrituras del pipeline KYC.
- El cifrado de backups con AES-256-CBC es obligatorio dado que los backups pueden contener datos de sesiones de verificación; la passphrase debe almacenarse en HashiCorp Vault.
- Probar la restauración al menos una vez al mes en un entorno aislado para validar que los backups son funcionales; un backup que no se ha probado no es un backup.
- La retención de 4 backups completos (1 mes) y 14 diferenciales está diseñada para cumplir con las políticas de retención del GDPR mientras permite PITR dentro de una ventana de 14 días.
- Integrar las métricas de pgBackRest en el dashboard de Grafana del database_agent para tener visibilidad del estado de los backups junto con las métricas del cluster.
