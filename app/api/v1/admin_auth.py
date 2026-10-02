from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.config import settings

from app.api.dependencies import (
    ADMIN_SESSION_COOKIE,
    get_current_admin,
    get_db,
    require_admin_origin,
)
from app.models.admin_user import AdminUser
from app.schemas.auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminMeResponse,
    AdminUserResponse,
)
from app.services.auth_service import (
    authenticate_admin,
    create_admin_session,
    revoke_admin_session,
)
from app.services.login_rate_limit_service import (
    is_login_blocked,
    record_failed_login,
    reset_failed_logins,
)




router = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Auth"],
)


@router.post(
    "/login",
    response_model=AdminLoginResponse,
)
def login(
    data: AdminLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    if is_login_blocked(
        db=db,
        username=data.username,
        ip_address=client_ip,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )

    admin = authenticate_admin(
        db=db,
        username=data.username,
        password=data.password,
    )

    if admin is None:
        record_failed_login(
            db=db,
            username=data.username,
            ip_address=client_ip,
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    reset_failed_logins(
        db=db,
        username=data.username,
        ip_address=client_ip,
    )

    session_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    db.commit()

    final_response = JSONResponse(
        content={
            "admin": {
                "id": admin.id,
                "username": admin.username,
            }
        }
    )

    final_response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=8 * 60 * 60,
        path="/",
    )

    

    return final_response
@router.post("/logout")
def logout(
    response: Response,
    admin_session: str | None = Cookie(
        default=None,
        alias=ADMIN_SESSION_COOKIE,
    ),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
   
):
    if admin_session:
        revoke_admin_session(
            db=db,
            raw_token=admin_session,
        )
 
    db.commit()
    response.delete_cookie(
        key=ADMIN_SESSION_COOKIE,
        path="/",
    )

    return {"message": "Logged out"}


@router.get(
    "/me",
    response_model=AdminMeResponse,
)
def me(
    admin: AdminUser = Depends(get_current_admin),
):
    return AdminMeResponse(
        id=admin.id,
        username=admin.username,
    )