import asyncio, aiohttp, base64, sys
sys.path.insert(0, '.')
from app.config import get_settings
settings = get_settings()

async def test_tts(text, language, filename):
    url = f"{settings.SARVAM_API_BASE_URL}/text-to-speech"
    headers = {"api-subscription-key": settings.SARVAM_API_KEY, "Content-Type": "application/json"}
    
    # 8kHz (what phone uses)
    payload = {"text": text, "target_language_code": language, "speaker": "suhani", "model": "bulbul:v3", "pace": 1.2, "speech_sample_rate": "8000"}
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload) as r:
            if r.status == 200:
                result = await r.json()
                wav = base64.b64decode(result["audios"][0])
                with open(f"{filename}_8khz.wav", "wb") as f: f.write(wav)
                print(f"OK: {filename}_8khz.wav ({len(wav)} bytes)")
            else:
                print(f"FAIL {r.status}: {(await r.text())[:100]}")

    # 24kHz (high quality)
    payload["speech_sample_rate"] = "24000"
    async with aiohttp.ClientSession() as s:
        async with s.post(url, headers=headers, json=payload) as r:
            if r.status == 200:
                result = await r.json()
                wav = base64.b64decode(result["audios"][0])
                with open(f"{filename}_24khz.wav", "wb") as f: f.write(wav)
                print(f"OK: {filename}_24khz.wav ({len(wav)} bytes)")
            else:
                print(f"FAIL {r.status}: {(await r.text())[:100]}")

async def main():
    print("=== English ===")
    await test_tts("Hello! This is your AI sales assistant. How can I help you today?", "en-IN", "english")
    print("\n=== Telugu ===")
    await test_tts("ఖచ్చితంగా! నేను తెలుగులో మాట్లాడగలను. మీకు ఏమి సహాయం కావాలి?", "te-IN", "telugu")
    print("\n=== Hindi ===")
    await test_tts("जी बिल्कुल! मैं आपकी किस तरह मदद कर सकता हूँ?", "hi-IN", "hindi")

asyncio.run(main())
