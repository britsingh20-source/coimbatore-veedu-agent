"""Coimbatoreveedubuilders - Real Estate Telecalling AI Agent"""
import os, json, logging
from datetime import datetime
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a friendly real estate assistant for Coimbatoreveedubuilders, a leading property developer in Coimbatore, Tamil Nadu.
Today is {current_date} ({current_day}).
Your job is to collect: 1) CALLER NAME 2) PROPERTY TYPE (flat/villa/plot/commercial) 3) LOCATION PREFERENCE (area in Coimbatore) 4) BUDGET RANGE (in lakhs/crores) 5) SITE VISIT DATE (within 30 days) 6) TIME SLOT (morning 9AM-12PM / afternoon 12PM-4PM / evening 4PM-7PM)
RULES: Keep responses to 1-2 sentences. Available days: Mon-Sat. Use Tamil-friendly English (Anna/Madam). For price questions say "Our team will share details when you visit, sir/madam."
Respond ONLY with raw JSON: {{"message":"...","extracted":{{"name":null,"property_type":null,"location":null,"budget":null,"visit_date":null,"time_slot":null,"time_exact":null}},"action":"gather"or"book"or"hangup","missing":[]}}"""

class ConversationAgent:
    async def process(self, session, speech_input):
        system = SYSTEM_PROMPT.format(current_date=datetime.now().strftime("%Y-%m-%d"), current_day=datetime.now().strftime("%A"))
        state = f"\nState: name={session.get('name') or '?'} | type={session.get('property_type') or '?'} | loc={session.get('location') or '?'} | budget={session.get('budget') or '?'} | date={session.get('date') or '?'} | time={session.get('time') or '?'}"
        msg = f"[Caller]: {speech_input}\n{state}" if speech_input.strip() else f"[Silent]\n{state}"
        session["history"].append({"role": "user", "content": msg})
        try:
            resp = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=500, system=system, messages=session["history"][-12:])
            result = json.loads(resp.content[0].text.strip())
        except Exception as e:
            logger.error(f"AI error: {e}")
            result = {"message": "Sorry, could you repeat that?", "extracted": {}, "action": "gather", "missing": []}
        ex = result.get("extracted", {})
        if ex.get("name"): session["name"] = ex["name"]
        if ex.get("property_type"): session["property_type"] = ex["property_type"]
        if ex.get("location"): session["location"] = ex["location"]
        if ex.get("budget"): session["budget"] = ex["budget"]
        if ex.get("visit_date"): session["date"] = ex["visit_date"]
        if ex.get("time_exact"): session["time"] = ex["time_exact"]
        elif ex.get("time_slot"): session["time"] = {"morning":"10:00","afternoon":"13:00","evening":"16:00"}.get(ex["time_slot"],"10:00")
        session["history"].append({"role": "assistant", "content": result["message"]})
        required = ["name","property_type","location","budget","date","time"]
        if result["action"] == "book" and not all(session.get(f) for f in required):
            result["action"] = "gather"
        return {"session": session, "message": result["message"], "action": result["action"]}