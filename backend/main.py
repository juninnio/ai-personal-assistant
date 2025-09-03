from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Literal
import json
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import uuid
import os
from dotenv import load_dotenv
import uvicorn

#google Oauth and API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google import genai
from google.genai import types
from gmail import new_fetch
from google_calendar import get_calendar_timezone, fetch_date_events, add_events, get_email_id

app = FastAPI()
load_dotenv() #Load env so we don't need to set up api keys

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
SECRET_KEY = "secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = 'ai_app.db'

#Google
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

genai_client = genai.Client()
GEMINI_MODEL = 'gemini-2.5-flash'

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class UserRegister(BaseModel):
    username:str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class CategorizeEmails(BaseModel):
    importance: bool = Field(description="Determine if this email is important based on its impact: For general emails - important if it greatly affects daily life, personal responsibilities, or requires immediate action (financial alerts, service outages, critical updates). For events - important if attendance is strictly advised or impacts personal/professional life (work meetings, close friend invitations, birthday parties). Mass promotional events are not important.")
    category: Literal['general','email'] = Field(description="Classify the email type: 'event' if the email contains an invitation to an occasion (meetings, dinners, parties, conferences, appointments). 'general' for all other emails including newsletters, notifications, updates, personal messages, or any communication that is not an invitation.")

class EventSummary(BaseModel):
    event_name: str = Field(description='Name of the event')
    event_type: str = Field(description='Type of the event')
    event_start: datetime = Field(description='Start Date and time of the event. MUST use format: YYYY-MM-DD HH:MM (e.g., 2025-07-29 14:30)')
    event_end: datetime = Field(description='End Date and time of the event. MUST use format: YYYY-MM-DD HH:MM (e.g., 2025-07-29 14:30). If none specified, add 1 hour to start time.')
    event_summary: str= Field(description='Summary of the email and event')

class GeneralSummary(BaseModel):
    email_summary: str= Field(description='Detailed summary of the email')

class EmailFetchRequest(BaseModel):
    email_count: int= 10

def init_database():
    with sqlite3.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                token_expiry TIMESTAMP,
                google_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ignored_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, email_id)
            )
        """)

        conn.commit()
        print("Database intialized successfully")

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
def create_google_oauth_flow():
    flow = Flow.from_client_config(
        {
            'web':{
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'auth_uri' : "https://accounts.google.com/o/oauth2/auth",
                'token_uri': "https://oauth2.googleapis.com/token",
                "redirect_uri": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow

def get_google_credentials(user_id: int) -> Optional[Credentials]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT access_token, refresh_token, token_expiry 
            FROM google_credentials WHERE user_id = ?
        """, (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return None
        
        expiry = result['token_expiry']
        if isinstance(expiry, str):
            expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
        
        creds = Credentials(
            token=result['access_token'],
            refresh_token=result['refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )
        
        # Refresh if expired
        if expiry:
            creds.expiry = expiry
        
        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Update database with new token
                cursor.execute("""
                    UPDATE google_credentials 
                    SET access_token = ?, token_expiry = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (creds.token, creds.expiry.isoformat() if creds.expiry else None, user_id))
                conn.commit()
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        
        return creds
    
def save_google_credentials(user_id: int, credentials: Credentials, google_email: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO google_credentials 
            (user_id, access_token, refresh_token, token_expiry, google_email, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, credentials.token, credentials.refresh_token, credentials.expiry, google_email))
        conn.commit()

def fetch_emails(credentials: Credentials, email_count: int = 10) -> List[Dict]:
    try:
        results = new_fetch(credentials=credentials, email_count=email_count)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to fetch emails: {str(e)}')
    
    return results

def add_cal_event(credentials: Credentials, email_id: str, event_data: Dict, timezone: str) -> Dict:
    try:
        result = add_events(credentials=credentials, email_id=email_id, event=event_data, timezone=timezone)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add event to Calendar: {str(e)}")
    
def fetch_calendar(credentials: Credentials, start_date: datetime, timezone: str):
    try:
        events = fetch_date_events(credentials=credentials, start_date=start_date, timezone=timezone)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch calendar events: {str(e)}")
    
def get_email_id_cal(event_data: Dict):
    try:
        email_id = get_email_id(event=event_data)
        return email_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get email id: {str(e)}")
    
def get_ignored_event_ids(user_id: int) -> set:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email_id FROM ignored_events WHERE user_id = ?", (user_id,))
        results = cursor.fetchall()
        return set(row['email_id'] for row in results)

def add_ignored_event(user_id: int, email_id: str):
    """Add email ID to ignored events"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO ignored_events (user_id, email_id)
            VALUES (?, ?)
        """, (user_id, email_id))
        conn.commit()

#feed to ai functions
def categorize_email(email_text: str) -> Dict:
    system_instruction = """You are an email categorization agent. Analyze the email and determine:
    1. Is this email important?
    2. What category does it belong to (event or general)?
    
    Be precise and only focus on classification."""
    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="CategorizeEmails",
            description="Categorize email importance and type",
            parameters=CategorizeEmails.model_json_schema()
        )
    ])]
    
    config = types.GenerateContentConfig(tools=tools, system_instruction=system_instruction)

    try:
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=email_text,
            config=config
        )
        
        # Extract categorization result
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call.name == "CategorizeEmails":
                    function_args = dict(part.function_call.args)
                    return {
                        'importance': function_args.get('importance', False),
                        'category': function_args.get('category', 'general')
                    }
        
        return {'importance': False, 'category': 'general'}
    
    except Exception as e:
        print(f"Error categorizing email: {str(e)}")
        return {'importance': False, 'category': 'general'}

def summarize_event_email(email_text: str) -> Dict:
    """Second step: Summarize event email with detailed event information."""
    system_instruction = f"""You are an event summarization agent. Extract all event details from this email including:
    - Event name and type
    - Date and time (start/end)
    - Summary of the event and email content
    
    Be thorough and accurate with dates and times. Today is {datetime.now()}"""

    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="EventSummary",
            description="Extract detailed event information",
            parameters=EventSummary.model_json_schema()
        )
    ])]
    
    config = types.GenerateContentConfig(tools=tools, system_instruction=system_instruction)
    
    try:
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=email_text,
            config=config
        )
        
        # Extract event summary result
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call.name == "EventSummary":
                    return dict(part.function_call.args)
        
        return {}
    
    except Exception as e:
        print(f"Error summarizing event email: {str(e)}")
        return {}

def summarize_general_email(email_text: str) -> Dict:
    """Second step: Summarize general email content."""
    system_instruction = """You are a general email summarization agent. Provide a comprehensive summary of this email's content, highlighting:
    - Key points and main message
    - Any action items or important information
    - Context and relevance
    
    Be concise but thorough. Use proper styling and don't use markdown formatting"""

    tools = [types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="GeneralSummary",
            description="Provide detailed email summary",
            parameters=GeneralSummary.model_json_schema()
        )
    ])]
    
    config = types.GenerateContentConfig(tools=tools, system_instruction=system_instruction)
    
    try:
        response = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=email_text,
            config=config
        )
        
        # Extract general summary result
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call.name == "GeneralSummary":
                    return dict(part.function_call.args)
        
        return {}
    
    except Exception as e:
        print(f"Error summarizing general email: {str(e)}")
        return {}

def categorize_and_summarize_email(email_text: str) -> Dict:
    """Main function: Categorize first, then summarize based on category and importance."""
    try:
        # Step 1: Categorize the email
        categorization = categorize_email(email_text)
        
        # If not important, return early with minimal data
        if not categorization['importance']:
            return {
                'importance': False,
                'category': categorization['category'],
                'content': {}
            }
        
        # Step 2: Summarize based on category (only for important emails)
        if categorization['category'] == 'event':
            content = summarize_event_email(email_text)
        else:
            content = summarize_general_email(email_text)
        
        return {
            'importance': True,
            'category': categorization['category'],
            'content': content
        }
    
    except Exception as e:
        print(f"Error in categorize_and_summarize_email: {str(e)}")
        return {'importance': False, 'category': 'general', 'content': {}}


init_database()

@app.get("/")
def read_root():
    return {"message": "What are you doing here"}

@app.post("/register")
def register(user: UserRegister):
    """Register a new user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                         (user.username, user.email))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Username or email already registered")
            
            # Hash password and create user
            hashed_password = get_password_hash(user.password)
            cursor.execute(
                "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
                (user.username, user.email, hashed_password)
            )
            conn.commit()
            
            return {"message": "User registered successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.post("/login")
def login(user: UserLogin):
    """Login and return access token"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, hashed_password FROM users WHERE username = ?", 
                         (user.username,))
            db_user = cursor.fetchone()
            
            if not db_user or not verify_password(user.password, db_user["hashed_password"]):
                raise HTTPException(status_code=401, detail="Incorrect username or password")
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(db_user["id"])}, expires_delta=access_token_expires
            )

            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": db_user["username"],
                "user_id": db_user['id']
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
    
@app.get('/auth/google')
def google_auth(current_user_id: int = Depends(verify_token)):
    flow = create_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=str(current_user_id)
    )

    return {'authorization_url': authorization_url}

@app.get('/auth/google/callback')
def google_callback(code: str, state:str):
    try:
        user_id = int(state)
        flow = create_google_oauth_flow()
        flow.fetch_token(code= code)

        credentials = flow.credentials

        user_info_service = build('oauth2','v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        google_email = user_info.get('email')

        save_google_credentials(user_id=user_id, credentials=credentials, google_email=google_email)

        return RedirectResponse(url="http://localhost:3000/?google_auth=success")
    
    except Exception as e:
        return RedirectResponse(url=f"http://localhost:3000/dashboard?google_auth=error&message={str(e)}")
    
@app.get("/google/status")
def google_auth_status(current_user_id: int = Depends(verify_token)):
    credentials = get_google_credentials(current_user_id)
    return{'connected': credentials is not None}

@app.post("/fetch-emails")
def fetch_and_process_emails(
    request: EmailFetchRequest,
    current_user_id: int = Depends(verify_token)
):
    try:
        credentials = get_google_credentials(current_user_id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Google account not connected")
        
        emails = fetch_emails(credentials, request.email_count)

        timezone = get_calendar_timezone(credentials)

        ignored_email_ids = get_ignored_event_ids(current_user_id)

        pending_events = []
        summarized_emails = []
        
        for email in emails:
            # Get AI analysis
            ai_result = categorize_and_summarize_email(email['text'])
            if not ai_result:
                continue
            
            important = ai_result['importance']
            
            if important:
                if ai_result['category'] != 'event':
                    # Important general email
                    email_data = {
                        'id': str(uuid.uuid4()),
                        'email_id': email['id'],
                        'sender': email['sender'],
                        'subject': email.get('subject', ''),
                        'category': 'general',
                        'content': ai_result['content']
                    }
                    summarized_emails.append(email_data)
                else:
                    # Important event email
                    event_start = datetime.strptime(ai_result['content']['event_start'], "%Y-%m-%d %H:%M")
                    
                    # Check calendar for existing events on that date
                    calendar_events = fetch_calendar(credentials, event_start, timezone)
                    
                    # Get email IDs from calendar events
                    calendar_email_ids = set()
                    if calendar_events:
                        for cal_event in calendar_events:
                            cal_email_id = get_email_id_cal(cal_event)
                            if cal_email_id:
                                calendar_email_ids.add(cal_email_id)
                    
                    # Combine calendar email IDs with ignored email IDs
                    all_excluded_ids = calendar_email_ids.union(ignored_email_ids)
                    
                    # If email ID is not in excluded list, add to pending events
                    if email['id'] not in all_excluded_ids:
                        event_data = {
                            'id': str(uuid.uuid4()),
                            'email_id': email['id'],
                            'sender': email['sender'],
                            'subject': email.get('subject', ''),
                            'category': 'event',
                            'content': ai_result['content']
                        }
                        pending_events.append(event_data)
            
            # If not important, skip (continue)
        
        return {
            'summarized_emails': summarized_emails,
            'pending_events': pending_events,
            'total_emails_processed': len(emails)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing emails: {str(e)}")
    
@app.post("/add-to-calendar/{email_id}")
def add_to_calendar(email_id: str, current_user_id: int = Depends(verify_token)):
    """Add event to Google Calendar"""
    try:
        # Get Google credentials
        credentials = get_google_credentials(current_user_id)
        if not credentials:
            raise HTTPException(status_code=400, detail="Google account not connected")
        
        # Re-fetch and process emails to find the specific event
        emails = fetch_emails(credentials, 50)  # Fetch more to ensure we find the email
        timezone = get_calendar_timezone(credentials)
        
        event_to_add = None
        for email in emails:
            if email['id'] == email_id:
                ai_result = categorize_and_summarize_email(email['text'])
                if ai_result and ai_result['importance'] and ai_result['category'] == 'event':
                    event_to_add = ai_result['content']
                    break
        
        if not event_to_add:
            raise HTTPException(status_code=404, detail="Event not found or not processable")
        
        # Add to calendar
        calendar_event = add_cal_event(credentials, email_id, event_to_add, timezone)
        
        return {
            'message': 'Event added to calendar successfully',
            'calendar_link': calendar_event.get('htmlLink'),
            'event_id': calendar_event.get('id')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding event to calendar: {str(e)}")

@app.delete("/ignore-event/{email_id}")
def ignore_event(email_id: str, current_user_id: int = Depends(verify_token)):
    """Add email to ignored events list"""
    try:
        add_ignored_event(current_user_id, email_id)
        return {'message': 'Event ignored successfully'}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ignoring event: {str(e)}")

@app.get("/dashboard-data")
def get_dashboard_data(current_user_id: int = Depends(verify_token)):
    """Get current dashboard data by re-processing emails"""
    try:
        # Get Google credentials
        credentials = get_google_credentials(current_user_id)
        if not credentials:
            return {
                'summarized_emails': [],
                'pending_events': [],
                'google_connected': False
            }
        
        # Use the same logic as fetch-emails but with default count
        request = EmailFetchRequest(email_count=10)
        result = fetch_and_process_emails(request, current_user_id)
        result['google_connected'] = True
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")

@app.get("/ignored-events")
def get_ignored_events(current_user_id: int = Depends(verify_token)):
    """Get list of ignored events for user"""
    try:
        ignored_ids = get_ignored_event_ids(current_user_id)
        return {'ignored_event_ids': list(ignored_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting ignored events: {str(e)}")

@app.delete("/ignored-events/{email_id}")
def remove_ignored_event(email_id: str, current_user_id: int = Depends(verify_token)):
    """Remove email from ignored events list"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM ignored_events 
                WHERE user_id = ? AND email_id = ?
            """, (current_user_id, email_id))
            conn.commit()
        
        return {'message': 'Event removed from ignored list'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing ignored event: {str(e)}")
    
@app.get("/user/profile")
def get_user_profile(current_user_id: int = Depends(verify_token)):
    """Get user profile information"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.username, u.email, u.created_at, gc.google_email
                FROM users u 
                LEFT JOIN google_credentials gc ON u.id = gc.user_id
                WHERE u.id = ?
            """, (current_user_id,))
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at'],
                'google_email': user['google_email'],
                'google_connected': user['google_email'] is not None
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user profile: {str(e)}")
    

@app.delete("/auth/google/unlink")
def unlink_google_account(current_user_id: int = Depends(verify_token)):
    """Unlink Google account from user"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM google_credentials 
                WHERE user_id = ?
            """, (current_user_id,))
            conn.commit()
        
        return {'message': 'Google account unlinked successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking Google account: {str(e)}")

if __name__ == "__main__":
    with get_db_connection() as conn:

        cursor = conn.cursor()

        hashed_pwd = get_password_hash("admin")
        cursor.execute("INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",("admin","admin@gmail.com",hashed_pwd))

        conn.commit()

