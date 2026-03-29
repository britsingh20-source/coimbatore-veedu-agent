"""
Coimbatoreveedubuilders - Real Estate Telecalling Agent
FastAPI app that handles Twilio voice webhooks.
"""
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import os, json, logging
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from agent import ConversationAgent
from calendar_service import CalendarService
from lead_store import save_lead

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
app = FastAPI(title="Coimbatoreveedubuilders Telecalling Agent", version="1.0.0")
sessions: dict = {}
VOICE    = os.getenv("TWILIO_VOICE", "Polly.Aditi")
LANGUAGE = os.getenv("TWILIO_LANGUAGE", "en-IN")
BUSINESS = "Coimbatoreveedubuilders"

@app.get("/")
async def health():
    return {"status": "running", "agent": BUSINESS}

@app.post("/twilio/incoming")
async def incoming_call(CallSid: str = Form(...), From: str = Form(default="Unknown")):
    logger.info(f"Incoming call: {CallSid} from {From}")
    sessions[CallSid] = {"call_sid": CallSid, "phone": From, "history": [], "name": None,
        "property_type": None, "location": None, "budget": None, "date": None,
        "time": None, "status": "active", "turns": 0, "started_at": datetime.now().isoformat()}
    response = VoiceResponse()
    gather = Gather(input="speech", action=f"/twilio/gather?sid={CallSid}", method="POST",
        speech_timeout="auto", language=LANGUAGE, timeout=6)
    gather.say(f"Hello! Welcome to {BUSINESS}. I am your property assistant. "
        "Please tell me your name and what kind of property you are looking for.", voice=VOICE)
    response.append(gather)
    response.say("I didn't hear you. Please call back. Goodbye!", voice=VOICE)
    response.hangup()
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/gather")
async def gather_speech(CallSid: str = Form(...), SpeechResult: str = Form(default=""), sid: str = None):
    call_sid = sid or CallSid
    logger.info(f"Speech | SID={call_sid} | '{SpeechResult}'")
    session = sessions.get(call_sid, {"call_sid": call_sid, "phone": "Unknown", "history": [],
        "name": None, "property_type": None, "location": None, "budget": None,
        "date": None, "time": None, "status": "active", "turns": 0, "started_at": datetime.now().isoformat()})
    sessions[call_sid] = session
    session["turns"] = session.get("turns", 0) + 1
    if session["turns"] > 10:
        response = VoiceResponse()
        response.say("Our team will call you back shortly. Goodbye!", voice=VOICE)
        response.hangup()
        save_lead(session, status="max_turns_reached")
        return Response(content=str(response), media_type="application/xml")
    agent = ConversationAgent()
    result = await agent.process(session, SpeechResult)
    sessions[call_sid] = result["session"]
    response = VoiceResponse()
    if result["action"] == "book":
        try:
            calendar = CalendarService()
            booking = await calendar.book_appointment(name=result["session"]["name"],
                date=result["session"]["date"], time=result["session"]["time"],
                phone=result["session"]["phone"],
                notes=f"Type: {result['session'].get('property_type','N/A')} | Loc: {result['session'].get('location','N/A')} | Budget: {result['session'].get('budget','N/A')}")
            logger.info(f"Site visit booked: {booking}")
            result["session"]["booking_id"] = booking.get("event_id")
        except Exception as e:
            logger.error(f"Calendar error: {e}")
        save_lead(result["session"], status="booked")
        response.say(result["message"], voice=VOICE)
        response.hangup()
        sessions.pop(call_sid, None)
    elif result["action"] == "hangup":
        save_lead(result["session"], status="dropped")
        response.say(result["message"], voice=VOICE)
        response.hangup()
        sessions.pop(call_sid, None)
    else:
        gather = Gather(input="speech", action=f"/twilio/gather?sid={call_sid}", method="POST",
            speech_timeout="auto", language=LANGUAGE, timeout=6)
        gather.say(result["message"], voice=VOICE)
        response.append(gather)
        response.say("Call back anytime. Goodbye!", voice=VOICE)
        response.hangup()
    return Response(content=str(response), media_type="application/xml")

@app.post("/twilio/status")
async def call_status(CallSid: str = Form(...), CallStatus: str = Form(default="")):
    if CallStatus in ("completed", "failed", "busy", "no-answer"):
        session = sessions.pop(CallSid, None)
        if session and session.get("name"):
            save_lead(session, status=CallStatus)
    return Response(content="", status_code=204)

@app.get("/leads")
async def view_leads():
    try:
        with open("/app/data/leads.json", "r") as f:
            leads = json.load(f)
        return {"total": len(leads), "leads": leads}
    except FileNotFoundError:
        return {"total": 0, "leads": []}