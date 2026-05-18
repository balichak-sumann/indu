"""
Main FastAPI application
Initializes all routes, middleware, and WebSocket connections
"""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.utils.logger import logger
from app.websocket.manager import ConnectionManager
from app.telephony.exotel import ExotelCallSession

# Initialize settings
settings = get_settings()

# Initialize connection manager
connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    Startup: Initialize connections
    Shutdown: Clean up resources
    """
    logger.info("🚀 Starting Conversational AI Backend")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    yield
    logger.info("🛑 Shutting down Conversational AI Backend")
    await connection_manager.close_all()


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now (frontend can be anywhere)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "mode": "development" if settings.DEBUG else "production",
    }


# WebSocket endpoint for conversational AI
@app.websocket("/ws/conversation/{session_id}")
async def websocket_endpoint(websocket_connection: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time conversation
    
    Events handled:
    - start_session: Initialize conversation session
    - audio_chunk: Stream audio data
    - stop_audio: Stop audio input
    - interrupt: Interrupt AI speaking
    - ping: Keep-alive signal
    """
    try:
        origin = websocket_connection.headers.get("origin")
        host_header = websocket_connection.headers.get("host")
        logger.info(
            f"🔌 WebSocket handshake attempt: session={session_id} origin={origin} host={host_header}"
        )
        await connection_manager.connect(websocket_connection, session_id)
        logger.info(f"✅ Client connected to session: {session_id}")
        
        while True:
            # Receive message from client
            data = await websocket_connection.receive_json()
            
            # Route based on event type
            event_type = data.get("event")
            
            if event_type == "start_session":
                await connection_manager.handle_start_session(session_id, data)
            elif event_type == "audio_chunk":
                await connection_manager.handle_audio_chunk(session_id, data)
            elif event_type == "stop_audio":
                await connection_manager.handle_stop_audio(session_id)
            elif event_type == "interrupt":
                await connection_manager.handle_interrupt(session_id)
            elif event_type == "ping":
                await websocket_connection.send_json({"event": "pong"})
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {str(e)}")
        connection_manager.disconnect(session_id)


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "details": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# ============================================================
# EXOTEL TELEPHONY INTEGRATION
# ============================================================

# Store active product configs for calls (keyed by call reference)
_call_configs = {}
# Default product config (used when Exotel "Test out" connects without config_id)
_default_product_config = {}
# Pre-compiled greeting audio (PCM bytes ready to play)
_precompiled_greeting = None
_precompiled_greeting_text = None


@app.post("/api/product-config", tags=["Product"])
async def set_product_config(config: dict):
    """
    Set the product config and pre-generate the greeting audio.
    """
    global _default_product_config, _precompiled_greeting, _precompiled_greeting_text
    _default_product_config = config
    logger.info(f"📦 Product config set: {config.get('productName', 'unknown')}")
    
    # Pre-generate greeting
    try:
        from app.ai.sarvam import llm, tts
        import base64, aiohttp
        
        pc = config
        product_name = pc.get("productName", "our product")
        company_name = pc.get("companyName", "our company")
        
        language = pc.get("language", "en")
        lang_instruction = ""
        if language == "te":
            lang_instruction = "Speak FULLY in Telugu (తెలుగు script). Use proper Telugu grammar. Technical product terms can stay in English. "
        elif language == "hi":
            lang_instruction = "Speak FULLY in Hindi (Devanagari script). Use proper Hindi grammar. Technical product terms can stay in English. "
        
        opening_prompt = (
            f"You are Priya calling a customer to sell {product_name} from {company_name}. "
            f"Product: {pc.get('productDescription', '')}. "
            f"{lang_instruction}"
            f"Say hi, introduce yourself, and tell them ONE exciting benefit of the product. "
            f"DO NOT ask questions. DO NOT use placeholders. Be direct. MAX 2 sentences."
        )
        
        greeting_text = await llm.generate_response(
            prompt=opening_prompt, context=[], personality="sales", language=language
        )
        
        if greeting_text:
            # Pre-generate TTS audio
            from app.config import get_settings
            settings_local = get_settings()
            url = f"{settings_local.SARVAM_API_BASE_URL}/text-to-speech"
            headers = {"api-subscription-key": settings_local.SARVAM_API_KEY, "Content-Type": "application/json"}
            payload = {
                "text": greeting_text[:2500],
                "target_language_code": {"te": "te-IN", "hi": "hi-IN"}.get(language, "en-IN"),
                "speaker": "suhani",
                "model": "bulbul:v3",
                "pace": 1.0,
                "speech_sample_rate": "8000",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        audios = result.get("audios", [])
                        if audios:
                            wav_bytes = base64.b64decode(audios[0])
                            _precompiled_greeting = wav_bytes[44:] if wav_bytes[:4] == b'RIFF' else wav_bytes
                            _precompiled_greeting_text = greeting_text
                            logger.info(f"✅ Greeting pre-compiled: '{greeting_text[:50]}...' ({len(_precompiled_greeting)} bytes)")
    except Exception as e:
        logger.error(f"Failed to pre-compile greeting: {e}")
    
    return {"success": True, "message": f"Product config set for: {config.get('productName', '')}", "greeting_ready": _precompiled_greeting is not None}


@app.get("/api/exotel/ws-url", tags=["Telephony"])
async def get_exotel_ws_url(config_id: str = "default", language: str = "en", CallFrom: str = ""):
    """
    Dynamic WebSocket URL endpoint for Exotel Voicebot applet.
    Exotel hits this HTTPS URL first, and we return the WSS endpoint.
    """
    ws_base = settings.EXOTEL_WS_URL or "wss://indu-u2r5.onrender.com/ws/exotel/voice"
    
    # Look up config by phone number (CallFrom is the customer's number)
    actual_config_id = "default"
    if CallFrom:
        # Find config_id by phone number
        for cid, cfg in _call_configs.items():
            if CallFrom.endswith(cfg.get("_phone", "")):
                actual_config_id = cid
                break
    
    ws_url = f"{ws_base}?config_id={actual_config_id}&language={language}"
    logger.info(f"📞 Exotel requesting WS URL: {ws_url} (from: {CallFrom})")
    return {"url": ws_url}


@app.websocket("/ws/exotel/voice")
async def exotel_voicebot_endpoint(websocket: WebSocket):
    """
    Exotel Voicebot WebSocket endpoint.
    Handles bidirectional audio streaming for AI voice calls.
    """
    await websocket.accept()

    # Create session immediately
    session = ExotelCallSession(websocket=websocket, product_config={})
    
    try:
        logger.info("📞 Exotel WebSocket connection accepted")

        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            # On start event, update session with product config
            if event == "start":
                custom_params = data.get("start", {}).get("custom_parameters", {})
                config_id = custom_params.get("config_id", "default")
                product_config = _call_configs.get(config_id, _default_product_config)
                session.product_config = product_config

            await session.handle_message(data)

            if event == "stop":
                break

    except Exception as e:
        logger.error(f"❌ Exotel WebSocket error: {str(e)}")
    finally:
        logger.info("📴 Exotel WebSocket closed")


@app.post("/api/call/outbound", tags=["Telephony"])
async def make_outbound_call(request_data: dict):
    """
    Trigger an outbound call via Exotel.
    
    Body:
    {
        "phone_number": "+91XXXXXXXXXX",
        "product_config": { ... },
        "language": "en"
    }
    """
    import aiohttp

    phone_number = request_data.get("phone_number")
    product_config = request_data.get("product_config", {})
    language = request_data.get("language", "en")

    if not phone_number:
        return JSONResponse(status_code=400, content={"error": "phone_number is required"})

    # Store product config for this call
    import uuid
    config_id = str(uuid.uuid4())[:8]
    _call_configs[config_id] = {**product_config, "language": language, "_phone": phone_number}

    # Exotel API credentials
    exotel_sid = settings.EXOTEL_SID
    exotel_api_key = settings.EXOTEL_API_KEY
    exotel_api_token = settings.EXOTEL_API_TOKEN
    exotel_caller_id = settings.EXOTEL_CALLER_ID

    if not all([exotel_sid, exotel_api_key, exotel_api_token, exotel_caller_id]):
        return JSONResponse(
            status_code=500,
            content={"error": "Exotel credentials not configured"},
        )

    # Build the WebSocket URL that Exotel will connect to
    # This should be your publicly accessible server URL
    ws_url = settings.EXOTEL_WS_URL or "wss://your-server.com/ws/exotel/voice"
    ws_url_with_params = f"{ws_url}?config_id={config_id}&language={language}"

    # Exotel API to make outbound call
    # Uses the Voicebot flow we created
    url = f"https://api.exotel.com/v1/Accounts/{exotel_sid}/Calls/connect.json"

    form_data = {
        "From": phone_number,
        "CallerId": exotel_caller_id,
        "Url": f"http://my.exotel.com/exoml/start/{exotel_sid}/1245633",
    }

    try:
        auth = aiohttp.BasicAuth(exotel_api_key, exotel_api_token)
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(url, data=form_data, auth=auth) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    call_sid = result.get("Call", {}).get("Sid", "")
                    logger.info(f"📞 Outbound call initiated: {call_sid} → {phone_number}")
                    return {
                        "success": True,
                        "call_sid": call_sid,
                        "config_id": config_id,
                        "message": f"Call initiated to {phone_number}",
                    }
                else:
                    error_text = await resp.text()
                    logger.error(f"Exotel API error ({resp.status}): {error_text}")
                    return JSONResponse(
                        status_code=resp.status,
                        content={"error": f"Exotel API error: {error_text[:200]}"},
                    )
    except Exception as e:
        logger.error(f"Outbound call error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
