from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from db.models import get_db, User,Profile, VerificationOTP,pwd_context
from schemas.users_schema import (
    UserCreateModel, 
    LoginModel, 
    ProfileUpdate, 
    UserEmailUpdate, 
    UserPasswordChange, 
    EmailVerificationRequest,
    ResendVerificationRequest,
    PasswordResetRequest,
    PasswordResetVerification
)
from utils.email_sender import generate_otp, send_verification_email, send_password_reset_email
from utils.auth import get_current_user, create_session, end_session
from utils.constants import ROLE_FOUNDER
from datetime import datetime, timedelta
router= APIRouter(
    prefix="/api/auth"
)

@router.post("/register")
async def create_user(request: Request, data: UserCreateModel, db: Session = Depends(get_db)):
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    
    elif db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    elif len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    # Public signup always creates a founder. Mentors are created via admin
    # invite, and admins are seeded — neither can be self-assigned here.
    new_user= User(
        email= data.email,
        role= ROLE_FOUNDER,
    )
    new_user.set_password(data.password)
    print(new_user)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    new_profile= Profile(user_id= new_user.id)
    db.add(new_profile)
    try:
        db.commit()
        db.refresh(new_profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate and send verification email
    await send_verification_otp(new_user.email, db)
    # Create session for the new user
    create_session(request, new_user)
    
    return JSONResponse({
        'detail': 'User created. Please check your email for verification code.',
        'user': {
            'id': new_user.id,
            'email': new_user.email,
            'is_verified': new_user.is_verified,
            'role': new_user.role
        }
    }, status_code=status.HTTP_201_CREATED)



async def send_verification_otp(email: str, db: Session):
    """Generate and send a verification OTP to the user's email"""
    
    # Generate a 6-digit OTP
    otp = generate_otp(6)
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Create OTP record in database
    verification_otp = VerificationOTP(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    
    # Save to database
    db.add(verification_otp)
    try:
        db.commit()
        # Send email with OTP
        send_verification_email(email, otp)
    except Exception as e:
        db.rollback()
        print(f"Error sending verification email: {e}")


async def send_password_reset_otp(email: str, db: Session):
    """Generate and send a password reset OTP to the user's email"""
    
    # Generate a 6-digit OTP
    otp = generate_otp(6)
    
    # Set expiration time (10 minutes from now)
    expires_at = datetime.now() + timedelta(minutes=10)
    
    # Create OTP record in database
    verification_otp = VerificationOTP(
        email=email,
        otp=otp,
        expires_at=expires_at
    )
    
    # Save to database
    db.add(verification_otp)
    try:
        db.commit()
        # Send password reset email with OTP
        send_password_reset_email(email, otp)
    except Exception as e:
        db.rollback()
        print(f"Error sending password reset email: {e}")


@router.post('/verify-email')
async def verify_email(data: EmailVerificationRequest, db: Session = Depends(get_db)):
    """Verify user's email using the provided OTP"""
    
    # Find the latest OTP for this email that hasn't been used
    verification = db.query(VerificationOTP).filter(
        VerificationOTP.email == data.email,
        VerificationOTP.is_used == False
    ).order_by(desc(VerificationOTP.created_at)).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No verification code found for this email"
        )
    
    if not verification.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one."
        )
    
    if verification.otp != data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Mark OTP as used
    verification.mark_as_used()
    
    # Update user's verification status
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        user.is_verified = True
    
    try:
        db.commit()
        return {"message": "Email verified successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))




@router.delete('/delete-user')
async def delete_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_user = db.query(User).filter(User.id == current_user.id).first()
    if not my_user:
        return HTTPException(detail="User not found, Unexpected error", status_code=status.HTTP_404_NOT_FOUND)
    db.delete(my_user)
    db.commit()
    return JSONResponse({'detail': "User deleted"}, status_code=status.HTTP_204_NO_CONTENT)


@router.post("/login")
async def login(request: Request, data: LoginModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user or not user.verify_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create session
    create_session(request, user)
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        },
        "message": "Login successful"
    }



@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    end_session(request)
    return {"message": "Logged out successfully"}


@router.patch("/profile/update/user-email")
async def update_user_email(
    data: UserEmailUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    my_user = db.query(User).filter(User.id == current_user.id).first()

    if not my_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    # Update the email
    my_user.email = data.email

    db.commit()
    db.refresh(my_user)

    return {"message": "Email updated successfully", "email": my_user.email}

@router.post('/change-password')
async def change_password(
    data: UserPasswordChange, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Fetch the user instance
    my_user = db.query(User).filter(User.id == current_user.id).first()

    if not my_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Not Found"
        )
    
    # Verify current password
    if not pwd_context.verify(data.current_password, my_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    # Check if new passwords match
    if data.new_password != data.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password didn't match"
        )

    # Hash new password and update user
    my_user.password = pwd_context.hash(data.new_password)
    
    db.commit()
    db.refresh(my_user)

    return {"message": "Password changed successfully."}

@router.get("/user/me")
async def get_profile(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's profile with detailed information"""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile

@router.get("/user/{id}")
async def get_profile(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's profile with detailed information"""
    profile = db.query(Profile).filter(Profile.user_id == id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.post('/resend-verification')
async def resend_verification(data: ResendVerificationRequest, db: Session = Depends(get_db)):
    """Resend verification OTP to an existing user's email"""
    
    # Find the user by email
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found with this email"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Send verification OTP
    await send_verification_otp(user.email, db)
    
    return {"message": "Verification code sent. Please check your email."}


@router.post('/request-password-reset')
async def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset OTP to user's email"""
    
    # Find the user by email
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        # For security reasons, don't reveal if email exists or not
        return {"message": "If your email is registered with us, you will receive a password reset code shortly."}
    
    # Send password reset OTP
    await send_password_reset_otp(user.email, db)
    
    return {"message": "If your email is registered with us, you will receive a password reset code shortly."}


@router.post('/reset-password')
async def reset_password(data: PasswordResetVerification, db: Session = Depends(get_db)):
    """Reset user password using OTP verification"""
    
    # Check if passwords match
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Check password length
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Find the latest OTP for this email that hasn't been used
    verification = db.query(VerificationOTP).filter(
        VerificationOTP.email == data.email,
        VerificationOTP.is_used == False
    ).order_by(desc(VerificationOTP.created_at)).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid password reset code found for this email"
        )
    
    if not verification.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code has expired. Please request a new one."
        )
    
    if verification.otp != data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset code"
        )
    
    # Find the user
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mark OTP as used
    verification.mark_as_used()
    
    # Update user's password
    user.set_password(data.new_password)
    
    try:
        db.commit()
        return {"message": "Password reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))




@router.get("/verification-status")
async def check_verification_status(current_user: User = Depends(get_current_user)):
    """Check if the current user's email is verified"""
    
    return {
        "is_verified": current_user.is_verified,
        "email": current_user.email,
        "message": "Your email is verified." if current_user.is_verified else "Your email is not verified. Please verify your email."
    }