from fastapi import Header, HTTPException


def require_admin(
    x_user_role: str = Header(
        default="employee",
        alias="X-User-Role",
    ),
) -> str:
    role = x_user_role.lower().strip()

    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required.",
        )

    return role