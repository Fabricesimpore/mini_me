import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode
import hashlib
import secrets

class TodoistService:
    """Service for interacting with Todoist API"""
    
    API_BASE_URL = "https://api.todoist.com/rest/v2"
    OAUTH_BASE_URL = "https://todoist.com/oauth"
    
    def __init__(self):
        self.client_id = os.getenv('TODOIST_CLIENT_ID')
        self.client_secret = os.getenv('TODOIST_CLIENT_SECRET')
        self.access_token = None
    
    def get_authorization_url(self, state: str) -> str:
        """Get OAuth2 authorization URL for Todoist"""
        params = {
            'client_id': self.client_id,
            'scope': 'data:read',
            'state': state,
            'redirect_uri': 'http://localhost:8000/api/todoist/oauth-callback'
        }
        
        return f"{self.OAUTH_BASE_URL}/authorize?{urlencode(params)}"
    
    def handle_oauth_callback(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': 'http://localhost:8000/api/todoist/oauth-callback'
        }
        
        response = requests.post(f"{self.OAUTH_BASE_URL}/access_token", data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        
        # Get user info
        user_info = self._make_request('GET', '/sync/v9/user')
        
        return {
            'access_token': token_data['access_token'],
            'user_email': user_info.get('email', 'Unknown')
        }
    
    def set_access_token(self, token: str):
        """Set access token for API requests"""
        self.access_token = token
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Todoist API"""
        if not self.access_token:
            raise ValueError("No access token available")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.API_BASE_URL}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=data)
        else:
            response = requests.request(method, url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json()
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        return self._make_request('GET', '/projects')
    
    def get_tasks(self, filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks with optional filter"""
        params = {}
        if filter:
            params['filter'] = filter
        
        return self._make_request('GET', '/tasks', params)
    
    def get_completed_tasks(self, since: Optional[datetime] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """Get completed tasks"""
        params = {
            'limit': limit
        }
        
        if since:
            params['since'] = since.isoformat()
        
        # Todoist API v2 doesn't have direct completed tasks endpoint
        # We'll use the activity/events endpoint instead
        events = self._make_request('GET', '/activity/events', params)
        
        completed_tasks = []
        for event in events:
            if event.get('object_type') == 'item' and event.get('event_type') == 'completed':
                completed_tasks.append(event)
        
        return completed_tasks
    
    def analyze_task_patterns(self) -> Dict[str, Any]:
        """Analyze user's task management patterns"""
        try:
            # Get all projects
            projects = self.get_projects()
            
            # Get active tasks
            active_tasks = self.get_tasks()
            
            # Get completed tasks from last 30 days
            since = datetime.now() - timedelta(days=30)
            completed_events = self.get_completed_tasks(since=since)
            
            analysis = {
                "projects_count": len(projects),
                "active_tasks_count": len(active_tasks),
                "completed_tasks_30d": len(completed_events),
                "task_patterns": self._analyze_task_patterns(active_tasks, completed_events),
                "project_distribution": self._analyze_project_distribution(active_tasks, projects),
                "productivity_insights": self._analyze_productivity(completed_events),
                "priority_usage": self._analyze_priority_usage(active_tasks)
            }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing tasks: {str(e)}")
    
    def _analyze_task_patterns(self, active_tasks: List[Dict], completed_events: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in task creation and completion"""
        # Task creation patterns
        due_dates_count = sum(1 for task in active_tasks if task.get('due'))
        
        # Overdue analysis
        overdue_count = 0
        upcoming_count = 0
        
        for task in active_tasks:
            if task.get('due'):
                due_date = datetime.fromisoformat(task['due']['date'].replace('Z', '+00:00'))
                if due_date < datetime.now():
                    overdue_count += 1
                elif due_date < datetime.now() + timedelta(days=7):
                    upcoming_count += 1
        
        # Completion time analysis
        completion_times = {}
        for event in completed_events:
            event_time = datetime.fromisoformat(event['event_date'].replace('Z', '+00:00'))
            hour = event_time.hour
            completion_times[hour] = completion_times.get(hour, 0) + 1
        
        # Find peak productivity hours
        peak_hours = sorted(completion_times.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "tasks_with_due_dates_percentage": (due_dates_count / len(active_tasks) * 100) if active_tasks else 0,
            "overdue_tasks": overdue_count,
            "upcoming_week_tasks": upcoming_count,
            "peak_productivity_hours": [{"hour": h, "completions": c} for h, c in peak_hours],
            "average_daily_completions": len(completed_events) / 30 if completed_events else 0
        }
    
    def _analyze_project_distribution(self, tasks: List[Dict], projects: List[Dict]) -> Dict[str, Any]:
        """Analyze how tasks are distributed across projects"""
        project_map = {p['id']: p['name'] for p in projects}
        project_task_count = {}
        inbox_count = 0
        
        for task in tasks:
            project_id = task.get('project_id')
            if project_id:
                project_name = project_map.get(project_id, 'Unknown')
                project_task_count[project_name] = project_task_count.get(project_name, 0) + 1
            else:
                inbox_count += 1
        
        # Sort projects by task count
        top_projects = sorted(project_task_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "inbox_tasks": inbox_count,
            "project_count": len(projects),
            "top_projects": [{"name": name, "tasks": count} for name, count in top_projects],
            "uses_projects": len(project_task_count) > 0
        }
    
    def _analyze_productivity(self, completed_events: List[Dict]) -> Dict[str, Any]:
        """Analyze productivity patterns"""
        if not completed_events:
            return {
                "daily_average": 0,
                "weekly_pattern": {},
                "completion_streak": 0
            }
        
        # Group completions by date
        daily_completions = {}
        for event in completed_events:
            event_date = datetime.fromisoformat(event['event_date'].replace('Z', '+00:00')).date()
            daily_completions[event_date] = daily_completions.get(event_date, 0) + 1
        
        # Weekly pattern
        weekly_pattern = {}
        for date, count in daily_completions.items():
            day_name = date.strftime('%A')
            if day_name not in weekly_pattern:
                weekly_pattern[day_name] = []
            weekly_pattern[day_name].append(count)
        
        # Calculate averages
        weekly_averages = {}
        for day, counts in weekly_pattern.items():
            weekly_averages[day] = sum(counts) / len(counts)
        
        # Find current streak
        today = datetime.now().date()
        streak = 0
        current_date = today
        
        while current_date in daily_completions and daily_completions[current_date] > 0:
            streak += 1
            current_date -= timedelta(days=1)
        
        return {
            "daily_average": sum(daily_completions.values()) / len(daily_completions),
            "weekly_pattern": weekly_averages,
            "completion_streak": streak,
            "most_productive_day": max(weekly_averages.items(), key=lambda x: x[1])[0] if weekly_averages else None
        }
    
    def _analyze_priority_usage(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Analyze how priorities are used"""
        priority_count = {1: 0, 2: 0, 3: 0, 4: 0}
        
        for task in tasks:
            priority = task.get('priority', 1)
            priority_count[priority] = priority_count.get(priority, 0) + 1
        
        total_tasks = len(tasks)
        
        return {
            "high_priority": priority_count.get(4, 0),
            "medium_priority": priority_count.get(3, 0) + priority_count.get(2, 0),
            "low_priority": priority_count.get(1, 0),
            "uses_priorities": any(task.get('priority', 1) > 1 for task in tasks),
            "priority_distribution": {
                f"p{p}": (count / total_tasks * 100) if total_tasks > 0 else 0
                for p, count in priority_count.items()
            }
        }
    
    def get_task_stats(self) -> Dict[str, Any]:
        """Get basic task statistics"""
        try:
            active_tasks = self.get_tasks()
            projects = self.get_projects()
            
            # Count tasks by status
            today_count = len(self.get_tasks(filter='today'))
            overdue_count = len(self.get_tasks(filter='overdue'))
            
            return {
                "total_active_tasks": len(active_tasks),
                "today_tasks": today_count,
                "overdue_tasks": overdue_count,
                "total_projects": len(projects)
            }
        except Exception as e:
            raise Exception(f"Error getting task stats: {str(e)}")