"""Auth routes — Register, Login, Get current user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password, create_reset_token, decode_reset_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserBrief, ForgotPasswordRequest, ResetPasswordRequest
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user.id, "REGISTER", "user", user.id)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserBrief.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT token."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    log_action(db, user.id, "LOGIN", "user", user.id)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserBrief.model_validate(user),
    )


@router.get("/me", response_model=UserBrief)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's info."""
    return UserBrief.model_validate(current_user)


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate a password reset token for a given email."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # To prevent email enumeration, we return a generic success message
        # even if the email doesn't exist.
        return {"message": "If an account with that email exists, a reset link has been sent.", "token": None}

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Generate token
    token = create_reset_token(user.email)
    
    # In a real app, send an email here.
    # For demo purposes, we return the token in the response so the frontend can mock it.
    log_action(db, user.id, "PASSWORD_RESET_REQUEST", "user", user.id)
    return {
        "message": "If an account with that email exists, a reset link has been sent.",
        "token": token
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset the password using a valid token."""
    email = decode_reset_token(req.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user.password_hash = hash_password(req.new_password)
    db.commit()

    log_action(db, user.id, "PASSWORD_RESET_SUCCESS", "user", user.id)
    return {"message": "Password has been successfully reset."}
