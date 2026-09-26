"""External system integration tools: Google Calendar, GitHub, and email."""

import os
import json
import smtplib
import time
from email.message import EmailMessage
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from llm_helper import LLMHelper
from config import Config

# Google Calendar imports (optional)
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# GitHub imports (optional)
try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


class ExternalTools:
    """External system integration tools."""
    
    def __init__(self, llm_helper: LLMHelper):
        """Initialize external tools with LLM helper."""
        self.llm_helper = llm_helper
        self._google_service = None
        self._github_client = None
    
    def _get_google_calendar_service(self):
        """Get or create Google Calendar service."""
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Calendar libraries not installed")
        
        if self._google_service:
            return self._google_service
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        token_path = Path('token.json')
        creds_path = Path(Config.GOOGLE_CALENDAR_CREDENTIALS_FILE)
        
        # Load token if exists
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not creds_path.exists():
                    raise FileNotFoundError(f"Credentials file not found: {creds_path}")
                flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save token
            token_path.write_text(creds.to_json(), encoding="utf-8")
        
        self._google_service = build('calendar', 'v3', credentials=creds)
        return self._google_service
    
    def _get_github_client(self):
        """Get or create GitHub client."""
        if not GITHUB_AVAILABLE:
            raise ImportError("GitHub library not installed")
        
        if self._github_client:
            return self._github_client
        
        if not Config.GITHUB_TOKEN:
            raise ValueError("GitHub token not configured")
        
        self._github_client = Github(Config.GITHUB_TOKEN)
        return self._github_client
    
    async def google_calendar_add(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add event to Google Calendar.
        
        Args:
            summary: Event title
            start_time: Start time (ISO 8601 format or natural language)
            end_time: End time (ISO 8601 format or natural language)
            description: Event description
            location: Event location
            
        Returns:
            Result dictionary with event details
        """
        try:
            service = self._get_google_calendar_service()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initialize Google Calendar: {str(e)}"
            }
        
        # Parse times
        try:
            start_dt = self._parse_datetime(start_time)
            end_dt = self._parse_datetime(end_time)
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid datetime format: {str(e)}"
            }
        
        # Validate times
        if end_dt <= start_dt:
            return {
                "success": False,
                "error": "End time must be after start time"
            }
        
        # Request approval
        if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
            approved, reason = self.llm_helper.request_approval(
                "google_calendar_add",
                {
                    "summary": summary,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                    "description": description
                }
            )
            
            if not approved:
                return {
                    "success": False,
                    "error": f"Calendar event creation not approved: {reason}"
                }
        
        # Create event
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC'
            }
        }
        
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        
        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return {
                "success": True,
                "event_id": created_event['id'],
                "event_link": created_event.get('htmlLink'),
                "summary": summary,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create calendar event: {str(e)}"
            }
    
    async def github_create_pr(
        self,
        repo_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a GitHub Pull Request.
        
        Args:
            repo_name: Repository name (format: owner/repo)
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            
        Returns:
            Result dictionary with PR details
        """
        try:
            github = self._get_github_client()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initialize GitHub client: {str(e)}"
            }
        
        # Validate repository name
        if '/' not in repo_name:
            return {
                "success": False,
                "error": "Repository name must be in format: owner/repo"
            }
        
        # Request approval
        if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
            approved, reason = self.llm_helper.request_approval(
                "github_create_pr",
                {
                    "repo": repo_name,
                    "title": title,
                    "head": head_branch,
                    "base": base_branch,
                    "body_preview": body[:200]
                }
            )
            
            if not approved:
                return {
                    "success": False,
                    "error": f"PR creation not approved: {reason}"
                }
        
        try:
            # Get repository
            repo = github.get_repo(repo_name)
            
            # Verify branches exist
            try:
                repo.get_branch(head_branch)
                repo.get_branch(base_branch)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Branch verification failed: {str(e)}"
                }

            # Query before mutation so a retry cannot create a duplicate PR.
            # This implements the idempotency rule described immediately before
            # Experiment 4-4 in the manuscript.
            owner = repo_name.split("/", 1)[0]
            existing = repo.get_pulls(
                state="open", head=f"{owner}:{head_branch}", base=base_branch
            )
            for pr in existing:
                if pr.head.ref == head_branch and pr.base.ref == base_branch:
                    return {
                        "success": True,
                        "pr_number": pr.number,
                        "pr_url": pr.html_url,
                        "title": pr.title,
                        "state": pr.state,
                        "created_at": pr.created_at.isoformat(),
                        "idempotent_reuse": True,
                    }
            
            # Create pull request
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": title,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "idempotent_reuse": False,
            }
            
        except GithubException as e:
            return {
                "success": False,
                "error": f"GitHub API error: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create pull request: {str(e)}"
            }
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        Send an email through a configured SMTP provider.

        Sending mail is irreversible, so this follows the two-phase
        "pre-check then confirm" pattern: a reviewer model approves the
        dispatch before smtplib is allowed to touch the network.

        Args:
            to: Recipient address
            subject: Email subject
            body: Plain-text email body

        Returns:
            Result dictionary with delivery details
        """
        missing = [name for name, value in {
            "SMTP_HOST": Config.SMTP_HOST,
            "SMTP_USER": Config.SMTP_USER,
            "SMTP_PASSWORD": Config.SMTP_PASSWORD,
        }.items() if not value]
        if missing:
            return {
                "success": False,
                "credential_status": "missing_credentials",
                "error": f"Email provider credentials not configured: {', '.join(missing)}"
            }

        # Phase 1 (pre-check): LLM review before any irreversible dispatch.
        if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
            approved, reason = self.llm_helper.request_approval(
                "send_email",
                {
                    "to": to,
                    "subject": subject,
                    "body_preview": body[:200],
                    "smtp_host": Config.SMTP_HOST
                }
            )

            if not approved:
                return {
                    "success": False,
                    "error": f"Email send not approved: {reason}"
                }

        # Phase 2 (confirm): real SMTP delivery.
        message = EmailMessage()
        message["From"] = Config.EMAIL_FROM or Config.SMTP_USER
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        started = time.perf_counter()
        try:
            use_ssl = Config.SMTP_PORT == 465
            smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
            with smtp_class(Config.SMTP_HOST, Config.SMTP_PORT, timeout=30) as smtp:
                if not use_ssl:
                    smtp.starttls()
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                refused = smtp.send_message(message)
            return {
                "success": True,
                "from": message["From"],
                "to": to,
                "subject": subject,
                "smtp_host": Config.SMTP_HOST,
                "smtp_port": Config.SMTP_PORT,
                "refused_recipients": {str(key): str(value)
                                       for key, value in (refused or {}).items()},
                "latency_seconds": round(time.perf_counter() - started, 3),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"SMTP send failed: {type(e).__name__}: {str(e)}",
                "latency_seconds": round(time.perf_counter() - started, 3),
            }

    def _parse_datetime(self, time_str: str) -> datetime:
        """Parse datetime string in various formats."""
        # Try ISO 8601 format first
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # If no format works, raise error
        raise ValueError(f"Could not parse datetime: {time_str}")
