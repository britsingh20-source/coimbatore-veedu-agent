# Coimbatoreveedubuilders - Real Estate Telecalling Agent

AI-powered voice bot that automatically handles incoming calls, collects real estate lead details, and books site visits on Google Calendar.

## What it collects
- Caller name
- Property type (flat/villa/plot/commercial)
- Location preference (area in Coimbatore)
- Budget range
- Preferred site visit date and time

## Tech Stack
- FastAPI + Uvicorn
- Twilio (voice calls + TTS + STT)
- Claude AI (Anthropic) - conversation engine
- Google Calendar API - site visit booking
- Docker + EasyPanel deployment

## Quick Start
1. Copy `.env.example` to `.env` and fill in your keys
2. Add Google service account JSON to `credentials/service_account.json`
3. Deploy to EasyPanel or run: `docker-compose up -d`
4. Set Twilio webhook to: `https://your-domain.com/twilio/incoming`

## Endpoints
- `GET /` - Health check
- `POST /twilio/incoming` - Incoming call webhook
- `POST /twilio/gather` - Speech processing
- `POST /twilio/status` - Call status updates
- `GET /leads` - View all captured leads

See DEPLOY.md for full setup instructions.