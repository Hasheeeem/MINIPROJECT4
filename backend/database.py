import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.getenv("DB_NAME", "ESWEBSITE")

# Ensure variables are set correctly
if not MONGODB_URL:
    raise ValueError("MONGODB_URL is not set!")
if not DB_NAME:
    raise ValueError("DB_NAME is not set!")

# Create MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DB_NAME]

# Debugging
print(f"Connected to MongoDB at {MONGODB_URL}, Database: {DB_NAME}")

# Initialize collections
contacts_collection = database["contacts"]
admins_collection = database["admins"]

# Create indexes
async def init_db():
    # Create indexes for contacts collection
    await contacts_collection.create_index("email")
    await contacts_collection.create_index("created_at")
    await contacts_collection.create_index("is_solved")
    
    # Create indexes for admins collection
    await admins_collection.create_index("email", unique=True)
    
    print("Database indexes created successfully")

# Export collections
__all__ = ["database", "contacts_collection", "admins_collection", "init_db"]
