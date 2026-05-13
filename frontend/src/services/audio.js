/**
 * Audio service using Silero VAD (ML-based voice activity detection)
 * Uses @ricky0123/vad-web loaded from CDN
 * 
 * Key features:
 * - ML-based speech detection (ignores background noise)
 * - Sequential audio queue (no overlapping)
 * - Echo protection (ignores AI's own audio)
 * - Interrupt support (stops playback when user speaks)
 */

class AudioService {
  constructor() {
    this.vad = null
    this.listeners = {}
    this.isListening = false
    this.isAIPlaying = false
    this.currentAudio = null
    this.audioQueue = []
    this.isPlayingQueue = false
    this._recentlyStoppedPlaying = false
    this._playbackStartTime = 0
  }

  /**
   * Initialize the Silero VAD model
   */
  async initialize() {
    try {
      const MicVAD = window.vad.MicVAD

      this.vad = await MicVAD.new({
        onSpeechStart: () => {
          // Ignore if AI just finished (echo protection)
          if (this._recentlyStoppedPlaying) return
          console.log('🗣️ Speech detected (Silero VAD)')
          this.emit('speech_start')
        },

        onSpeechEnd: (audioData) => {
          // audioData is Float32Array at 16kHz - convert to WAV
          const wavBlob = this._float32ToWavBlob(audioData, 16000)
          console.log('✅ Speech ended, size:', wavBlob.size, 'bytes')
          this.emit('speech_end', wavBlob)
        },

        onVADMisfire: () => {
          console.log('⚡ VAD misfire (too short)')
        },

        // Strict settings to avoid background noise
        model: 'v5',
        positiveSpeechThreshold: 0.85,
        negativeSpeechThreshold: 0.5,
        redemptionMs: 1800,
        minSpeechMs: 1200,
        preSpeechPadMs: 300,

        baseAssetPath: 'https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.18/dist/',
        onnxWASMBasePath: 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.19.0/dist/',
      })

      console.log('✅ Silero VAD initialized')
      return true
    } catch (error) {
      console.error('❌ VAD init error:', error)
      this.emit('error', error)
      return false
    }
  }

  startListening() {
    if (!this.vad || this.isListening) return
    this.vad.start()
    this.isListening = true
    console.log('👂 Listening active')
    this.emit('listening_started')
  }

  stopListening() {
    if (!this.vad) return
    this.vad.pause()
    this.isListening = false
    this.emit('listening_stopped')
  }

  setAIPlaying(playing) {
    this.isAIPlaying = playing
    if (playing) {
      this._playbackStartTime = Date.now()
    }
  }

  getVolume() {
    return this.isAIPlaying ? 0 : (this.isListening ? 5 : 0)
  }

  /**
   * Convert Float32Array audio to WAV Blob
   */
  _float32ToWavBlob(float32Array, sampleRate) {
    const numChannels = 1
    const bitsPerSample = 16
    const byteRate = sampleRate * numChannels * (bitsPerSample / 8)
    const blockAlign = numChannels * (bitsPerSample / 8)
    const dataSize = float32Array.length * (bitsPerSample / 8)
    const headerSize = 44
    const totalSize = headerSize + dataSize

    const buffer = new ArrayBuffer(totalSize)
    const view = new DataView(buffer)

    const writeString = (offset, str) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, totalSize - 8, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitsPerSample, true)
    writeString(36, 'data')
    view.setUint32(40, dataSize, true)

    let offset = 44
    for (let i = 0; i < float32Array.length; i++) {
      const sample = Math.max(-1, Math.min(1, float32Array[i]))
      const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      view.setInt16(offset, int16, true)
      offset += 2
    }

    return new Blob([buffer], { type: 'audio/wav' })
  }

  /**
   * Queue audio for sequential playback
   * Audio chunks arrive as sentences - play them in order without overlap
   */
  queueAudio(base64Audio, volume = 1.0) {
    this.audioQueue.push({ audio: base64Audio, volume })
    if (!this.isPlayingQueue) {
      this._processQueue()
    }
  }

  async _processQueue() {
    if (this.isPlayingQueue) return
    this.isPlayingQueue = true
    this.emit('ai_speaking_start')

    while (this.audioQueue.length > 0) {
      // Check if interrupted
      if (!this.isAIPlaying) {
        this.audioQueue = []
        break
      }
      const item = this.audioQueue.shift()
      await this._playOneChunk(item.audio, item.volume)
    }

    this.isPlayingQueue = false

    // Echo protection: brief delay before re-enabling speech detection
    this._recentlyStoppedPlaying = true
    setTimeout(() => {
      this._recentlyStoppedPlaying = false
    }, 600)

    this.setAIPlaying(false)
    this.emit('ai_speaking_end')
  }

  /**
   * Play a single audio chunk and wait for completion
   */
  _playOneChunk(base64Audio, volume) {
    return new Promise((resolve) => {
      try {
        const bin = atob(base64Audio)
        const bytes = new Uint8Array(bin.length)
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)

        const blob = new Blob([bytes], { type: 'audio/mpeg' })
        const url = URL.createObjectURL(blob)
        this.currentAudio = new Audio(url)
        this.currentAudio.volume = volume

        this.currentAudio.onended = () => {
          URL.revokeObjectURL(url)
          this.currentAudio = null
          resolve()
        }
        this.currentAudio.onerror = () => {
          URL.revokeObjectURL(url)
          this.currentAudio = null
          resolve()
        }
        this.currentAudio.play().catch(() => {
          this.currentAudio = null
          resolve()
        })
      } catch (e) {
        this.currentAudio = null
        resolve()
      }
    })
  }

  /**
   * Stop AI audio playback immediately (for interruption)
   */
  stopPlayback() {
    this.audioQueue = []
    this.isPlayingQueue = false
    if (this.currentAudio) {
      this.currentAudio.pause()
      this.currentAudio = null
    }
    this.setAIPlaying(false)
    this.emit('ai_speaking_end')
  }

  /**
   * Check if AI has been playing long enough to allow interruption
   * Prevents false interrupts from audio bleed
   */
  canInterrupt() {
    if (!this.isAIPlaying) return false
    const playingFor = Date.now() - this._playbackStartTime
    return playingFor > 500 // Must be playing for at least 500ms
  }

  /**
   * Convert blob to base64
   */
  async blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result.split(',')[1])
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  // Event system
  on(et, cb) { if (!this.listeners[et]) this.listeners[et] = []; this.listeners[et].push(cb) }
  off(et, cb) { if (this.listeners[et]) this.listeners[et] = this.listeners[et].filter(c => c !== cb) }
  emit(et, d) { if (this.listeners[et]) this.listeners[et].forEach(cb => { try { cb(d) } catch(e) {} }) }

  cleanup() {
    this.stopListening()
    this.stopPlayback()
    if (this.vad) { this.vad.pause() }
    this.listeners = {}
  }
}

export default new AudioService()
