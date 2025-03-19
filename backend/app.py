from fastapi import FastAPI, HTTPException, Depends
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
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import logging


# Load environment variables
load_dotenv()

# FastAPI Instance
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
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

load_dotenv()  # Load environment variables

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = os.getenv("MAIL_PORT")
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_TLS = os.getenv("MAIL_TLS") == "True"  # Convert string to boolean
MAIL_SSL = os.getenv("MAIL_SSL") == "True"

# Models
class EmailSchema(BaseModel):
    message: str

class Contact(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

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

class LatestWork(BaseModel):
    title: str
    link: str
    thumbnail: str
    category: str

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

# Latest Works Endpoints
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
async def create_latest_work(work: LatestWork):
    try:
        result = await latest_works_collection.insert_one(work.dict())
        if result.inserted_id:
            created_work = await latest_works_collection.find_one({"_id": result.inserted_id})
            created_work["_id"] = str(created_work["_id"])
            return created_work
        raise HTTPException(status_code=500, detail="Failed to create work")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/latest-works/{work_id}")
async def update_latest_work(work_id: str, work: LatestWork):
    try:
        result = await latest_works_collection.update_one(
            {"_id": ObjectId(work_id)},
            {"$set": work.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Work not found")
        updated_work = await latest_works_collection.find_one({"_id": ObjectId(work_id)})
        updated_work["_id"] = str(updated_work["_id"])
        return updated_work
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid work ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/latest-works/{work_id}")
async def delete_latest_work(work_id: str):
    try:
        result = await latest_works_collection.delete_one({"_id": ObjectId(work_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Work not found")
        return {"message": "Work deleted successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid work ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FAQ Management Endpoints
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

# Submit Contact Form
@app.post("/submit")
async def submit_form(contact: Contact):
    try:
        contact_data = contact.dict()
        contact_data["is_solved"] = False  # Default status
        contact_data["created_at"] = datetime.datetime.utcnow()
        
        result = await contacts_collection.insert_one(contact_data)
        
        if not result.acknowledged:
            raise HTTPException(status_code=500, detail="Failed to save contact form")
            
        return {"message": "Form submitted successfully!"}
    except Exception as e:
        print(f"Error submitting form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Send Reply to Inquiry
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

        # ✅ Use the admin's custom reply from the request
        message = MessageSchema(
            subject="Reply to Your Inquiry - E&S Decorations",
            recipients=[recipient_email],  
            body=reply.html_body,  # Use custom HTML message
            subtype="html",
            alternatives=[(reply.plain_text_body, "plain")]  # Use custom plain text
        )

        fm = FastMail(email_conf)
        await fm.send_message(message, template_name=None)

        # ✅ Update inquiry status to solved
        await contacts_collection.update_one(
            {"_id": ObjectId(inquiry_id)},
            {"$set": {"is_solved": True}}
        )

        return {"message": "Reply sent successfully"}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logging.error(f"Error sending reply: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



# Admin Login with JWT
@app.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        admin = await admins_collection.find_one({"email": form_data.username})
        
        if not admin or not verify_password(form_data.password, admin["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        access_token = create_access_token(data={"sub": admin["email"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add New Admin
@app.post("/admin/add")
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
@app.patch("/admin/update/{admin_id}")
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