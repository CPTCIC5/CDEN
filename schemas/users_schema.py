from pydantic import BaseModel,EmailStr,Field
import datetime
class LoginModel(BaseModel):
    email: EmailStr 
    password: str


class UserCreateModel(BaseModel):
    email: EmailStr 
    password: str
    confirm_password: str = Field(exclude=True)

class ProfileUpdate(BaseModel):
    nickname: str = None


class UserResponse(BaseModel):  
    id: int
    email: EmailStr
    joined_at: datetime
    is_active: bool

    class Config:
        arbitrary_types_allowed=True
        from_attributes = True 


class EmailVerificationRequest(BaseModel):
    email: str
    otp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456"
            }
        }

class ResendVerificationRequest(BaseModel):
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class PasswordResetRequest(BaseModel):
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }

class PasswordResetVerification(BaseModel):
    email: str
    otp: str
    new_password: str
    confirm_password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "otp": "123456",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        } 



class UserEmailUpdate(BaseModel):
    email: EmailStr

class UserPasswordChange(BaseModel):
    current_password: str 
    new_password: str 
    confirm_new_password: str= Field(exclude=True)

class UserPasswordForgot(BaseModel):
    new_password: str 
    confirm_new_password: str