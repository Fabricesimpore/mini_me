"""Real Gmail OAuth2 Integration"""
import os
import json
import base64
from typing import Optional, List, Dict
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

class GmailOAuth:
    """Handle Gmail OAuth2 authentication and API operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.compose',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/api/gmail/callback"],
                "javascript_origins": ["http://localhost:3000", "http://localhost:5173"]
            }
        }
        self.credentials_store = {}  # In production, use database
        
    def get_auth_url(self, user_id: str) -> str:
        """Generate OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8000/api/gmail/callback"
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=user_id  # Pass user_id in state
        )
        
        # Store flow for callback
        self.credentials_store[user_id] = {
            'flow': flow,
            'state': state
        }
        
        return auth_url
    
    def handle_callback(self, code: str, state: str) -> Credentials:
        """Handle OAuth2 callback"""
        user_id = state  # We passed user_id as state
        
        if user_id not in self.credentials_store:
            raise ValueError("Invalid state")
        
        flow = self.credentials_store[user_id]['flow']
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Store credentials (in production, encrypt and save to database)
        self.credentials_store[user_id] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        return credentials
    
    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get stored credentials for user"""
        if user_id not in self.credentials_store:
            return None
        
        creds_data = self.credentials_store[user_id]
        if 'token' not in creds_data:
            return None
        
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Update stored credentials
            self.credentials_store[user_id]['token'] = credentials.token
            if credentials.expiry:
                self.credentials_store[user_id]['expiry'] = credentials.expiry.isoformat()
        
        return credentials
    
    def get_gmail_service(self, user_id: str):
        """Get Gmail API service instance"""
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise ValueError("No valid credentials found")
        
        return build('gmail', 'v1', credentials=credentials)
    
    def fetch_emails(self, user_id: str, query: str = '', max_results: int = 10) -> List[Dict]:
        """Fetch emails from Gmail"""
        try:
            service = self.get_gmail_service(user_id)
            
            # List messages
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                # Get full message
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                # Parse email data
                email_data = self._parse_email(message)
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _parse_email(self, message: Dict) -> Dict:
        """Parse Gmail message into structured data"""
        headers = message['payload'].get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        to_email = next((h['value'] for h in headers if h['name'] == 'To'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Extract body
        body = self._get_message_body(message['payload'])
        
        # Extract labels
        labels = message.get('labelIds', [])
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'subject': subject,
            'from': from_email,
            'to': to_email,
            'date': date,
            'body': body[:500],  # Truncate for preview
            'labels': labels,
            'is_unread': 'UNREAD' in labels,
            'is_important': 'IMPORTANT' in labels,
            'has_attachments': self._has_attachments(message['payload'])
        }
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract message body from payload"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='ignore')
        
        return body
    
    def _has_attachments(self, payload: Dict) -> bool:
        """Check if message has attachments"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
        return False
    
    def analyze_email_patterns(self, user_id: str) -> Dict:
        """Analyze user's email patterns"""
        emails = self.fetch_emails(user_id, max_results=100)
        
        # Analyze patterns
        senders = {}
        subjects = []
        hourly_distribution = [0] * 24
        
        for email in emails:
            # Count senders
            sender = email['from']
            senders[sender] = senders.get(sender, 0) + 1
            
            # Collect subjects for topic analysis
            subjects.append(email['subject'])
            
            # Time distribution
            try:
                date_str = email['date']
                # Parse date and extract hour
                # This is simplified - in production use proper date parsing
                hour = 9  # Default hour
                hourly_distribution[hour] += 1
            except:
                pass
        
        # Get top senders
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_emails': len(emails),
            'top_senders': [{'email': s[0], 'count': s[1]} for s in top_senders],
            'hourly_distribution': hourly_distribution,
            'unread_count': sum(1 for e in emails if e['is_unread']),
            'important_count': sum(1 for e in emails if e['is_important'])
        }

# Global instance
gmail_oauth = GmailOAuth()