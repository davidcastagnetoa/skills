"""Role-Based Access Control (RBAC) for the VerifID API.

Roles:
    admin     — full access to all endpoints
    operator  — create verifications, view dashboards
    reviewer  — access manual review queue
    client    — create and query own verifications only
"""

from enum import Enum

import structlog
from fastapi import HTTPException, Request, status

logger = structlog.get_logger()


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    CLIENT = "client"


# Permission matrix: role → set of allowed actions
_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "verify:create",
        "verify:read",
        "verify:list",
        "review:read",
        "review:resolve",
        "dashboard:view",
        "admin:manage_clients",
        "admin:manage_blacklist",
        "admin:view_audit",
    },
    Role.OPERATOR: {
        "verify:create",
        "verify:read",
        "verify:list",
        "dashboard:view",
    },
    Role.REVIEWER: {
        "review:read",
        "review:resolve",
        "verify:read",
    },
    Role.CLIENT: {
        "verify:create",
        "verify:read",
    },
}


def has_permission(role: Role, action: str) -> bool:
    """Check if a role has permission for an action."""
    return action in _PERMISSIONS.get(role, set())


def require_permission(action: str):
    """FastAPI dependency that checks user permission.

    Usage:
        @router.post("/verify", dependencies=[Depends(require_permission("verify:create"))])
    """
    async def _check(request: Request):
        # Get role from request headers (set by Nginx Lua or JWT middleware)
        role_str = request.headers.get("X-User-Role", "")
        user_id = request.headers.get("X-User-ID", "anonymous")

        if not role_str:
            # No auth context — allow in dev, deny in production
            import os
            if os.getenv("AUTH_BYPASS", "true") == "true":
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned",
            )

        try:
            role = Role(role_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Unknown role: {role_str}",
            )

        if not has_permission(role, action):
            logger.warning(
                "rbac.denied",
                user_id=user_id,
                role=role_str,
                action=action,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_str}' does not have permission '{action}'",
            )

    return _check
