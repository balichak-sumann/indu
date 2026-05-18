"""
Sarvam AI integration - STT, LLM (streaming), and TTS services
Optimized for real-time conversation with minimal latency
"""

import base64
import asyncio
import aiohttp
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Language code mapping for Sarvam API (BCP-47 format)
LANGUAGE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN",
    "hinglish": "hi-IN",
    "auto": "unknown",
}

# TTS language code mapping
TTS_LANGUAGE_MAP = {
    "en": "en-IN",
    "hi": "hi-IN",
    "te": "te-IN",
    "hinglish": "hi-IN",
}


class SarvamSTT:
    """
    Sarvam Speech-to-Text Service
    Uses the /speech-to-text REST API with saaras:v3 model
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = "saaras:v3"
        self.base_url = settings.SARVAM_API_BASE_URL
        logger.info(f"SarvamSTT initialized with model: {self.model}")

    async def transcribe_audio(self, audio_data: bytes, language: str = "en") -> dict:
        """
        Transcribe audio to text using Sarvam STT API
        """
        language_code = LANGUAGE_MAP.get(language, "unknown")

        url = f"{self.base_url}/speech-to-text"
        headers = {
            "api-subscription-key": self.api_key,
        }

        # Create multipart form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            audio_data,
            filename="audio.wav",
            content_type="audio/wav",
        )
        form_data.add_field("model", self.model)
        form_data.add_field("language_code", language_code)
        form_data.add_field("mode", "transcribe")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        transcript = result.get("transcript", "")
                        logger.info(f"STT result: '{transcript[:50]}...' (lang: {language_code})")
                        return {
                            "text": transcript,
                            "language_code": result.get("language_code", language_code),
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"STT API error ({response.status}): {error_text}")
                        return {"text": "", "error": error_text}
        except Exception as e:
            logger.error(f"STT request failed: {str(e)}")
            return {"text": "", "error": str(e)}


class SarvamLLM:
    """
    Sarvam Language Model Service - STREAMING
    Uses /v1/chat/completions with stream=true for real-time token delivery
    Calls sentence_callback as soon as a complete sentence is ready
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = "sarvam-m"
        self.base_url = settings.SARVAM_API_BASE_URL
        logger.info(f"SarvamLLM initialized with model: {self.model}")

    async def generate_response_streaming(
        self, prompt: str, context: list = None, personality: str = "assistant",
        language: str = "en", sentence_callback=None
    ) -> str:
        """
        Generate response and call sentence_callback for each sentence.
        Uses non-streaming API, then splits response into sentences for parallel TTS.
        """
        from app.prompts.templates import get_system_prompt

        system_prompt = get_system_prompt(personality)
        system_prompt += "\nCRITICAL RULES FOR THIS LIVE PHONE CALL:\n1. Respond in ONLY 1-2 short sentences\n2. If user switches to Hindi/Telugu, respond FULLY in that language (native script). Technical terms can stay English.\n3. DO NOT ask questions unless customer asks you something first. Just pitch benefits.\n4. Always steer conversation toward the product you're selling.\n5. Be warm and natural."

        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation context (last 6 messages for speed)
        # CRITICAL: Sarvam API requires strict alternation: user → assistant → user → ...
        # First non-system message MUST be from user
        if context:
            # Filter and enforce alternation
            alternated = []
            last_role = None
            for msg in context[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if not content:
                    continue
                # Skip consecutive same-role messages (keep the latest one)
                if role == last_role:
                    alternated[-1] = {"role": role, "content": content}
                else:
                    alternated.append({"role": role, "content": content})
                    last_role = role
            
            # Ensure first message is from user
            if alternated and alternated[0]["role"] == "assistant":
                alternated.insert(0, {"role": "user", "content": "Hi"})
            
            # Ensure last message before current user prompt is from assistant
            # (so we don't get user → user)
            if alternated and alternated[-1]["role"] == "user":
                alternated.pop()  # Remove trailing user msg (current prompt replaces it)
            
            messages.extend(alternated)

        messages.append({"role": "user", "content": prompt})

        # Get full response (non-streaming because streaming + reasoning_effort = empty content)
        full_response = await self._generate_non_streaming(messages)

        # Split into sentences and fire callbacks for parallel TTS
        if sentence_callback and full_response:
            sentences = self._split_sentences(full_response)
            for sentence in sentences:
                if sentence.strip():
                    await sentence_callback(sentence.strip())

        return full_response

    def _split_sentences(self, text: str) -> list:
        """Split text into sentences at natural boundaries"""
        import re
        parts = re.split(r'(?<=[.!?।॥])\s+', text)
        if len(parts) <= 1:
            return [text]
        return [p for p in parts if p.strip()]

    def _strip_think_tags(self, text: str) -> str:
        """
        Aggressively clean model output.
        """
        import re
        
        # Strip closed think blocks
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Strip unclosed think blocks
        cleaned = re.sub(r'<think>.*$', '', cleaned, flags=re.DOTALL).strip()
        
        # If cleaned result is substantial (>20 chars), use it
        if len(cleaned) > 20:
            text = cleaned
        else:
            # Result too short - look inside think tags for the actual response
            think_match = re.search(r'<think>(.*?)(?:</think>|$)', text, flags=re.DOTALL)
            if think_match:
                think_content = think_match.group(1)
                quoted = re.findall(r'"([^"]{10,})"', think_content)
                if quoted:
                    text = max(quoted, key=len)
                else:
                    lines = [l.strip() for l in think_content.split('\n') if len(l.strip()) > 15]
                    if lines:
                        text = lines[-1]
                    else:
                        text = cleaned if cleaned else "Could you say that again?"
            else:
                text = cleaned if cleaned else "Could you say that again?"
        
        # POST-PROCESSING: Remove useless meta-phrases
        meta_starts = [
            "Let me rephrase", "Let me explain", "Let me tell you",
            "Let me clarify", "Let me break", "Let me put",
            "Oh sorry", "I apologize", "Sorry about that",
        ]
        for phrase in meta_starts:
            if text.startswith(phrase):
                # Remove the meta-phrase and keep the rest
                after = text[len(phrase):].lstrip('.,!: ')
                if len(after) > 15:
                    text = after
                    break
        
        # Limit to ~150 chars to keep TTS fast (cut at sentence boundary)
        if len(text) > 150:
            # Find last sentence end before 150 chars
            for i in range(150, 50, -1):
                if text[i] in '.!?।':
                    text = text[:i+1]
                    break
            else:
                text = text[:150]
        
        return text.strip()

    async def _generate_non_streaming(self, messages: list) -> str:
        """Non-streaming LLM call"""
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        message = result["choices"][0]["message"]
                        content = message.get("content") or ""
                        # Strip <think>...</think> tags (model leaks reasoning)
                        content = self._strip_think_tags(content)
                        content = content.strip()
                        if not content or len(content) < 10:
                            logger.warning(f"LLM returned empty/short content. Full response: {result}")
                            content = "Could you say that again? I didn't quite catch that."
                        logger.info(f"LLM response ({result['usage']['completion_tokens']} tokens): '{content[:80]}...'")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"LLM API error ({response.status}): {error_text[:200]}")
                        return "I'm sorry, I couldn't process that. Could you try again?"
        except Exception as e:
            logger.error(f"LLM non-streaming failed: {str(e)}")
            return "I'm sorry, something went wrong. Please try again."

    async def generate_response(
        self, prompt: str, context: list = None, personality: str = "assistant",
        language: str = "en"
    ) -> str:
        """
        Non-streaming generate (used for initial greeting etc.)
        """
        return await self.generate_response_streaming(
            prompt=prompt, context=context, personality=personality,
            language=language, sentence_callback=None
        )


class SarvamTTS:
    """
    Sarvam Text-to-Speech Service
    Uses streaming HTTP endpoint for fast audio generation
    """

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.model = "bulbul:v3"
        self.base_url = settings.SARVAM_API_BASE_URL
        logger.info(f"SarvamTTS initialized with model: {self.model}")

    async def synthesize_speech(self, text: str, language: str = "en") -> str:
        """
        Synthesize text to speech - returns base64 audio
        """
        # Support both short codes and BCP-47 codes
        if "-" in language:
            bcp47_to_tts = {
                "en-IN": "en-IN", "hi-IN": "hi-IN", "te-IN": "te-IN",
                "bn-IN": "bn-IN", "kn-IN": "kn-IN", "ml-IN": "ml-IN",
                "mr-IN": "mr-IN", "ta-IN": "ta-IN", "gu-IN": "gu-IN",
                "od-IN": "od-IN", "pa-IN": "pa-IN",
            }
            target_language = bcp47_to_tts.get(language, "en-IN")
        else:
            target_language = TTS_LANGUAGE_MAP.get(language, "en-IN")

        # Use streaming endpoint (faster time-to-first-byte)
        url = f"{self.base_url}/text-to-speech/stream"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text[:3500],
            "target_language_code": target_language,
            "speaker": "suhani",
            "model": self.model,
            "pace": 1.2,
            "output_audio_codec": "mp3",
        }

        try:
            timeout = aiohttp.ClientTimeout(total=45)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        audio_bytes = await response.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        logger.info(f"TTS stream: {len(audio_bytes)} bytes")
                        return audio_base64
                    else:
                        error_text = await response.text()
                        logger.warning(f"TTS stream failed ({response.status}): {error_text[:100]}")
                        return await self._synthesize_rest(text, target_language)
        except Exception as e:
            logger.warning(f"TTS stream error: {str(e)}, falling back to REST")
            return await self._synthesize_rest(text, target_language)

    async def _synthesize_rest(self, text: str, target_language: str) -> str:
        """Fallback REST TTS endpoint"""
        url = f"{self.base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text[:2500],
            "target_language_code": target_language,
            "speaker": "suhani",
            "model": self.model,
            "pace": 1.2,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        audios = result.get("audios", [])
                        if audios:
                            return audios[0]
                    return ""
        except Exception as e:
            logger.error(f"TTS REST failed: {str(e)}")
            return ""


# Export singleton instances
stt = SarvamSTT()
llm = SarvamLLM()
tts = SarvamTTS()

