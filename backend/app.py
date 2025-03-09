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
faqs_collection = db["faqs"]  # New collection for FAQs

# JWT Security
SECRET_KEY = os.getenv("SECRET_KEY", "miniproject")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")

# Models
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

# FAQ Management Endpoints
@app.get("/faqs")
async def get_faqs():
    try:
        faqs = await faqs_collection.find().to_list(length=None)
        return [{**faq, "_id": str(faq["_id"])} for faq in faqs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/faqs")
async def create_faq(faq: FAQ, _: dict = Depends(get_current_admin)):
    try:
        result = await faqs_collection.insert_one(faq.dict())
        if result.inserted_id:
            return {"message": "FAQ created successfully", "id": str(result.inserted_id)}
        raise HTTPException(status_code=500, detail="Failed to create FAQ")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/faqs/{faq_id}")
async def update_faq(faq_id: str, faq: FAQ, _: dict = Depends(get_current_admin)):
    try:
        result = await faqs_collection.update_one(
            {"_id": ObjectId(faq_id)},
            {"$set": faq.dict()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found")
        return {"message": "FAQ updated successfully"}
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid FAQ ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: str, _: dict = Depends(get_current_admin)):
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
