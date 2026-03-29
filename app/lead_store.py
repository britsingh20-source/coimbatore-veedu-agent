"""Lead Storage - saves call leads to JSON file."""
import json, logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DATA_DIR = Path("/app/data")
LEADS_FILE = DATA_DIR / "leads.json"

def save_lead(session: dict, status: str = "unknown"):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        leads = json.loads(LEADS_FILE.read_text()) if LEADS_FILE.exists() else []
        lead = {"id": len(leads)+1, "call_sid": session.get("call_sid"), "phone": session.get("phone"),
            "name": session.get("name"), "property_type": session.get("property_type"),
            "location": session.get("location"), "budget": session.get("budget"),
            "visit_date": session.get("date"), "visit_time": session.get("time"),
            "booking_id": session.get("booking_id"), "status": status,
            "call_turns": session.get("turns", 0), "captured_at": datetime.now().isoformat()}
        leads.append(lead)
        LEADS_FILE.write_text(json.dumps(leads, indent=2, ensure_ascii=False))
        logger.info(f"Lead saved: {lead['name']} | {lead['phone']} | {status}")
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")