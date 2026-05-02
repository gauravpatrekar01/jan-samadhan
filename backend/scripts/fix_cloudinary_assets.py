import os
import cloudinary
import cloudinary.api
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Configure MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DATABASE_NAME", "jansamadhan")]

def fix_assets():
    print("Starting Cloudinary Asset Fix...")
    
    complaints = db.get_collection("complaints").find({"media": {"$exists": True, "$not": {"$size": 0}}})
    
    fixed_count = 0
    error_count = 0
    
    for complaint in complaints:
        media_list = complaint.get("media", [])
        updated = False
        
        for media in media_list:
            public_id = media.get("public_id")
            if not public_id:
                continue
                
            try:
                print(f"Fixing asset: {public_id}")
                
                # Try to find and update resource across all types
                found = False
                for r_type in ["image", "video", "raw"]:
                    try:
                        # Check if resource exists with this type
                        cloudinary.api.resource(public_id, resource_type=r_type)
                        
                        # Update it
                        result = cloudinary.api.update(
                            public_id,
                            resource_type=r_type,
                            access_mode="public",
                            type="upload"
                        )
                        print(f"Fixed {public_id} as {r_type}: {result.get('secure_url')}")
                        fixed_count += 1
                        
                        if result.get("secure_url") and result.get("secure_url") != media.get("url"):
                            media["url"] = result.get("secure_url")
                            updated = True
                        
                        found = True
                        break
                    except Exception:
                        continue
                
                if not found:
                    print(f"Could not find asset {public_id} in any resource type")
                    error_count += 1
                    
            except Exception as e:
                print(f"Error fixing {public_id}: {str(e)}")
                error_count += 1
        
        if updated:
            db.get_collection("complaints").update_one(
                {"id": complaint["id"]},
                {"$set": {"media": media_list}}
            )

    print(f"\nFix Complete!")
    print(f"Assets Updated: {fixed_count}")
    print(f"Errors Encountered: {error_count}")

if __name__ == "__main__":
    fix_assets()
