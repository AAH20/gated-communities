"""Main FastAPI application."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

from .database import engine, Base, get_db
from .api import communities, members, moderation, search, audit, export, bulk, websocket
from .auth import (
    security, get_current_user, get_current_user_optional,
    LoginRequest, RegisterRequest, TokenResponse, PasswordChangeRequest,
    register_user, authenticate_user, create_access_token, create_refresh_token,
    verify_token, refresh_access_token, revoke_token,
)
from .rate_limit import RateLimitMiddleware, rate_limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Gated Communities API",
    description="Tiered access control for community platforms",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(communities.router, prefix="/communities", tags=["communities"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(bulk.router, prefix="/bulk", tags=["bulk"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/", response_model=dict)
def root():
    return {"name": "Gated Communities API", "version": "0.1.0"}


@app.get("/health", response_model=dict)
def health_check():
    return {"status": "ok"}


@app.get("/health/live", response_model=dict)
def liveness_check():
    return {"status": "ok"}


@app.get("/health/ready", response_model=dict)
def readiness_check():
    return {"status": "ok"}


@app.get("/ready", response_model=dict)
def ready_check():
    return {"status": "ready"}


@app.get("/live", response_model=dict)
def live_check():
    return {"status": "alive"}


# Auth endpoints
@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    return TokenResponse(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    refresh_token = auth_header[7:]
    new_access_token = refresh_access_token(refresh_token)
    if not new_access_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return TokenResponse(access_token=new_access_token, token_type="bearer")


@app.post("/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        revoke_token(credentials.credentials)
    return {"status": "logged_out"}


@app.post("/auth/register", response_model=dict, status_code=201)
def register(request: RegisterRequest):
    if len(request.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    user = register_user(request.username, request.email, request.password)
    return user


@app.post("/auth/password/change")
def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
):
    if len(request.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    # Verify current password
    from .auth import _users, _hash_password
    user = _users.get(current_user["username"])
    if user and user["password_hash"] != _hash_password(request.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if user:
        user["password_hash"] = _hash_password(request.new_password)
    return {"status": "password_changed"}


@app.get("/auth/me", response_model=dict)
def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "username": current_user["username"], "email": current_user["email"]}
