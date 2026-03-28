from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ...core.db import get_session
from ...models.user import User
from ...schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, PasswordReset, PasswordResetConfirm, EmailVerification
from ...core.security import get_password_hash, verify_password, create_access_token, get_current_user
from ...core.rate_limit import check_rate_limit, login_limiter, register_limiter, password_reset_limiter

# Add this for debugging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@sathyanishta.com")

# Token lifetimes (hours). Password reset was 1h — too short for many users.
EMAIL_VERIFICATION_EXPIRE_HOURS = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_HOURS", "72"))
PASSWORD_RESET_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_EXPIRE_HOURS", "24"))
# Public URL for links in emails (match Traefik / dev port)
APP_PUBLIC_URL = (
    os.getenv("NEXT_PUBLIC_APP_URL")
    or os.getenv("PUBLIC_APP_URL")
    or "http://127.0.0.1:3000"
).rstrip("/")


def utc_now() -> datetime:
    """Timezone-aware UTC 'now' (avoids naive/Postgres timestamptz mismatches)."""
    return datetime.now(timezone.utc)


def to_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize DB datetimes to aware UTC for comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # We store/compare in UTC; naive values from DB are treated as UTC.
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def send_verification_email(email: str, token: str):
    """Send email verification link"""
    if not SMTP_USER or not SMTP_PASSWORD or "your-email" in SMTP_USER:
        print(f"Skipping verification email to {email} - SMTP credentials not configured")
        return

    verification_url = f"{APP_PUBLIC_URL}/auth/verify?token={token}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Welcome to Sathya Nishta!</h2>
        <p>Thank you for signing up. Please verify your email address by clicking the link below:</p>
        <a href="{verification_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0;">
            Verify Email Address
        </a>
        <p>Or copy and paste this link in your browser:</p>
        <p>{verification_url}</p>
        <p>This link will expire in {EMAIL_VERIFICATION_EXPIRE_HOURS} hours.</p>
        <p>Best regards,<br>The Sathya Nishta Team</p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your Sathya Nishta account"
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send verification email: {e}")

def send_password_reset_email(email: str, token: str):
    """Send password reset link"""
    if not SMTP_USER or not SMTP_PASSWORD or "your-email" in SMTP_USER:
        print(f"Skipping password reset email to {email} - SMTP credentials not configured")
        return

    reset_url = f"{APP_PUBLIC_URL}/auth/reset-password?token={token}"
    
    html_content = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested a password reset for your Sathya Nishta account. Click the link below to reset your password:</p>
        <a href="{reset_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0;">
            Reset Password
        </a>
        <p>Or copy and paste this link in your browser:</p>
        <p>{reset_url}</p>
        <p>This link will expire in {PASSWORD_RESET_EXPIRE_HOURS} hours.</p>
        <p>If you didn't request this password reset, please ignore this email.</p>
        <p>Best regards,<br>The Sathya Nishta Team</p>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Reset your Sathya Nishta password"
        msg["From"] = FROM_EMAIL
        msg["To"] = email
        
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send password reset email: {e}")

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_session), request: Request = None):
    """Register a new user"""
    try:
        # Debug logging
        logger.info(f"Registration attempt: {user.email}")
        logger.info(f"User data: {user.dict()}")
        
        # Apply rate limiting
        client_ip = request.client.host if request else "unknown"
        check_rate_limit(register_limiter, user.email, "Too many registration attempts. Please try again later.")
        
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            logger.warning(f"Email already registered: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        verification_token = secrets.token_urlsafe(32)
        verification_expires = utc_now() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
        
        db_user = User(
            email=user.email,
            name=user.name,
            hashed_password=hashed_password,
            company=user.company,
            role=user.role,
            bio=user.bio,
            verification_token=verification_token,
            verification_expires=verification_expires
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Send verification email
        send_verification_email(user.email, verification_token)
        
        logger.info(f"User registered successfully: {user.email}")
        return UserResponse.model_validate(db_user)
        
    except ValueError as e:
        # Handle validation errors from Pydantic validators
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/verify-email")
async def verify_email(verification: EmailVerification, db: Session = Depends(get_session)):
    """Verify email address"""
    raw_token = (verification.token or "").strip()
    user = db.query(User).filter(User.verification_token == raw_token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    exp = to_utc_aware(user.verification_expires)
    if exp is not None and exp <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    user.verification_expires = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/login")
async def login(user_credentials: UserLogin, db: Session = Depends(get_session), request: Request = None):
    """Login user and return access token"""
    # Apply rate limiting
    client_ip = request.client.host if request else "unknown"
    check_rate_limit(login_limiter, client_ip, "Too many login attempts. Please try again later.")
    
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email before logging in"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@router.post("/forgot-password")
async def forgot_password(password_reset: PasswordReset, db: Session = Depends(get_session), request: Request = None):
    """Send password reset email"""
    # Apply rate limiting
    client_ip = request.client.host if request else "unknown"
    check_rate_limit(password_reset_limiter, password_reset.email, "Too many password reset attempts. Please try again later.")
    
    user = db.query(User).filter(User.email == password_reset.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    reset_token = secrets.token_urlsafe(32)
    reset_expires = utc_now() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    
    user.reset_token = reset_token
    user.reset_expires = reset_expires
    db.commit()
    
    send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm, db: Session = Depends(get_session)):
    """Reset password with token"""
    raw_token = (reset_data.token or "").strip()
    user = db.query(User).filter(User.reset_token == raw_token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    exp = to_utc_aware(user.reset_expires)
    if exp is not None and exp <= utc_now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse.model_validate(current_user)

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update current user info"""
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)
