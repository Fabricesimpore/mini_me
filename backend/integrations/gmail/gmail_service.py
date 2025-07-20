import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GmailService:
    """Service for Gmail integration and email analysis"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials_path = f"credentials/gmail_{user_id}_token.json"
        self.service = None
        
    def get_auth_url(self, redirect_uri: str) -> str:
        """Get OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        
        flow.redirect_uri = redirect_uri
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def handle_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and save credentials"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Save credentials
        os.makedirs("credentials", exist_ok=True)
        with open(self.credentials_path, 'w') as token:
            token.write(credentials.to_json())
        
        # Initialize service
        self._initialize_service(credentials)
        
        # Get user profile
        profile = self._get_user_profile()
        
        return {
            "status": "success",
            "email": profile.get("emailAddress"),
            "profile": profile
        }
    
    def _initialize_service(self, credentials: Optional[Credentials] = None):
        """Initialize Gmail API service"""
        if not credentials:
            if os.path.exists(self.credentials_path):
                credentials = Credentials.from_authorized_user_file(self.credentials_path, self.SCOPES)
            else:
                raise ValueError("No credentials available")
        
        # Refresh if needed
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save refreshed credentials
            with open(self.credentials_path, 'w') as token:
                token.write(credentials.to_json())
        
        self.service = build('gmail', 'v1', credentials=credentials)
    
    def _get_user_profile(self) -> Dict[str, Any]:
        """Get Gmail user profile"""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile
        except HttpError as error:
            logger.error(f"Error getting profile: {error}")
            return {}
    
    def analyze_sent_emails(self, max_results: int = 100) -> Dict[str, Any]:
        """Analyze sent emails for communication patterns"""
        if not self.service:
            self._initialize_service()
        
        try:
            # Get sent emails
            results = self.service.users().messages().list(
                userId='me',
                q='in:sent',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            analysis = {
                "total_analyzed": len(messages),
                "communication_patterns": {},
                "writing_style": {},
                "relationships": {},
                "response_patterns": {}
            }
            
            for msg_info in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_info['id']
                ).execute()
                
                # Analyze message
                self._analyze_message(msg, analysis)
            
            # Process patterns
            analysis = self._process_communication_patterns(analysis)
            
            return analysis
            
        except HttpError as error:
            logger.error(f"Error analyzing emails: {error}")
            return {"error": str(error)}
    
    def _analyze_message(self, msg: Dict[str, Any], analysis: Dict[str, Any]):
        """Analyze individual email message"""
        headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
        
        # Extract metadata
        to_email = headers.get('To', '')
        subject = headers.get('Subject', '')
        date_str = headers.get('Date', '')
        
        # Get message body
        body = self._extract_body(msg['payload'])
        
        if not body:
            return
        
        # Analyze communication style
        self._analyze_writing_style(body, analysis['writing_style'])
        
        # Track relationships
        if to_email:
            self._track_relationship(to_email, analysis['relationships'])
        
        # Analyze response time if it's a reply
        if 'Re:' in subject or 'RE:' in subject:
            self._analyze_response_time(msg, analysis['response_patterns'])
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        return body
    
    def _analyze_writing_style(self, body: str, style_analysis: Dict[str, Any]):
        """Analyze writing style from email body"""
        # Word count
        words = body.split()
        word_count = len(words)
        
        # Sentence analysis
        sentences = body.split('.')
        avg_sentence_length = word_count / max(len(sentences), 1)
        
        # Greeting patterns
        greetings = ['hi', 'hello', 'dear', 'hey', 'good morning', 'good afternoon']
        used_greeting = None
        for greeting in greetings:
            if body.lower().startswith(greeting):
                used_greeting = greeting
                break
        
        # Closing patterns
        closings = ['regards', 'best', 'sincerely', 'thanks', 'cheers', 'yours']
        used_closing = None
        body_lower = body.lower()
        for closing in closings:
            if closing in body_lower[-100:]:  # Check last 100 chars
                used_closing = closing
                break
        
        # Update analysis
        if 'word_counts' not in style_analysis:
            style_analysis['word_counts'] = []
        style_analysis['word_counts'].append(word_count)
        
        if 'sentence_lengths' not in style_analysis:
            style_analysis['sentence_lengths'] = []
        style_analysis['sentence_lengths'].append(avg_sentence_length)
        
        if used_greeting:
            if 'greetings' not in style_analysis:
                style_analysis['greetings'] = {}
            style_analysis['greetings'][used_greeting] = style_analysis['greetings'].get(used_greeting, 0) + 1
        
        if used_closing:
            if 'closings' not in style_analysis:
                style_analysis['closings'] = {}
            style_analysis['closings'][used_closing] = style_analysis['closings'].get(used_closing, 0) + 1
    
    def _track_relationship(self, email: str, relationships: Dict[str, Any]):
        """Track email relationships"""
        # Extract domain
        domain = email.split('@')[-1] if '@' in email else 'unknown'
        
        # Track frequency
        if email not in relationships:
            relationships[email] = {
                'count': 0,
                'domain': domain,
                'type': 'personal' if domain in ['gmail.com', 'yahoo.com', 'hotmail.com'] else 'professional'
            }
        
        relationships[email]['count'] += 1
    
    def _analyze_response_time(self, msg: Dict[str, Any], response_patterns: Dict[str, Any]):
        """Analyze email response times"""
        # This would require matching with received emails
        # For now, we'll track that it's a response
        if 'responses' not in response_patterns:
            response_patterns['responses'] = 0
        response_patterns['responses'] += 1
    
    def _process_communication_patterns(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Process and summarize communication patterns"""
        # Calculate averages for writing style
        if analysis['writing_style'].get('word_counts'):
            analysis['writing_style']['avg_word_count'] = sum(analysis['writing_style']['word_counts']) / len(analysis['writing_style']['word_counts'])
        
        if analysis['writing_style'].get('sentence_lengths'):
            analysis['writing_style']['avg_sentence_length'] = sum(analysis['writing_style']['sentence_lengths']) / len(analysis['writing_style']['sentence_lengths'])
        
        # Find most common greeting and closing
        if analysis['writing_style'].get('greetings'):
            analysis['writing_style']['preferred_greeting'] = max(
                analysis['writing_style']['greetings'].items(),
                key=lambda x: x[1]
            )[0]
        
        if analysis['writing_style'].get('closings'):
            analysis['writing_style']['preferred_closing'] = max(
                analysis['writing_style']['closings'].items(),
                key=lambda x: x[1]
            )[0]
        
        # Sort relationships by frequency
        if analysis['relationships']:
            analysis['top_contacts'] = sorted(
                [(email, data) for email, data in analysis['relationships'].items()],
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
        
        return analysis
    
    def get_email_templates(self) -> List[Dict[str, Any]]:
        """Extract common email templates/patterns"""
        if not self.service:
            self._initialize_service()
        
        try:
            # Get sent emails
            results = self.service.users().messages().list(
                userId='me',
                q='in:sent',
                maxResults=50
            ).execute()
            
            messages = results.get('messages', [])
            templates = []
            
            # Group by subject patterns
            subject_groups = {}
            
            for msg_info in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_info['id']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
                subject = headers.get('Subject', '')
                
                # Remove Re: and similar prefixes
                clean_subject = subject.replace('Re:', '').replace('RE:', '').replace('Fwd:', '').strip()
                
                # Group similar subjects
                if clean_subject:
                    if clean_subject not in subject_groups:
                        subject_groups[clean_subject] = []
                    
                    body = self._extract_body(msg['payload'])
                    if body:
                        subject_groups[clean_subject].append(body)
            
            # Find common patterns in grouped emails
            for subject, bodies in subject_groups.items():
                if len(bodies) >= 2:  # At least 2 similar emails
                    # Find common phrases
                    common_phrases = self._find_common_phrases(bodies)
                    if common_phrases:
                        templates.append({
                            'subject_pattern': subject,
                            'frequency': len(bodies),
                            'common_phrases': common_phrases,
                            'sample': bodies[0][:200] + '...' if len(bodies[0]) > 200 else bodies[0]
                        })
            
            return templates
            
        except HttpError as error:
            logger.error(f"Error getting templates: {error}")
            return []
    
    def _find_common_phrases(self, texts: List[str]) -> List[str]:
        """Find common phrases across multiple texts"""
        # Simple implementation - find sentences that appear in multiple emails
        common_phrases = []
        
        # Split into sentences
        all_sentences = []
        for text in texts:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            all_sentences.extend(sentences)
        
        # Count occurrences
        sentence_counts = {}
        for sentence in all_sentences:
            if len(sentence) > 10:  # Ignore very short sentences
                sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
        
        # Find sentences that appear multiple times
        for sentence, count in sentence_counts.items():
            if count >= len(texts) / 2:  # Appears in at least half of the texts
                common_phrases.append(sentence)
        
        return common_phrases[:5]  # Return top 5
    
    def draft_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a draft email using learned patterns"""
        if not self.service:
            self._initialize_service()
        
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return {
                "status": "success",
                "draft_id": draft['id'],
                "message": "Draft created successfully"
            }
            
        except HttpError as error:
            logger.error(f"Error creating draft: {error}")
            return {"status": "error", "message": str(error)}