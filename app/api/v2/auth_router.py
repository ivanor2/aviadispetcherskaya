from fastapi import APIRouter, Depends, Query, status, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdateRole
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user, admin_required
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, session: Session = Depends(get_session)):  # ✅ Добавлено 'data:'
    user = User(username=data.username, password=hash_password(data.password), role="guest")
    session.add(user); session.commit(); session.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, response: Response, session: Session = Depends(get_session)):  # ✅ Добавлено 'data:'
    user = session.exec(select(User).where(User.username == data.username)).first()
    if not user or not verify_password(data.password, user.password):
        raise status.HTTP_401_UNAUTHORIZED
    response.set_cookie(key="access_token", value=create_access_token({"sub": user.username}), httponly=True, samesite="lax", path="/")
    return {"access_token": create_access_token({"sub": user.username}), "refreshToken": create_refresh_token({"sub": user.username}), "tokenType": "bearer"}

@router.post("/refresh", response_model=dict)
def refresh_token(refresh_token: str):
    username = decode_token(refresh_token, expected_type="refresh")
    if not username: raise status.HTTP_401_UNAUTHORIZED
    return {"accessToken": create_access_token({"sub": username}), "tokenType": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "Logged out"}

@router.get("/me", response_model=UserResponse)
def me(user=Depends(get_current_user)):
    return user

@router.put("/{user_id}/role", response_model=UserResponse, dependencies=[Depends(admin_required)])
def change_role(user_id: int, data: UserUpdateRole, session: Session = Depends(get_session)):  # ✅ Добавлено 'data:'
    user = session.get(User, user_id)
    if not user: raise status.HTTP_404_NOT_FOUND
    user.role = data.role
    session.commit(); session.refresh(user)
    return user

@router.get("/users", response_model=Page[UserResponse], dependencies=[Depends(admin_required)])
def list_users(session: Session = Depends(get_session), role: str = Query(None)):
    q = select(User)
    if role: q = q.where(User.role == role)
    return paginate(session, q)