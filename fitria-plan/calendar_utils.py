from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
import uuid

def make_ics_event(summary: str, description: str, start_dt: datetime, duration_minutes: int = 60, location: str = "", tz: str = "Asia/Jakarta") -> bytes:
    tzinfo = pytz.timezone(tz)
    start_local = tzinfo.localize(start_dt)
    end_local = start_local + timedelta(minutes=duration_minutes)

    cal = Calendar()
    cal.add('prodid', '-//Content Reminder//streamlit//')
    cal.add('version', '2.0')

    event = Event()
    event.add('uid', str(uuid.uuid4()))
    event.add('summary', summary)
    if description:
        event.add('description', description)
    if location:
        event.add('location', location)
    event.add('dtstart', start_local)
    event.add('dtend', end_local)

    cal.add_component(event)
    return cal.to_ical()