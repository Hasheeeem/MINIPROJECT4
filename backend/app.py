from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId
import bcrypt
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
import datetime
from bson import ObjectId, errors
# REMOVED: from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List, Optional
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import magic
from typing import Tuple, Dict, Any
import logging
import base64
import io
from PIL import Image
import httpx
from collections import defaultdict
from fastapi import Request
import random
import string
from typing import Dict

# NEW: Import Resend SDK
import resend

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_SUPPORTED = True
    print("✅ HEIC support enabled")
except ImportError:
    HEIC_SUPPORTED = False
    print("⚠️ HEIC support not available - install pillow-heif")

class SmartImageCompressor:
    MAX_SIZE_BYTES = 15 * 1024 * 1024  # 15MB threshold
    MAX_FILE_SIZE = 50 * 1024 * 1024   # 50MB absolute maximum
    
    @staticmethod
    def is_image_by_filename(filename: str) -> bool:
        """Validate by file extension - includes HEIC"""
        if not filename:
            return False
        
        # Include HEIC since we can process them
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.heic', '.heif'}
        
        try:
            file_extension = filename.lower().split('.')[-1]
            return f'.{file_extension}' in valid_extensions
        except:
            return False
    
    @staticmethod
    def is_image(file_content: bytes) -> Tuple[bool, str]:
        """Validate if file is a valid image using PIL"""
        try:
            if not file_content or len(file_content) == 0:
                return False, "File is empty"
            
            # Try to open the image with PIL (should work with HEIC if pillow-heif is installed)
            image = Image.open(io.BytesIO(file_content))
            
            # Get basic info
            width, height = image.size
            format_type = image.format or "Unknown"
            
            # Check if dimensions are reasonable
            if width <= 0 or height <= 0:
                return False, "Invalid image dimensions"
            
            if width > 20000 or height > 20000:
                return False, "Image dimensions too large (max 20000x20000)"
            
            # Verify the image by loading it
            image.verify()
            return True, f"Valid {format_type} image ({width}x{height})"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def convert_to_web_format(
        image_bytes: bytes,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Convert ANY image format to web-compatible JPEG"""
        
        original_size = len(image_bytes)
        
        try:
            # Open image (works with HEIC if pillow-heif is installed)
            image = Image.open(io.BytesIO(image_bytes))
            original_dimensions = image.size
            original_format = image.format or "Unknown"
            original_mode = image.mode
            
            print(f"   📸 Converting {original_format} to JPEG: {original_dimensions} {original_mode}")
            
            # ALWAYS convert to RGB for consistent JPEG output
            if image.mode in ('RGBA', 'LA', 'P'):
                print(f"   🎨 Converting {image.mode} to RGB")
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                if image.mode in ('RGBA', 'LA'):
                    background.paste(image, mask=image.split()[-1])
                    image = background
            elif image.mode != 'RGB':
                print(f"   🎨 Converting {image.mode} to RGB")
                image = image.convert('RGB')
            
            # Resize if needed
            if image.size[0] > max_width or image.size[1] > max_height:
                print(f"   📐 Resizing from {image.size} to fit {max_width}x{max_height}")
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # ALWAYS save as JPEG for web compatibility
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            jpeg_bytes = output.getvalue()
            
            # Calculate stats
            final_size = len(jpeg_bytes)
            compression_ratio = final_size / original_size
            savings_percent = round((1 - compression_ratio) * 100, 1)
            
            metadata = {
                'original_size': original_size,
                'final_size': final_size,
                'original_dimensions': original_dimensions,
                'final_dimensions': image.size,
                'original_format': original_format,
                'final_format': 'JPEG',
                'original_mode': original_mode,
                'compression_ratio': round(compression_ratio, 3),
                'savings_percent': savings_percent,
                'quality_used': quality,
                'method': 'converted_to_jpeg',
                'web_compatible': True
            }
            
            return jpeg_bytes, metadata
            
        except Exception as e:
            raise Exception(f"Image conversion failed: {str(e)}")
    
    @staticmethod
    def compress_image(
        image_bytes: bytes,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Compress image (wrapper for convert_to_web_format)"""
        return SmartImageCompressor.convert_to_web_format(
            image_bytes, max_width, max_height, quality
        )
    
    @staticmethod
    def progressive_compress(
        image_bytes: bytes,
        target_size: int = 5 * 1024 * 1024  # 5MB target
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Progressive compression - always outputs JPEG"""
        
        print(f"   🎯 Target size: {target_size / (1024*1024):.1f}MB")
        
        # Try different quality levels
        quality_levels = [85, 75, 65, 55, 45, 35]
        
        for quality in quality_levels:
            try:
                print(f"   🔧 Trying quality {quality}")
                jpeg_bytes, metadata = SmartImageCompressor.convert_to_web_format(
                    image_bytes, quality=quality
                )
                
                if len(jpeg_bytes) <= target_size:
                    print(f"   ✅ Target achieved with quality {quality}")
                    metadata['compression_level'] = 'progressive'
                    metadata['target_achieved'] = True
                    return jpeg_bytes, metadata
                    
            except Exception as e:
                print(f"   ⚠️ Quality {quality} failed: {e}")
                continue
        
        # Try dimension reduction
        try:
            scale_factors = [0.8, 0.6, 0.4, 0.3]
            
            for scale in scale_factors:
                max_w = int(1920 * scale)
                max_h = int(1080 * scale)
                
                print(f"   📏 Trying {scale*100}% scale ({max_w}x{max_h})")
                
                jpeg_bytes, metadata = SmartImageCompressor.convert_to_web_format(
                    image_bytes,
                    max_width=max_w,
                    max_height=max_h,
                    quality=35
                )
                
                if len(jpeg_bytes) <= target_size:
                    print(f"   ✅ Target achieved with {scale*100}% scale")
                    metadata['compression_level'] = 'progressive_with_resize'
                    metadata['scale_factor'] = scale
                    metadata['target_achieved'] = True
                    return jpeg_bytes, metadata
                    
        except Exception as e:
            print(f"   ⚠️ Progressive resize failed: {e}")
        
        # Best effort fallback
        try:
            jpeg_bytes, metadata = SmartImageCompressor.convert_to_web_format(
                image_bytes, quality=20, max_width=800, max_height=600
            )
            metadata['compression_level'] = 'maximum_effort'
            metadata['target_achieved'] = False
            return jpeg_bytes, metadata
        except Exception as e:
            raise Exception(f"All compression methods failed: {str(e)}")

# Initialize the compressor
image_compressor = SmartImageCompressor()

# Load environment variables
load_dotenv()

# NEW: Configure Resend API
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise ValueError("RESEND_API_KEY environment variable is required")

resend.api_key = RESEND_API_KEY

EMAIL_FROM = "E&S Decorations <noreply@esdecorations.in>"

EMAIL_FROM_NAME = "E&S Decorations"


# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "miniproject")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Token expires after 24 hours
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_MINIMUM_SCORE = 0.5

ip_requests = defaultdict(list)
IP_LIMIT = 3
TIME_WINDOW = 3600

# FastAPI Instance
app = FastAPI()

# CORS Middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local development
        "https://es-decorations.vercel.app",  # Production frontend URL
        "https://esdecorations.in",  # Custom domain if you have one
        "https://www.esdecorations.in"  # www version
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "ESWEBSITE")
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
contacts_collection = db["contacts"]
admins_collection = db["admins"]
faqs_collection = db["faqs"]
latest_works_collection = db["latest_works"]
job_applications_collection = db["job_applications"]
job_listings_collection = db["job_listings"]
events_collection = db["events"]  

# REMOVED: Initialize FastMail
# fm = FastMail(email_conf)

# Event Models
class EventBase(BaseModel):
    title: str
    description: str
    date: str
    time: str
    location: str
    status: str = "upcoming"  # upcoming, completed, cancelled
    highlights: List[str]

class EventCreate(EventBase):
    pass

class EventUpdate(EventBase):
    pass

class EventInDB(EventBase):
    id: str

class GalleryEventBase(BaseModel):
    title: str
    description: str
    date: str
    location: str
    attendees: int
    category: str
    thumbnail: str
    images: List[str]
    details: str

class GalleryEventCreate(GalleryEventBase):
    pass

class GalleryEventUpdate(GalleryEventBase):
    pass

class GalleryEventInDB(GalleryEventBase):
    id: str

class LatestWork(BaseModel):
    title: str
    thumbnail: str  # Will store base64 image data
    category: str

class AdminLoginRequest(BaseModel):
    email: str
    password: str
    verification_code: str = ""

class RequestVerificationCode(BaseModel):
    email: str
    password: str

verification_codes: Dict[str, Dict] = {}

# Event Management Endpoints
@app.get("/events")
async def get_events():
    try:
        events = await events_collection.find().to_list(length=None)
        # Convert ObjectId to string for each event
        for event in events:
            event["_id"] = str(event["_id"])
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/events")
async def create_event(event: EventCreate):
    try:
        result = await events_collection.insert_one(event.dict())
        if result.inserted_id:
            created_event = await events_collection.find_one(
                {"_id": result.inserted_id}
            )
            created_event["_id"] = str(created_event["_id"])
            return created_event
        raise HTTPException(status_code=500, detail="Failed to create event")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/events/{event_id}")
async def update_event(event_id: str, event: EventUpdate):
    try:
        result = await events_collection.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": event.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        updated_event = await events_collection.find_one(
            {"_id": ObjectId(event_id)}
        )
        updated_event["_id"] = str(updated_event["_id"])
        return updated_event
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/events/{event_id}")
async def delete_event(event_id: str):
    try:
        result = await events_collection.delete_one(
            {"_id": ObjectId(event_id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"message": "Event deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Updated function to send acceptance email using Resend
async def send_acceptance_email(applicant_name: str, applicant_email: str):
    """Send job acceptance email using Resend API"""
    try:
        # Create the email content
        subject = "Welcome to E&S Decorations!"
        
        # HTML version of the email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to E&S Decorations</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to E&S Decorations!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="font-size: 18px; margin-bottom: 20px;">Dear <strong>{applicant_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Thank you for your interest in E&S Decorations. After reviewing your application, 
                    we are <strong style="color: #667eea;">pleased to offer you a position</strong> on our team!
                </p>
                
                <div style="background: #e8f4fd; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; color: #667eea;">What's Next?</p>
                    <p style="margin: 10px 0 0 0;">
                        Our recruiting team will be in touch soon with the next steps, including:
                    </p>
                    <ul style="margin: 10px 0 0 20px;">
                        <li>Contract signing details</li>
                        <li>Onboarding information</li>
                        <li>Your official start date</li>
                    </ul>
                </div>
                
                <p style="margin-bottom: 20px;">
                    If you have any questions in the meantime, feel free to reach out to us. 
                    We're excited to have you join our growing team!
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #667eea; color: white; padding: 15px 30px; border-radius: 25px; display: inline-block;">
                        <strong>🎉 Welcome Aboard! 🎉</strong>
                    </div>
                </div>
                
                <p style="margin-bottom: 5px;"><strong>Best regards,</strong></p>
                <p style="margin-top: 0; color: #667eea; font-weight: bold;">E&S Decorations Recruiting Team</p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>© 2025 E&S Decorations. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version of the email
        plain_text = f"""
        Dear {applicant_name},

        Thank you for your interest in E&S Decorations. After reviewing your application, we are pleased to offer you a position on our team!

        What's Next?
        Our recruiting team will be in touch soon with the next steps, including:
        • Contract signing details
        • Onboarding information  
        • Your official start date

        If you have any questions in the meantime, feel free to reach out to us. We're excited to have you join our growing team!

        🎉 Welcome Aboard! 🎉

        Best regards,
        E&S Decorations Recruiting Team

        © 2025 E&S Decorations. All rights reserved.
        """

        # Send email using Resend
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [applicant_email],
            "subject": subject,
            "html": html_content,
            "text": plain_text,
            "reply_to": "esdecorationsind@gmail.com"
        }

        email_response = resend.Emails.send(params)
        
        # Handle different response formats
        email_id = None
        if hasattr(email_response, 'id'):
            email_id = email_response.id
        elif isinstance(email_response, dict) and 'id' in email_response:
            email_id = email_response['id']
        else:
            email_id = "unknown"
            
        print(f"✅ Acceptance email sent successfully to {applicant_email}. Email ID: {email_id}")
        return email_response

    except Exception as e:
        print(f"❌ Error sending acceptance email: {str(e)}")
        raise Exception(f"Failed to send acceptance email: {str(e)}")

async def send_rejection_email(applicant_name: str, applicant_email: str):
    """Send job rejection email using Resend API"""
    try:
        # Create the email content
        subject = "Thank you for your interest in E&S Decorations"
        
        # HTML version of the email
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Thank you for your interest in E&S Decorations</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Thank you for your interest in E&S Decorations</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="font-size: 18px; margin-bottom: 20px;">Dear <strong>{applicant_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Thank you for taking the time to apply for a position at E&S Decorations. 
                    We appreciate your interest in joining our team and the effort you put into your application.
                </p>
                
                <p style="margin-bottom: 20px;">
                    After careful consideration of all applications, we have decided to 
                    <strong style="color: #e74c3c;">move forward with other candidates</strong> 
                    whose qualifications more closely match our current needs.
                </p>
                
                <div style="background: #fef9e7; padding: 20px; border-left: 4px solid #f39c12; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; color: #f39c12;">We Encourage You To:</p>
                    <ul style="margin: 10px 0 0 20px;">
                        <li>Keep an eye on our future job openings</li>
                        <li>Continue developing your skills and experience</li>
                        <li>Apply again when suitable positions become available</li>
                    </ul>
                </div>
                
                <p style="margin-bottom: 20px;">
                    We were impressed by your background and encourage you to apply for future opportunities 
                    that may be a better fit. We will keep your application on file and may reach out 
                    if a suitable position becomes available.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #667eea; color: white; padding: 15px 30px; border-radius: 25px; display: inline-block;">
                        <strong>🌟 Best of Luck in Your Job Search! 🌟</strong>
                    </div>
                </div>
                
                <p style="margin-bottom: 5px;"><strong>Best regards,</strong></p>
                <p style="margin-top: 0; color: #667eea; font-weight: bold;">E&S Decorations Recruiting Team</p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>© 2025 E&S Decorations. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version of the email
        plain_text = f"""
        Dear {applicant_name},

        Thank you for taking the time to apply for a position at E&S Decorations. We appreciate your interest in joining our team and the effort you put into your application.

        After careful consideration of all applications, we have decided to move forward with other candidates whose qualifications more closely match our current needs.

        We Encourage You To:
        • Keep an eye on our future job openings
        • Continue developing your skills and experience
        • Apply again when suitable positions become available

        We were impressed by your background and encourage you to apply for future opportunities that may be a better fit. We will keep your application on file and may reach out if a suitable position becomes available.

        🌟 Best of Luck in Your Job Search! 🌟

        Best regards,
        E&S Decorations Recruiting Team

        © 2025 E&S Decorations. All rights reserved.
        """

        # Send email using Resend
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [applicant_email],
            "subject": subject,
            "html": html_content,
            "text": plain_text,
            "reply_to": "esdecorationsind@gmail.com"
        }

        email_response = resend.Emails.send(params)
        
        # Handle different response formats
        email_id = None
        if hasattr(email_response, 'id'):
            email_id = email_response.id
        elif isinstance(email_response, dict) and 'id' in email_response:
            email_id = email_response['id']
        else:
            email_id = "unknown"
            
        print(f"✅ Rejection email sent successfully to {applicant_email}. Email ID: {email_id}")
        return email_response

    except Exception as e:
        print(f"❌ Error sending rejection email: {str(e)}")
        raise Exception(f"Failed to send rejection email: {str(e)}")

# Models
class EmailSchema(BaseModel):
    message: str

class Contact(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
    recaptcha_token: str = ""

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class AdminUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    new_password: str | None = None

class Token(BaseModel):
    access_token: str
    token_type: str

class FAQ(BaseModel):
    question: str
    answer: str
    category: str

# Job Listing Model
class JobListing(BaseModel):
    id: str
    title: str
    description: str
    requirements: List[str]
    type: str
    icon: str = "Users"  # Default icon
    isActive: bool = True

# Job Application Model
class JobApplication(BaseModel):
    jobId: str
    name: str
    email: str
    phone: str
    experience: str
    address: Optional[str] = None
    resume: Optional[str] = None  # Base64 encoded string for the resume
    status: str = "pending"  # pending, approved, rejected
    appliedDate: str

class ReplySchema(BaseModel):
    plain_text_body: str
    html_body: str

# Password Hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# Generate JWT Token
def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Authenticate Admin and Protect Routes
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def verify_recaptcha(token: str, client_ip: str) -> dict:
    """Verify reCAPTCHA token with Google's API"""
    if not RECAPTCHA_SECRET_KEY or not token:
        return {"success": False, "score": 0.0, "error": "Missing reCAPTCHA configuration"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": RECAPTCHA_SECRET_KEY,
                    "response": token,
                    "remoteip": client_ip
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": result.get("success", False),
                    "score": result.get("score", 0.0),
                    "action": result.get("action", ""),
                    "error": result.get("error-codes", [])
                }
            else:
                return {"success": False, "score": 0.0, "error": "reCAPTCHA verification failed"}
                
    except Exception as e:
        logging.error(f"reCAPTCHA verification error: {e}")
        return {"success": False, "score": 0.0, "error": str(e)}

def is_rate_limited(client_ip: str) -> bool:
    """Check if IP address has exceeded rate limit"""
    now = datetime.datetime.utcnow()
    
    ip_requests[client_ip] = [
        req_time for req_time in ip_requests[client_ip] 
        if now - req_time < datetime.timedelta(seconds=TIME_WINDOW)
    ]
    
    if len(ip_requests[client_ip]) >= IP_LIMIT:
        return True
    
    ip_requests[client_ip].append(now)
    return False

def validate_contact_form(contact) -> list:
    """Validate contact form data and return list of errors"""
    errors = []
    
    if not contact.name.strip():
        errors.append("Name is required")
    elif len(contact.name.strip()) < 2:
        errors.append("Name must be at least 2 characters")
    elif len(contact.name) > 100:
        errors.append("Name must be less than 100 characters")
    
    if not contact.message.strip():
        errors.append("Message is required")
    elif len(contact.message.strip()) < 10:
        errors.append("Message must be at least 10 characters")
    elif len(contact.message) > 1000:
        errors.append("Message must be less than 1000 characters")
    
    if len(contact.subject) > 150:
        errors.append("Subject must be less than 150 characters")
    
    return errors

def detect_spam_content(name: str, email: str, message: str, subject: str) -> bool:
    """Basic spam detection based on content analysis"""
    spam_keywords = [
        'viagra', 'casino', 'lottery', 'winner', 'congratulations',
        'million dollars', 'click here', 'buy now', 'limited time',
        'crypto', 'bitcoin', 'investment opportunity', 'make money fast'
    ]
    
    content = f"{name} {email} {subject} {message}".lower()
    spam_score = sum(1 for keyword in spam_keywords if keyword in content)
    
    if len([c for c in message if c.isupper()]) > len(message) * 0.7:
        spam_score += 1
    
    if message.count('http://') + message.count('https://') > 2:
        spam_score += 2
    
    import re
    if re.search(r'(.)\1{4,}', message):
        spam_score += 1
    
    return spam_score >= 2

# Submit Contact Form
@app.post("/submit")
async def submit_form(contact: Contact, request: Request):
    try:
        client_ip = request.client.host
        
        # Rate limiting check
        if is_rate_limited(client_ip):
            logging.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail="Too many requests. Please try again in an hour."
            )
        
        # Form validation
        validation_errors = validate_contact_form(contact)
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Validation errors: {', '.join(validation_errors)}"
            )
        
        # Spam content detection
        if detect_spam_content(contact.name, contact.email, contact.message, contact.subject):
            logging.warning(f"Spam content detected from IP: {client_ip}")
            is_flagged = True
        else:
            is_flagged = False
        
        # reCAPTCHA verification
        recaptcha_result = {"success": True, "score": 1.0}
        if contact.recaptcha_token:
            recaptcha_result = await verify_recaptcha(contact.recaptcha_token, client_ip)
            
            if not recaptcha_result["success"]:
                logging.warning(f"reCAPTCHA verification failed for IP {client_ip}: {recaptcha_result['error']}")
                raise HTTPException(
                    status_code=400, 
                    detail="Security verification failed. Please try again."
                )
            
            if recaptcha_result["score"] < RECAPTCHA_MINIMUM_SCORE:
                logging.warning(f"Low reCAPTCHA score for IP {client_ip}: {recaptcha_result['score']}")
                raise HTTPException(
                    status_code=400, 
                    detail="Security verification failed. Please try again."
                )
            
            logging.info(f"reCAPTCHA verified for IP {client_ip} with score {recaptcha_result['score']}")
        else:
            logging.warning(f"No reCAPTCHA token provided by IP {client_ip}")
        
        # Prepare contact data for database
        contact_data = {
            "name": contact.name.strip(),
            "email": contact.email,
            "subject": contact.subject.strip(),
            "message": contact.message.strip(),
            "is_solved": False,
            "is_flagged": is_flagged,
            "client_ip": client_ip,
            "created_at": datetime.datetime.utcnow(),
            "recaptcha_score": recaptcha_result.get("score", 0.0)
        }
        
        result = await contacts_collection.insert_one(contact_data)
        
        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Failed to save contact form")
        
        logging.info(f"Contact form submitted successfully by {contact.name} ({contact.email}) from IP {client_ip}")
        
        return {"message": "Form submitted successfully!"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error processing contact form: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request. Please try again later.")

# ADD this health endpoint if you don't have it
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    timestamp = datetime.datetime.utcnow().isoformat()
    return {
        "status": "healthy", 
        "timestamp": timestamp,
        "uptime": os.times().elapsed if hasattr(os, 'times') else 0
    }

# Fetch Unsolved Inquiries
@app.get("/inquiries")
async def get_inquiries():
    try:
        # Sort by created_at in descending order (newest first)
        cursor = contacts_collection.find({"is_solved": False}).sort("created_at", -1)
        inquiries = await cursor.to_list(length=None)
        
        # Convert ObjectId to string and format dates
        formatted_inquiries = []
        for inq in inquiries:
            formatted_inq = {
                "id": str(inq["_id"]),
                "name": inq["name"],
                "email": inq["email"],
                "subject": inq["subject"],
                "message": inq["message"],
                "is_solved": inq.get("is_solved", False),
                "created_at": inq.get("created_at", datetime.datetime.utcnow()).isoformat()
            }
            formatted_inquiries.append(formatted_inq)
            
        return formatted_inquiries
    except Exception as e:
        print(f"Error fetching inquiries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mark Inquiry as Solved
@app.patch("/inquiries/{inquiry_id}/solve")
async def solve_inquiry(inquiry_id: str):
    try:
        result = await contacts_collection.update_one(
            {"_id": ObjectId(inquiry_id)},
            {"$set": {"is_solved": True}}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inquiry not found")

        return {"message": "Inquiry marked as solved"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid inquiry ID")
    except Exception as e:
        print(f"Error marking inquiry as solved: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Updated function to send reply using Resend
@app.post("/inquiries/{inquiry_id}/reply")
async def reply_to_inquiry(inquiry_id: str, reply: ReplySchema):
    try:
        # ✅ Validate ObjectId
        if not ObjectId.is_valid(inquiry_id):
            raise HTTPException(status_code=400, detail="Invalid inquiry ID format")

        # ✅ Find the inquiry in the database
        inquiry = await contacts_collection.find_one({"_id": ObjectId(inquiry_id)})
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")

        # ✅ Ensure email field exists
        recipient_email = inquiry.get("email")
        if not recipient_email:
            raise HTTPException(status_code=400, detail="Inquiry has no associated email")

        recipient_name = inquiry.get("name", "Valued Customer")
        original_subject = inquiry.get("subject", "Your Inquiry")

        # Create professional reply email
        subject = f"Re: {original_subject} - E&S Decorations"
        
        # Enhanced HTML version
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reply from E&S Decorations</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">E&S Decorations</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0; font-size: 14px;">Thank you for reaching out to us</p>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{recipient_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Thank you for contacting E&S Decorations. We have received your inquiry and are pleased to respond:
                </p>
                
                <div style="background: white; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 5px;">
                    <p style="margin: 0; color: #666; font-size: 14px; font-weight: bold;">Your Original Message:</p>
                    <p style="margin: 10px 0 0 0; font-style: italic; color: #555;">"{inquiry.get('message', '')[:150]}{'...' if len(inquiry.get('message', '')) > 150 else ''}"</p>
                </div>
                
                <div style="background: #e8f4fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; font-weight: bold; color: #667eea; margin-bottom: 15px;">Our Response:</p>
                    <div style="color: #333; line-height: 1.6;">
                        {reply.html_body}
                    </div>
                </div>
                
                <div style="margin: 30px 0; padding: 15px; background: #f0f8ff; border-radius: 5px; text-align: center;">
                    <p style="margin: 0; color: #667eea; font-weight: bold;">Need further assistance?</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px;">Feel free to reply to this email or contact us directly.</p>
                </div>
                
                <p style="margin-bottom: 5px;"><strong>Best regards,</strong></p>
                <p style="margin-top: 0; color: #667eea; font-weight: bold;">E&S Decorations Team</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                    <p style="margin: 0;">📧 Email: esdecorationsind@gmail.com</p>
                    <p style="margin: 5px 0 0 0;">🌐 Creating beautiful spaces since [Year]</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>© 2025 E&S Decorations. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Enhanced plain text version
        plain_text = f"""
Dear {recipient_name},

Thank you for contacting E&S Decorations. We have received your inquiry and are pleased to respond:

Your Original Message:
"{inquiry.get('message', '')[:150]}{'...' if len(inquiry.get('message', '')) > 150 else ''}"

Our Response:
{reply.plain_text_body}

Need further assistance?
Feel free to reply to this email or contact us directly.

Best regards,
E&S Decorations Team

📧 Email: esdecorationsind@gmail.com
🌐 Creating beautiful spaces since [Year]

© 2025 E&S Decorations. All rights reserved.
        """

        # Send email using Resend
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [recipient_email],
            "subject": subject,
            "html": html_content,
            "text": plain_text,
            "reply_to": "esdecorationsind@gmail.com"
        }

        email_response = resend.Emails.send(params)
        
        # Handle different response formats
        email_id = None
        if hasattr(email_response, 'id'):
            email_id = email_response.id
        elif isinstance(email_response, dict) and 'id' in email_response:
            email_id = email_response['id']
        else:
            email_id = "unknown"
            
        print(f"✅ Reply email sent successfully to {recipient_email}. Email ID: {email_id}")

        # Update inquiry status
        await contacts_collection.update_one(
            {"_id": ObjectId(inquiry_id)},
            {"$set": {"is_solved": True}}
        )

        return {"message": "Reply sent successfully", "email_id": email_id}
        
    except Exception as e:
        logging.error(f"Error sending reply: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send reply")

# Admin Login with JWT
def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

async def send_admin_verification_email(email: str, code: str, admin_name: str = "Admin"):
    """Send verification code via email for admin login"""
    try:
        subject = "🔐 E&S Decorations - Admin Login Verification"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Admin Login Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🔐 Admin Login Verification</h1>
                <p style="color: #f0f0f0; margin: 10px 0 0 0;">E&S Decorations Security System</p>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <p style="font-size: 16px; margin-bottom: 20px;">Hello <strong>{admin_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Someone is attempting to access the E&S Decorations admin panel. If this is you, 
                    please use the verification code below to complete your login:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #667eea; color: white; padding: 25px; border-radius: 15px; font-size: 36px; font-weight: bold; letter-spacing: 8px; display: inline-block; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                        {code}
                    </div>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <p style="margin: 0; color: #856404; font-weight: bold;">⚠️ Security Notice:</p>
                    <ul style="margin: 10px 0 0 20px; color: #856404;">
                        <li>This code expires in <strong>5 minutes</strong></li>
                        <li>Never share this code with anyone</li>
                        <li>If you didn't request this, ignore this email</li>
                        <li>Only use this code on the official admin portal</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <p style="color: #666; font-size: 14px;">
                        This verification code was requested from the E&S Decorations admin system.
                        <br>Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
                    </p>
                </div>
                
                <div style="border-top: 1px solid #ddd; padding-top: 20px; margin-top: 30px; text-align: center;">
                    <p style="margin: 0; color: #667eea; font-weight: bold;">E&S Decorations Security Team</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">
                        This is an automated security message
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_text = f"""
        E&S Decorations - Admin Login Verification

        Hello {admin_name},

        Someone is attempting to access the E&S Decorations admin panel. If this is you, please use the verification code below to complete your login:

        Verification Code: {code}

        ⚠️ Security Notice:
        • This code expires in 5 minutes
        • Never share this code with anyone
        • If you didn't request this, ignore this email
        • Only use this code on the official admin portal

        Time: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

        E&S Decorations Security Team
        This is an automated security message
        """

        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [email],
            "subject": subject,
            "html": html_content,
            "text": plain_text,
            "reply_to": "esdecorationsind@gmail.com"
        }

        email_response = resend.Emails.send(params)
        print(f"✅ Admin verification email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Error sending admin verification email: {str(e)}")
        return False

# Replace your existing admin login endpoints with these two new endpoints:

@app.post("/admin-management-pambady-kayathumkal/request-verification")
async def request_admin_verification(request: RequestVerificationCode):
    """Step 1: Validate credentials and send verification code"""
    try:
        # First validate email and password
        admin = await admins_collection.find_one({"email": request.email})
        if not admin or not verify_password(request.password, admin["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Generate verification code
        code = generate_verification_code()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        
        # Store verification code
        verification_codes[request.email] = {
            "code": code,
            "expires": expires_at,
            "admin_name": admin.get("name", "Admin")
        }

        # Send verification email
        admin_name = admin.get("name", "Admin")
        success = await send_admin_verification_email(request.email, code, admin_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        print(f"✅ Verification code sent to {request.email}")
        return {
            "message": "Verification code sent to your email", 
            "email": request.email,
            "expires_in": "5 minutes"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error requesting verification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process request")

@app.post("/admin-management-pambady-kayathumkal/login", response_model=Token)
async def admin_login_with_2fa(login_request: AdminLoginRequest):
    """Step 2: Verify code and complete login"""
    try:
        # Check if verification code exists
        if login_request.email not in verification_codes:
            raise HTTPException(status_code=401, detail="No verification code requested. Please request a new code.")

        stored_data = verification_codes[login_request.email]
        
        # Check if code expired
        if datetime.datetime.utcnow() > stored_data["expires"]:
            del verification_codes[login_request.email]
            raise HTTPException(status_code=401, detail="Verification code expired. Please request a new code.")

        # Check if code matches
        if login_request.verification_code != stored_data["code"]:
            raise HTTPException(status_code=401, detail="Invalid verification code")

        # Verify admin credentials again (security)
        admin = await admins_collection.find_one({"email": login_request.email})
        if not admin or not verify_password(login_request.password, admin["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Clean up verification code
        del verification_codes[login_request.email]

        # Generate access token
        access_token = create_access_token(data={"sub": admin["email"]})
        
        print(f"✅ Admin {admin.get('name')} successfully logged in with 2FA")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error during 2FA login: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

# Add a cleanup endpoint (optional - for removing expired codes)
@app.post("/admin-management-pambady-kayathumkal/cleanup-codes")
async def cleanup_expired_codes():
    """Clean up expired verification codes"""
    try:
        now = datetime.datetime.utcnow()
        expired_emails = []
        
        for email, data in verification_codes.items():
            if now > data["expires"]:
                expired_emails.append(email)
        
        for email in expired_emails:
            del verification_codes[email]
        
        return {"message": f"Cleaned up {len(expired_emails)} expired codes"}
    except Exception as e:
        print(f"Error cleaning up codes: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

# Add New Admin
@app.post("/admin-management-pambady-kayathumkal/add")
async def add_admin(admin: AdminCreate):
    try:
        existing_admin = await admins_collection.find_one({"email": admin.email})
        if existing_admin:
            raise HTTPException(status_code=400, detail="Admin with this email already exists")

        hashed_password = hash_password(admin.password)
        new_admin = {
            "name": admin.name,
            "email": admin.email,
            "password": hashed_password,
            "created_at": datetime.datetime.utcnow()
        }

        result = await admins_collection.insert_one(new_admin)
        return {"message": "Admin added successfully", "admin_id": str(result.inserted_id)}
    except Exception as e:
        print(f"Error adding admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update Admin Details
@app.patch("/admin-management-pambady-kayathumkal/update/{admin_id}")
async def update_admin(admin_id: str, admin_update: AdminUpdate):
    try:
        update_data = {}

        if admin_update.name:
            update_data["name"] = admin_update.name
        if admin_update.email:
            update_data["email"] = admin_update.email
        if admin_update.new_password:
            update_data["password"] = hash_password(admin_update.new_password)

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = await admins_collection.update_one(
            {"_id": ObjectId(admin_id)}, 
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Admin not found")

        return {"message": "Admin updated successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid admin ID")
    except Exception as e:
        print(f"Error updating admin: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Listings Endpoints
@app.get("/job-listings")
async def get_job_listings():
    try:
        listings = await job_listings_collection.find().to_list(length=None)
        # Convert ObjectId to string for each listing
        for listing in listings:
            listing["_id"] = str(listing["_id"])
        return listings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job-listings")
async def create_job_listing(listing: JobListing):
    try:
        result = await job_listings_collection.insert_one(listing.dict())
        if result.inserted_id:
            created_listing = await job_listings_collection.find_one(
                {"_id": result.inserted_id}
            )
            created_listing["_id"] = str(created_listing["_id"])
            return created_listing
        raise HTTPException(status_code=500, detail="Failed to create job listing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/job-listings/{listing_id}")
async def update_job_listing(listing_id: str, listing: JobListing):
    try:
        result = await job_listings_collection.update_one(
            {"_id": ObjectId(listing_id)},
            {"$set": listing.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Job listing not found")
        updated_listing = await job_listings_collection.find_one(
            {"_id": ObjectId(listing_id)}
        )
        updated_listing["_id"] = str(updated_listing["_id"])
        return updated_listing
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/job-listings/{listing_id}")
async def delete_job_listing(listing_id: str):
    try:
        result = await job_listings_collection.delete_one(
            {"_id": ObjectId(listing_id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job listing not found")
        return {"message": "Job listing deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid listing ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Job Applications Endpoints
@app.get("/job-applications")
async def get_job_applications():
    try:
        applications = await job_applications_collection.find().to_list(length=None)
        # Convert ObjectId to string for each application
        for app in applications:
            app["_id"] = str(app["_id"])
            # If resume is bytes, convert to base64 string
            if isinstance(app.get("resume"), bytes):
                app["resume"] = base64.b64encode(app["resume"]).decode('utf-8')
        return applications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/job-applications")
async def submit_job_application(application: JobApplication):
    try:
        # Convert application to dict and handle the resume
        application_dict = application.dict()
        
        # If resume is provided as base64 string, decode it
        if application.resume and isinstance(application.resume, str):
            try:
                resume_bytes = base64.b64decode(application.resume)
                application_dict["resume"] = resume_bytes
            except:
                raise HTTPException(status_code=400, detail="Invalid resume format")
        
        # Insert application into database
        result = await job_applications_collection.insert_one(application_dict)
        
        if result.inserted_id:
            # Return the created application with string ID
            created_application = await job_applications_collection.find_one(
                {"_id": result.inserted_id}
            )
            created_application["_id"] = str(created_application["_id"])
            # Convert resume back to base64 if it exists
            if isinstance(created_application.get("resume"), bytes):
                created_application["resume"] = base64.b64encode(created_application["resume"]).decode('utf-8')
            return created_application
        
        raise HTTPException(status_code=500, detail="Failed to submit application")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/job-applications/{application_id}/status")
async def update_application_status(application_id: str, status: str):
    try:
        # First get the application to access the applicant's details
        application = await job_applications_collection.find_one({"_id": ObjectId(application_id)})
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Update the status
        result = await job_applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"status": status}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")

        # Send appropriate email based on status
        if status == "approved":
            await send_acceptance_email(
                applicant_name=application["name"],
                applicant_email=application["email"]
            )
        elif status == "rejected":
            await send_rejection_email(
                applicant_name=application["name"],
                applicant_email=application["email"]
            )

        return {"message": f"Application {status} successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid application ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FAQ Endpoints
@app.get("/faqs")
async def get_faqs():
    try:
        faqs = await faqs_collection.find().to_list(length=None)
        # Convert ObjectId to string for each FAQ
        for faq in faqs:
            faq["_id"] = str(faq["_id"])
        return faqs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/faqs")
async def create_faq(faq: FAQ):
    try:
        result = await faqs_collection.insert_one(faq.dict())
        if result.inserted_id:
            created_faq = await faqs_collection.find_one({"_id": result.inserted_id})
            created_faq["_id"] = str(created_faq["_id"])
            return created_faq
        raise HTTPException(status_code=500, detail="Failed to create FAQ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/faqs/{faq_id}")
async def update_faq(faq_id: str, faq: FAQ):
    try:
        result = await faqs_collection.update_one(
            {"_id": ObjectId(faq_id)},
            {"$set": faq.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found")
        updated_faq = await faqs_collection.find_one({"_id": ObjectId(faq_id)})
        updated_faq["_id"] = str(updated_faq["_id"])
        return updated_faq
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid FAQ ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    try:
        result = await faqs_collection.delete_one({"_id": ObjectId(faq_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found")
        return {"message": "FAQ deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid FAQ ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Latest Works Endpoints

# New image upload endpoint
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        print(f"\n🚀 Starting upload for: {file.filename}")
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        if len(file_content) > image_compressor.MAX_FILE_SIZE:
            max_mb = image_compressor.MAX_FILE_SIZE / (1024*1024)
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {max_mb}MB"
            )
        
        if not image_compressor.is_image_by_filename(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="File type not supported. Please upload: JPG, PNG, GIF, BMP, WebP, TIFF, or HEIC"
            )
        
        is_valid, validation_message = image_compressor.is_image(file_content)
        if not is_valid:
            raise HTTPException(status_code=400, detail=validation_message)
        
        print(f"✅ Validation passed: {validation_message}")
        
        file_size = len(file_content)
        print(f"📏 File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        
        # Check if it's a HEIC file - always convert these
        is_heic = file.filename.lower().endswith(('.heic', '.heif'))
        
        if file_size > image_compressor.MAX_SIZE_BYTES or is_heic:
            if is_heic:
                print(f"🔄 HEIC file detected - converting to JPEG for web compatibility")
            else:
                print(f"🗜️  File exceeds 15MB - applying compression")
            
            try:
                if file_size > 25 * 1024 * 1024:
                    final_content, metadata = image_compressor.progressive_compress(file_content)
                else:
                    final_content, metadata = image_compressor.convert_to_web_format(file_content)
                
                compression_applied = True
                
                if is_heic:
                    print(f"✅ HEIC converted to JPEG: {metadata.get('savings_percent', 0)}% size change")
                else:
                    print(f"✅ Compressed: {metadata['savings_percent']}% savings")
                
            except Exception as e:
                print(f"❌ Processing failed: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
            
        else:
            print(f"✨ File within 15MB limit")
            # Still convert to JPEG for consistency (optional)
            try:
                final_content, metadata = image_compressor.convert_to_web_format(file_content, quality=95)
                compression_applied = True
                print(f"🔄 Converted to JPEG for web compatibility")
            except:
                # Fallback to original if conversion fails
                final_content = file_content
                compression_applied = False
                metadata = {
                    'original_size': file_size,
                    'final_size': file_size,
                    'compression_ratio': 1.0,
                    'savings_percent': 0,
                    'method': 'no_processing',
                    'reason': 'under_15mb_limit'
                }
        
        # Convert to base64 - this should now always be a JPEG
        base64_string = base64.b64encode(final_content).decode('utf-8')
        
        print(f"🎯 Final: {len(final_content):,} bytes as JPEG")
        
        return {
            "image": base64_string,
            "compression_applied": compression_applied,
            "metadata": metadata,
            "file_info": {
                "filename": file.filename,
                "original_size": file_size,
                "final_size": len(final_content),
                "content_type": "image/jpeg",  # Always JPEG output
                "web_compatible": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/compression-stats")
async def get_compression_stats():
    """Get compression statistics from recent uploads"""
    try:
        # You could track these in a separate collection if needed
        return {
            "max_size_limit": f"{image_compressor.MAX_SIZE_BYTES / (1024*1024):.1f} MB",
            "compression_enabled": True,
            "supported_formats": ["JPEG", "PNG", "WebP", "GIF", "BMP"],
            "max_dimensions": "1920x1080",
            "default_quality": 85
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Gallery Event Management Endpoints
@app.get("/gallery-events")
async def get_gallery_events():
    try:
        events = await events_collection.find({"type": "gallery"}).to_list(length=None)
        # Convert ObjectId to string for each event
        for event in events:
            event["_id"] = str(event["_id"])
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gallery-events")
async def create_gallery_event(event: GalleryEventCreate):
    try:
        event_dict = event.dict()
        event_dict["type"] = "gallery"  # Add type field to distinguish gallery events
        result = await events_collection.insert_one(event_dict)
        if result.inserted_id:
            created_event = await events_collection.find_one(
                {"_id": result.inserted_id}
            )
            created_event["_id"] = str(created_event["_id"])
            return created_event
        raise HTTPException(status_code=500, detail="Failed to create event")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/gallery-events/{event_id}")
async def update_gallery_event(event_id: str, event: GalleryEventUpdate):
    try:
        event_dict = event.dict()
        event_dict["type"] = "gallery"  # Ensure type remains gallery
        result = await events_collection.update_one(
            {"_id": ObjectId(event_id), "type": "gallery"},
            {"$set": event_dict}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Gallery event not found")
        updated_event = await events_collection.find_one(
            {"_id": ObjectId(event_id)}
        )
        updated_event["_id"] = str(updated_event["_id"])
        return updated_event
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/gallery-events/{event_id}")
async def delete_gallery_event(event_id: str):
    try:
        result = await events_collection.delete_one(
            {"_id": ObjectId(event_id), "type": "gallery"}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Gallery event not found")
        return {"message": "Gallery event deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/latest-works")
async def get_latest_works():
    try:
        works = await latest_works_collection.find().to_list(length=None)
        # Convert ObjectId to string for each work
        for work in works:
            work["_id"] = str(work["_id"])
        return works
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/latest-works")
async def create_latest_work(work: dict):
    try:
        # Validate required fields
        if not all(key in work for key in ["title", "thumbnail", "category"]):
            raise HTTPException(status_code=422, detail="Missing required fields")

        # Add compression metadata if available
        if "compression_metadata" not in work and "thumbnail" in work:
            # If thumbnail is already processed, add basic metadata
            work["compression_metadata"] = {
                "method": "unknown",
                "processed": True
            }

        # Insert the work into MongoDB
        result = await latest_works_collection.insert_one(work)
        
        if result.inserted_id:
            created_work = await latest_works_collection.find_one({"_id": result.inserted_id})
            created_work["_id"] = str(created_work["_id"])
            return created_work
            
        raise HTTPException(status_code=500, detail="Failed to create work")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/test-compression")
async def test_compression(file: UploadFile = File(...)):
    """Test endpoint to see compression results without saving"""
    try:
        file_content = await file.read()
        
        if not image_compressor.is_image(file_content):
            raise HTTPException(status_code=400, detail="File is not a valid image")
        
        file_size = len(file_content)
        
        # Always compress for testing
        compressed_content, metadata = image_compressor.compress_image(file_content)
        progressive_content, progressive_metadata = image_compressor.progressive_compress(file_content)
        
        return {
            "original_size": file_size,
            "original_size_mb": round(file_size / (1024*1024), 2),
            "compression_needed": file_size > image_compressor.MAX_SIZE_BYTES,
            "standard_compression": {
                "size": metadata['final_size'],
                "size_mb": round(metadata['final_size'] / (1024*1024), 2),
                "savings": metadata['savings_percent']
            },
            "progressive_compression": {
                "size": progressive_metadata['final_size'],
                "size_mb": round(progressive_metadata['final_size'] / (1024*1024), 2),
                "savings": progressive_metadata['savings_percent']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/latest-works/{work_id}")
async def update_latest_work(work_id: str, work: dict):
    try:
        # Validate work_id
        if not ObjectId.is_valid(work_id):
            raise HTTPException(status_code=400, detail="Invalid work ID format")

        # Validate required fields
        if not all(key in work for key in ["title", "thumbnail", "category"]):
            raise HTTPException(status_code=422, detail="Missing required fields")

        result = await latest_works_collection.update_one(
            {"_id": ObjectId(work_id)},
            {"$set": work}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Work not found")
            
        if result.modified_count == 0:
            raise HTTPException(status_code=304, detail="No changes made")
            
        updated_work = await latest_works_collection.find_one({"_id": ObjectId(work_id)})
        updated_work["_id"] = str(updated_work["_id"])
        return updated_work
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid work ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/latest-works/{work_id}")
async def delete_latest_work(work_id: str):
    try:
        # Validate work_id
        if not ObjectId.is_valid(work_id):
            raise HTTPException(status_code=400, detail="Invalid work ID format")

        # Check if work exists before deleting
        work = await latest_works_collection.find_one({"_id": ObjectId(work_id)})
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")

        result = await latest_works_collection.delete_one({"_id": ObjectId(work_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete work")
            
        return {"message": "Work deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid work ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Test endpoint to verify Resend integration
@app.post("/test-email")
async def test_email_sending():
    """Test endpoint to verify Resend API is working correctly"""
    try:
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": ["esdecorationsind@gmail.com"],  # Send test email to yourself
            "subject": "🧪 E&S Decorations - Resend API Test",
            "html": """
            <div style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
                <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #667eea; text-align: center;">✅ Resend API Test Successful!</h2>
                    <p>This is a test email to verify that Resend API integration is working correctly with your E&S Decorations website.</p>
                    <p><strong>Test Details:</strong></p>
                    <ul>
                        <li>API Integration: ✅ Working</li>
                        <li>Email Sending: ✅ Successful</li>
                        <li>From Address: esdecorationsind@gmail.com</li>
                        <li>Test Time: Just now</li>
                    </ul>
                    <p style="text-align: center; margin-top: 30px;">
                        <span style="background: #667eea; color: white; padding: 10px 20px; border-radius: 5px;">
                            🎉 Ready for Production!
                        </span>
                    </p>
                </div>
            </div>
            """,
            "text": "✅ Resend API Test Successful! This test email confirms that Resend API integration is working correctly with your E&S Decorations website.",
            "reply_to": "esdecorationsind@gmail.com"
        }

        email_response = resend.Emails.send(params)
        
        # Handle different response formats
        email_id = None
        if hasattr(email_response, 'id'):
            email_id = email_response.id
        elif isinstance(email_response, dict) and 'id' in email_response:
            email_id = email_response['id']
        else:
            email_id = "unknown"
            
        return {
            "success": True,
            "message": "Test email sent successfully!",
            "email_id": email_id,
            "from": EMAIL_FROM,
            "to": "esdecorationsind@gmail.com"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to send test email. Please check your Resend API configuration."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)