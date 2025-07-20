import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

class GoogleCalendarService:
    """Service for interacting with Google Calendar API"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    def __init__(self, credentials_json: Optional[str] = None):
        self.credentials = None
        self.service = None
        self.client_config = self._load_client_config(credentials_json)
        
    def _load_client_config(self, credentials_json: Optional[str] = None) -> Dict:
        """Load OAuth2 client configuration"""
        if credentials_json:
            return json.loads(credentials_json)
        
        # Try to load from environment or file
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if client_id and client_secret:
            return {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8000/api/calendar/oauth-callback"]
                }
            }
        
        # Try to load from file
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as f:
                return json.load(f)
        
        raise ValueError("No Google OAuth2 credentials found")
    
    def get_authorization_url(self) -> str:
        """Get OAuth2 authorization URL"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8000/api/calendar/oauth-callback"
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        return auth_url
    
    def handle_oauth_callback(self, authorization_code: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and get tokens"""
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.SCOPES,
            redirect_uri="http://localhost:8000/api/calendar/oauth-callback"
        )
        
        flow.fetch_token(code=authorization_code)
        self.credentials = flow.credentials
        
        # Build service
        self.service = build('calendar', 'v3', credentials=self.credentials)
        
        # Get user info
        calendar_list = self.service.calendarList().get(calendarId='primary').execute()
        
        return {
            "email": calendar_list.get('summary', 'Unknown'),
            "access_token": self.credentials.token,
            "refresh_token": self.credentials.refresh_token,
            "token_expiry": self.credentials.expiry.isoformat() if self.credentials.expiry else None
        }
    
    def set_credentials(self, token_data: Dict[str, Any]):
        """Set credentials from stored tokens"""
        self.credentials = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=self.client_config['web']['token_uri'],
            client_id=self.client_config['web']['client_id'],
            client_secret=self.client_config['web']['client_secret'],
            scopes=self.SCOPES
        )
        
        self.service = build('calendar', 'v3', credentials=self.credentials)
    
    def get_calendar_list(self) -> List[Dict[str, Any]]:
        """Get list of user's calendars"""
        if not self.service:
            raise ValueError("Not authenticated")
        
        calendars = []
        page_token = None
        
        while True:
            calendar_list = self.service.calendarList().list(
                pageToken=page_token
            ).execute()
            
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'name': calendar['summary'],
                    'primary': calendar.get('primary', False),
                    'color': calendar.get('backgroundColor'),
                    'time_zone': calendar.get('timeZone')
                })
            
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break
        
        return calendars
    
    def get_events(self, time_min: Optional[datetime] = None, 
                   time_max: Optional[datetime] = None,
                   max_results: int = 1000,
                   calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """Get calendar events within a time range"""
        if not self.service:
            raise ValueError("Not authenticated")
        
        # Default to last 6 months if not specified
        if not time_min:
            time_min = datetime.now(pytz.UTC) - timedelta(days=180)
        if not time_max:
            time_max = datetime.now(pytz.UTC)
        
        events = []
        page_token = None
        
        while len(events) < max_results:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=min(250, max_results - len(events)),
                singleEvents=True,
                orderBy='startTime',
                pageToken=page_token
            ).execute()
            
            events.extend(events_result.get('items', []))
            
            page_token = events_result.get('nextPageToken')
            if not page_token:
                break
        
        return events[:max_results]
    
    def analyze_calendar_patterns(self, max_events: int = 1000) -> Dict[str, Any]:
        """Analyze user's calendar patterns"""
        if not self.service:
            raise ValueError("Not authenticated")
        
        events = self.get_events(max_results=max_events)
        
        analysis = {
            "events_analyzed": len(events),
            "time_patterns": self._analyze_time_patterns(events),
            "meeting_patterns": self._analyze_meeting_patterns(events),
            "work_life_balance": self._analyze_work_life_balance(events),
            "scheduling_habits": self._analyze_scheduling_habits(events),
            "event_categories": self._categorize_events(events)
        }
        
        return analysis
    
    def _analyze_time_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in calendar events"""
        hour_distribution = {}
        day_distribution = {}
        duration_stats = []
        
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Parse start time
            start_time = None
            if 'dateTime' in start:
                start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            elif 'date' in start:
                # All-day event
                continue
            
            if start_time:
                # Hour distribution
                hour = start_time.hour
                hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
                
                # Day distribution
                day = start_time.strftime('%A')
                day_distribution[day] = day_distribution.get(day, 0) + 1
                
                # Duration calculation
                if 'dateTime' in end:
                    end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                    duration = (end_time - start_time).total_seconds() / 60  # minutes
                    duration_stats.append(duration)
        
        # Find peak hours
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Find busiest days
        busiest_days = sorted(day_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "peak_hours": [{"hour": h, "count": c} for h, c in peak_hours],
            "busiest_days": [{"day": d, "count": c} for d, c in busiest_days],
            "average_duration_minutes": sum(duration_stats) / len(duration_stats) if duration_stats else 0,
            "typical_start_time": self._get_typical_time(hour_distribution) if hour_distribution else None
        }
    
    def _analyze_meeting_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze meeting patterns"""
        meeting_types = {
            "one_on_one": 0,
            "small_group": 0,
            "large_meeting": 0,
            "recurring": 0,
            "external": 0
        }
        
        attendee_frequency = {}
        location_frequency = {}
        
        for event in events:
            # Skip all-day events
            if 'date' in event.get('start', {}):
                continue
            
            attendees = event.get('attendees', [])
            num_attendees = len(attendees)
            
            # Categorize by size
            if num_attendees == 2:
                meeting_types["one_on_one"] += 1
            elif 2 < num_attendees <= 5:
                meeting_types["small_group"] += 1
            elif num_attendees > 5:
                meeting_types["large_meeting"] += 1
            
            # Check if recurring
            if event.get('recurringEventId'):
                meeting_types["recurring"] += 1
            
            # Analyze attendees
            for attendee in attendees:
                email = attendee.get('email', '')
                if email and email != event.get('creator', {}).get('email'):
                    attendee_frequency[email] = attendee_frequency.get(email, 0) + 1
                    
                    # Check if external
                    if '@' in email:
                        domain = email.split('@')[1]
                        creator_email = event.get('creator', {}).get('email', '')
                        if '@' in creator_email and domain != creator_email.split('@')[1]:
                            meeting_types["external"] += 1
                            break
            
            # Location analysis
            location = event.get('location', '')
            if location:
                location_frequency[location] = location_frequency.get(location, 0) + 1
        
        # Get top collaborators
        top_collaborators = sorted(
            attendee_frequency.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Get top locations
        top_locations = sorted(
            location_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "meeting_types": meeting_types,
            "top_collaborators": [
                {"email": email, "meetings": count} 
                for email, count in top_collaborators
            ],
            "preferred_locations": [
                {"location": loc, "count": count}
                for loc, count in top_locations
            ]
        }
    
    def _analyze_work_life_balance(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze work-life balance from calendar"""
        work_hours = 0
        personal_hours = 0
        weekend_events = 0
        evening_events = 0
        early_morning_events = 0
        
        work_keywords = ['meeting', 'call', 'sync', 'review', 'standup', 'presentation', '1:1', 'interview']
        personal_keywords = ['lunch', 'doctor', 'gym', 'personal', 'vacation', 'holiday', 'birthday']
        
        for event in events:
            # Skip all-day events for hour calculations
            if 'date' in event.get('start', {}):
                continue
            
            summary = event.get('summary', '').lower()
            start = event.get('start', {})
            
            # Calculate duration
            duration_hours = 0
            if 'dateTime' in start and 'dateTime' in event.get('end', {}):
                start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                duration_hours = (end_time - start_time).total_seconds() / 3600
                
                # Check time of day
                if start_time.hour < 8:
                    early_morning_events += 1
                elif start_time.hour >= 18:
                    evening_events += 1
                
                # Check weekend
                if start_time.weekday() >= 5:
                    weekend_events += 1
            
            # Categorize as work or personal
            is_work = any(keyword in summary for keyword in work_keywords)
            is_personal = any(keyword in summary for keyword in personal_keywords)
            
            if is_work and not is_personal:
                work_hours += duration_hours
            elif is_personal:
                personal_hours += duration_hours
            else:
                # Default to work if during work hours
                if 'dateTime' in start:
                    start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    if 9 <= start_time.hour < 17 and start_time.weekday() < 5:
                        work_hours += duration_hours
                    else:
                        personal_hours += duration_hours
        
        total_hours = work_hours + personal_hours
        
        return {
            "work_hours_percentage": (work_hours / total_hours * 100) if total_hours > 0 else 0,
            "personal_hours_percentage": (personal_hours / total_hours * 100) if total_hours > 0 else 0,
            "weekend_events": weekend_events,
            "evening_events": evening_events,
            "early_morning_events": early_morning_events,
            "work_life_balance_score": self._calculate_balance_score(
                work_hours, personal_hours, weekend_events, evening_events
            )
        }
    
    def _analyze_scheduling_habits(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze how user schedules events"""
        buffer_times = []
        back_to_back_count = 0
        advance_scheduling_days = []
        
        # Sort events by start time
        sorted_events = sorted(
            [e for e in events if 'dateTime' in e.get('start', {})],
            key=lambda x: x['start']['dateTime']
        )
        
        for i, event in enumerate(sorted_events):
            # Check when event was created vs when it occurs
            created = event.get('created')
            start = event.get('start', {}).get('dateTime')
            
            if created and start:
                created_time = datetime.fromisoformat(created.replace('Z', '+00:00'))
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                days_advance = (start_time - created_time).days
                if days_advance >= 0:
                    advance_scheduling_days.append(days_advance)
            
            # Check for back-to-back meetings
            if i < len(sorted_events) - 1:
                current_end = event.get('end', {}).get('dateTime')
                next_start = sorted_events[i + 1].get('start', {}).get('dateTime')
                
                if current_end and next_start:
                    current_end_time = datetime.fromisoformat(current_end.replace('Z', '+00:00'))
                    next_start_time = datetime.fromisoformat(next_start.replace('Z', '+00:00'))
                    
                    buffer_minutes = (next_start_time - current_end_time).total_seconds() / 60
                    
                    if 0 <= buffer_minutes <= 60:  # Within an hour
                        buffer_times.append(buffer_minutes)
                        
                        if buffer_minutes == 0:
                            back_to_back_count += 1
        
        return {
            "average_buffer_minutes": sum(buffer_times) / len(buffer_times) if buffer_times else 15,
            "back_to_back_meetings": back_to_back_count,
            "average_advance_scheduling_days": sum(advance_scheduling_days) / len(advance_scheduling_days) if advance_scheduling_days else 7,
            "prefers_buffer_time": sum(buffer_times) / len(buffer_times) > 10 if buffer_times else True
        }
    
    def _categorize_events(self, events: List[Dict]) -> Dict[str, int]:
        """Categorize events by type"""
        categories = {
            "meetings": 0,
            "focus_time": 0,
            "personal": 0,
            "recurring": 0,
            "external": 0,
            "one_on_ones": 0
        }
        
        for event in events:
            summary = event.get('summary', '').lower()
            attendees = event.get('attendees', [])
            
            # Check categories
            if any(word in summary for word in ['meeting', 'call', 'sync', 'discussion']):
                categories["meetings"] += 1
            
            if any(word in summary for word in ['focus', 'work time', 'deep work', 'coding']):
                categories["focus_time"] += 1
            
            if any(word in summary for word in ['personal', 'lunch', 'break', 'doctor']):
                categories["personal"] += 1
            
            if event.get('recurringEventId'):
                categories["recurring"] += 1
            
            if len(attendees) == 2:
                categories["one_on_ones"] += 1
            
            # Check for external attendees
            if self._has_external_attendees(event):
                categories["external"] += 1
        
        return categories
    
    def _has_external_attendees(self, event: Dict) -> bool:
        """Check if event has external attendees"""
        creator_email = event.get('creator', {}).get('email', '')
        if not creator_email or '@' not in creator_email:
            return False
        
        creator_domain = creator_email.split('@')[1]
        
        for attendee in event.get('attendees', []):
            email = attendee.get('email', '')
            if '@' in email and email.split('@')[1] != creator_domain:
                return True
        
        return False
    
    def _get_typical_time(self, hour_distribution: Dict[int, int]) -> str:
        """Get typical meeting start time"""
        if not hour_distribution:
            return "9:00 AM"
        
        # Weight by frequency
        total_weight = sum(hour_distribution.values())
        weighted_hour = sum(hour * count for hour, count in hour_distribution.items()) / total_weight
        
        hour = int(weighted_hour)
        minute = int((weighted_hour - hour) * 60)
        
        return f"{hour:02d}:{minute:02d}"
    
    def _calculate_balance_score(self, work_hours: float, personal_hours: float, 
                                weekend_events: int, evening_events: int) -> float:
        """Calculate work-life balance score (0-100)"""
        score = 100.0
        
        # Penalize for too much work
        total_hours = work_hours + personal_hours
        if total_hours > 0:
            work_ratio = work_hours / total_hours
            if work_ratio > 0.8:
                score -= (work_ratio - 0.8) * 100
        
        # Penalize for weekend work
        score -= min(weekend_events * 2, 20)
        
        # Penalize for too many evening events
        score -= min(evening_events * 1, 15)
        
        return max(0, min(100, score))