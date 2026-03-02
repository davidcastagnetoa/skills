---
name: rbac
description: Control de acceso basado en roles para microservicios y operadores del sistema KYC
---

# rbac

RBAC (Role-Based Access Control) limita lo que puede hacer cada servicio, operador y proceso dentro del sistema KYC. En Kubernetes, el RBAC nativo controla qué pods pueden acceder a qué recursos. En la capa de aplicación, los roles controlan el acceso a las funcionalidades de revisión manual y administración.

## When to use

Definir desde el inicio del proyecto. Principio de mínimo privilegio: cada servicio solo puede acceder a los recursos que necesita para su función.

## Instructions

1. RBAC en Kubernetes para los servicios KYC (`k8s/rbac.yaml`):
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: kyc-api-role
   rules:
     - apiGroups: [""]
       resources: ["secrets"]
       resourceNames: ["kyc-db-credentials", "kyc-jwt-key"]
       verbs: ["get"]
     - apiGroups: [""]
       resources: ["configmaps"]
       verbs: ["get", "list"]
   ---
   kind: RoleBinding
   apiVersion: rbac.authorization.k8s.io/v1
   metadata:
     name: kyc-api-binding
   subjects:
     - kind: ServiceAccount
       name: kyc-api
   roleRef:
     kind: Role
     name: kyc-api-role
   ```
2. Roles de aplicación en FastAPI:
   ```python
   class UserRole(str, Enum):
       REVIEWER = "reviewer"    # puede ver y decidir casos en revisión manual
       ADMIN = "admin"          # puede cambiar thresholds y configuración
       AUDITOR = "auditor"      # puede ver logs de auditoría, solo lectura
       API_CLIENT = "client"    # solo puede iniciar sesiones KYC
   def require_role(required_role: UserRole):
       async def dependency(payload: dict = Depends(verify_jwt)):
           if payload.get("role") != required_role:
               raise HTTPException(403, "Insufficient permissions")
       return dependency
   ```
3. Aplicar en endpoints: `@app.get("/admin/thresholds", dependencies=[Depends(require_role(UserRole.ADMIN))])`.
4. En Vault, aplicar políticas por servicio: el kyc-api solo puede leer `secret/kyc/`, los workers solo `secret/models/`.

## Notes

- El ServiceAccount de cada pod en Kubernetes debe ser diferente — no usar el ServiceAccount por defecto.
- Los cambios de thresholds de decisión deben requerir rol ADMIN y quedar registrados en el audit log.
- Revisar periódicamente (trimestral) los roles asignados — eliminar accesos que ya no son necesarios (principio de menor privilegio).