"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from .api import audit, bulk, communities, export, health, members, moderation, search, websocket
from .api.main import register_all_routers
from .auth import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    TokenResponse,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    refresh_access_token,
    register_user,
    revoke_token,
    security,
)
from .database import Base, engine
from .rate_limit import RateLimitMiddleware


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

# CORS: Restrict origins in production; allow_credentials requires specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(RateLimitMiddleware)


# ---------------------------------------------------------------------------
# Global exception handlers for proper error handling
# ---------------------------------------------------------------------------


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions without leaking internal details."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Include routers
app.include_router(health.health_router, tags=["health"])
app.include_router(communities.router, prefix="/communities", tags=["communities"])
app.include_router(members.router, prefix="/members", tags=["members"])
app.include_router(moderation.router, prefix="/moderation", tags=["moderation"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(bulk.router, prefix="/bulk", tags=["bulk"])
app.include_router(websocket.router, tags=["websocket"])

# Mount every remaining domain router (tiers, audit, bulk, webhooks, ...)
register_all_routers(app)


@app.get("/", response_model=dict)
def root():
    return {"name": "Gated Communities API", "version": "0.1.0"}


# NOTE: /health, /health/live, /health/ready, /ready, /live are served by
# src/gated_communities/api/health.py (registered in api/main.py).
# Do not re-define them here — duplicates shadow the router versions.


# Auth endpoints
@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


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
    from .auth import _hash_password, _users

    user = _users.get(current_user["username"])
    if user and user["password_hash"] != _hash_password(request.current_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user:
        user["password_hash"] = _hash_password(request.new_password)
    return {"status": "password_changed"}


@app.get("/auth/me", response_model=dict)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
    }
