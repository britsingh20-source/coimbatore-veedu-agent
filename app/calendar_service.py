"""Google Calendar Integration for Coimbatoreveedubuilders site visits."""
import os, logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = os.getenv("CALENDAR_TIMEZONE", "Asia/Kolkata")
CAL_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
DURATION = int(os.getenv("APPOINTMENT_DURATION", "60"))
CREDS_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/app/credentials/service_account.json")

class CalendarService:
    def _get_service(self):
        if not Path(CREDS_FILE).exists():
            raise FileNotFoundError(f"Service account not found at {CREDS_FILE}")
        creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        return build("calendar", "v3", credentials=creds)

    def _to_dt(self, date_str, time_str):
        tz = ZoneInfo(TIMEZONE)
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    async def book_appointment(self, name, date, time, phone="", notes=""):
        service = self._get_service()
        start_dt = self._to_dt(date, time)
        end_dt = start_dt + timedelta(minutes=DURATION)
        readable = start_dt.strftime("%I:%M %p, %A %d %B %Y")
        event = {"summary": f"Site Visit - {name}",
            "description": f"Customer: {name}\nPhone: {phone}\n{notes}\nBooked via Telecalling Agent\nTime: {readable}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE}, "colorId": "2",
            "reminders": {"useDefault": False, "overrides": [{"method":"popup","minutes":60},{"method":"popup","minutes":15}]}}
        try:
            created = service.events().insert(calendarId=CAL_ID, body=event).execute()
            logger.info(f"Event created: {created['id']} for {name}")
            return {"event_id": created["id"], "event_link": created.get("htmlLink",""), "start_time": readable, "name": name}
        except HttpError as e:
            raise RuntimeError(f"Calendar booking failed: {e}")