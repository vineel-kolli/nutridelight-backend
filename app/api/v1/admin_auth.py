from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

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
    response: Response,
    db: Session = Depends(get_db),
   
):
    admin = authenticate_admin(
        db=db,
        username=data.username,
        password=data.password,
    )

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    session_token = create_admin_session(
        db=db,
        admin_user=admin,
    )

    db.commit()

    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=8 * 60 * 60,
        path="/",
    )

    return AdminLoginResponse(
        admin=AdminUserResponse(
            id=admin.id,
            username=admin.username,
        ),
    )


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