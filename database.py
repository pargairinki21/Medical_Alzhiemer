"""
database.py
─────────────────────────────────────────────────────────────
MongoDB database operations for user authentication
─────────────────────────────────────────────────────────────
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import config
import random
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self.otps_collection = None
        self.demo_mode = False
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            # Use environment variable directly
            mongo_url = os.getenv("MONGO_DB_URL")
            if not mongo_url:
                print("⚠️ MONGO_DB_URL not found in environment variables")
                self.demo_mode = True
                self._init_demo_storage()
                return
            
            print(f"Connecting to MongoDB with URL: {mongo_url[:30]}...")
            
            # Connect with proper options for MongoDB Atlas
            self.client = MongoClient(
                mongo_url,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=30000,
                retryWrites=True,
                w='majority'
            )
            
            self.db = self.client["stay_app"]
            self.users_collection = self.db["users"]
            self.otps_collection = self.db["otps"]
            
            # Test connection with a simple command
            self.db.list_collection_names()
            print("✅ Connected to MongoDB")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("🔄 Falling back to demo mode (in-memory storage)")
            self.demo_mode = True
            self._init_demo_storage()
    
    def _init_demo_storage(self):
        """Initialize in-memory storage for demo mode"""
        self.demo_users = {}
        self.demo_otps = {}
        print("✅ Demo mode initialized")
    
    def create_user(self, email, name, gender):
        """Create or update user"""
        user = {
            "email": email,
            "name": name,
            "gender": gender,
            "profile_image": "",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        if self.demo_mode:
            # Demo mode: use in-memory storage
            if email in self.demo_users:
                self.demo_users[email].update({
                    "name": name,
                    "gender": gender,
                    "profile_image": self.demo_users[email].get("profile_image", ""),
                    "last_login": datetime.utcnow()
                })
                return self.demo_users[email]
            else:
                self.demo_users[email] = user
                return user
        else:
            # MongoDB mode
            existing_user = self.users_collection.find_one({"email": email})
            if existing_user:
                self.users_collection.update_one(
                    {"email": email},
                    {"$set": {"name": name, "gender": gender, "last_login": datetime.utcnow()}}
                )
                return self.users_collection.find_one({"email": email})
            else:
                self.users_collection.insert_one(user)
                return user
    
    def get_user(self, email):
        """Get user by email"""
        if self.demo_mode:
            return self.demo_users.get(email)
        else:
            return self.users_collection.find_one({"email": email})

    def update_user_profile(self, current_email, name, gender, new_email=None, profile_image=""):
        """Update user profile details and optional email/profile image"""
        target_email = (new_email or current_email).strip()

        if self.demo_mode:
            user = self.demo_users.get(current_email)
            if not user:
                return None

            # If email changed, move key
            if target_email != current_email:
                self.demo_users[target_email] = user
                del self.demo_users[current_email]
                user = self.demo_users[target_email]

            user.update({
                "email": target_email,
                "name": name,
                "gender": gender,
                "profile_image": profile_image or "",
                "last_login": datetime.utcnow()
            })
            return user

        # Mongo mode
        user = self.users_collection.find_one({"email": current_email})
        if not user:
            return None

        # Prevent duplicate email if changing to one that already exists
        if target_email != current_email:
            existing = self.users_collection.find_one({"email": target_email})
            if existing:
                raise ValueError("Email already exists")

        self.users_collection.update_one(
            {"email": current_email},
            {"$set": {
                "email": target_email,
                "name": name,
                "gender": gender,
                "profile_image": profile_image or "",
                "last_login": datetime.utcnow()
            }}
        )
        return self.users_collection.find_one({"email": target_email})
    
    def generate_otp(self, email):
        """Generate and store OTP"""
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        otp_data = {
            "email": email,
            "otp": otp,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "used": False
        }

        if self.demo_mode:
            # Demo mode: use in-memory storage
            self.demo_otps[email] = otp_data
        else:
            # MongoDB mode
            self.otps_collection.insert_one(otp_data)

        # Send OTP via email in background thread (non-blocking)
        import threading
        email_thread = threading.Thread(target=self.send_email_otp, args=(email, otp))
        email_thread.daemon = True
        email_thread.start()

        return otp
    
    def send_email_otp(self, email, otp):
        """Send OTP via email using Gmail SMTP"""
        try:
            if not config.EMAIL_ADDRESS or not config.EMAIL_PASSWORD:
                print("⚠️ Email credentials not configured, skipping email send")
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = config.EMAIL_ADDRESS
            msg['To'] = email
            msg['Subject'] = 'Your Stay Verification Code'
            
            body = f"""
            <html>
            <body>
                <h2>Welcome to Stay!</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #8b5cf6; font-size: 32px;">{otp}</h1>
                <p>This code will expire in 5 minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The Stay Team</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email via Gmail SMTP
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ OTP sent to {email}")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            print("⚠️ OTP will still work (returned in API response for demo)")
    
    def verify_otp(self, email, otp):
        """Verify OTP"""
        if self.demo_mode:
            # Demo mode: check in-memory storage
            otp_data = self.demo_otps.get(email)
            if otp_data and not otp_data["used"] and otp_data["otp"] == otp:
                if datetime.utcnow() < otp_data["expires_at"]:
                    otp_data["used"] = True
                    return True
            return False
        else:
            # MongoDB mode
            otp_data = self.otps_collection.find_one({
                "email": email,
                "otp": otp,
                "used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if otp_data:
                self.otps_collection.update_one(
                    {"_id": otp_data["_id"]},
                    {"$set": {"used": True}}
                )
                return True
            return False
    
    def cleanup_expired_otps(self):
        """Clean up expired OTPs"""
        if self.demo_mode:
            # Demo mode: clean up in-memory storage
            current_time = datetime.utcnow()
            for email in list(self.demo_otps.keys()):
                if self.demo_otps[email]["expires_at"] < current_time:
                    del self.demo_otps[email]
        else:
            # MongoDB mode
            self.otps_collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })


# Global database instance
db = Database()
