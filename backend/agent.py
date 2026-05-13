"""
NOTE: Pipecat agent is NOT used in this project.
The real-time conversation is handled by the streaming pipeline in:
- app/websocket/manager.py (orchestration)
- app/ai/sarvam.py (STT + Streaming LLM + TTS)

The pipeline works as:
1. User speaks → Silero VAD detects speech end → WAV sent to backend
2. STT transcribes audio (~1-2s)
3. Streaming LLM generates response sentence-by-sentence
4. Each sentence is IMMEDIATELY sent to TTS (parallel processing)
5. Audio chunks are streamed to frontend as they're ready

This gives ~2-3s time-to-first-audio vs ~6-8s with sequential processing.
"""
