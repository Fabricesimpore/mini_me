"""Real Google Calendar OAuth2 Integration"""
import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class CalendarOAuth:
    """Handle Google Calendar OAuth2 authentication and API operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/api/calendar/callback"],
                "javascript_origins": ["http://localhost:3000", "http://localhost:5173"]
            }
        }
        self.credentials_store = {}  # In production, use database
        
    def get_auth_url(self, user_id: str) -> str:
        """Generate OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8000/api/calendar/callback"
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
    
    def get_calendar_service(self, user_id: str):
        """Get Calendar API service instance"""
        credentials = self.get_credentials(user_id)
        if not credentials:
            raise ValueError("No valid credentials found")
        
        return build('calendar', 'v3', credentials=credentials)
    
    def fetch_events(self, user_id: str, time_min: datetime = None, time_max: datetime = None, max_results: int = 10) -> List[Dict]:
        """Fetch calendar events"""
        try:
            service = self.get_calendar_service(user_id)
            
            # Default to next 7 days if not specified
            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = time_min + timedelta(days=7)
            
            # Format times for API
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'
            
            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Parse events
            parsed_events = []
            for event in events:
                parsed_events.append(self._parse_event(event))
            
            return parsed_events
            
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            return []
    
    def _parse_event(self, event: Dict) -> Dict:
        """Parse calendar event into structured data"""
        # Get start and end times
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Handle all-day vs timed events
        if 'dateTime' in start:
            start_time = start['dateTime']
            end_time = end['dateTime']
            all_day = False
        else:
            start_time = start.get('date', '')
            end_time = end.get('date', '')
            all_day = True
        
        # Extract attendees
        attendees = []
        for attendee in event.get('attendees', []):
            attendees.append({
                'email': attendee.get('email', ''),
                'response': attendee.get('responseStatus', 'needsAction'),
                'organizer': attendee.get('organizer', False)
            })
        
        return {
            'id': event['id'],
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start': start_time,
            'end': end_time,
            'all_day': all_day,
            'status': event.get('status', 'confirmed'),
            'html_link': event.get('htmlLink', ''),
            'attendees': attendees,
            'organizer': event.get('organizer', {}).get('email', ''),
            'recurring': bool(event.get('recurringEventId')),
            'meeting_type': self._determine_meeting_type(event)
        }
    
    def _determine_meeting_type(self, event: Dict) -> str:
        """Determine the type of meeting"""
        summary = event.get('summary', '').lower()
        description = event.get('description', '').lower()
        attendee_count = len(event.get('attendees', []))
        
        # Check for common meeting types
        if any(word in summary for word in ['standup', 'daily', 'scrum']):
            return 'standup'
        elif any(word in summary for word in ['1:1', 'one-on-one', '1-1']):
            return 'one-on-one'
        elif any(word in summary for word in ['interview', 'screening']):
            return 'interview'
        elif any(word in summary for word in ['review', 'retro', 'retrospective']):
            return 'review'
        elif attendee_count > 5:
            return 'large-meeting'
        elif attendee_count > 1:
            return 'meeting'
        else:
            return 'personal'
    
    def analyze_calendar_patterns(self, user_id: str) -> Dict:
        """Analyze user's calendar patterns"""
        # Fetch events for the past month and next month
        time_min = datetime.utcnow() - timedelta(days=30)
        time_max = datetime.utcnow() + timedelta(days=30)
        
        events = self.fetch_events(user_id, time_min, time_max, max_results=100)
        
        # Analyze patterns
        meeting_types = {}
        daily_distribution = [0] * 24
        weekday_distribution = [0] * 7
        total_duration = 0
        recurring_count = 0
        
        for event in events:
            # Count meeting types
            meeting_type = event['meeting_type']
            meeting_types[meeting_type] = meeting_types.get(meeting_type, 0) + 1
            
            # Count recurring events
            if event['recurring']:
                recurring_count += 1
            
            # Time analysis (simplified - would need proper timezone handling)
            try:
                if not event['all_day'] and 'T' in event['start']:
                    hour = int(event['start'].split('T')[1].split(':')[0])
                    daily_distribution[hour] += 1
                    
                    # Weekday (simplified)
                    weekday = datetime.fromisoformat(event['start'].replace('Z', '+00:00')).weekday()
                    weekday_distribution[weekday] += 1
            except:
                pass
        
        # Find busiest hours
        busiest_hours = sorted(enumerate(daily_distribution), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate insights
        insights = []
        if busiest_hours[0][1] > 0:
            insights.append(f"Your busiest meeting hours are around {busiest_hours[0][0]}:00")
        
        if meeting_types.get('meeting', 0) > 10:
            insights.append(f"You have {meeting_types.get('meeting', 0)} meetings scheduled")
        
        if recurring_count > 5:
            insights.append(f"{recurring_count} of your meetings are recurring")
        
        return {
            'total_events': len(events),
            'meeting_types': meeting_types,
            'daily_distribution': daily_distribution,
            'weekday_distribution': weekday_distribution,
            'recurring_count': recurring_count,
            'insights': insights,
            'busiest_hours': [h[0] for h in busiest_hours[:3]]
        }

# Global instance
calendar_oauth = CalendarOAuth()