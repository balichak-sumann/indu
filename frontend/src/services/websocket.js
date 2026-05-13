/**
 * WebSocket service for real-time communication
 */

class WebSocketService {
  constructor() {
    this.ws = null
    this.sessionId = null
    this.listeners = {}
  }

  /**
   * Connect to WebSocket server
   * @param {string} sessionId - Session identifier
   * @param {object} options - Connection options
   */
  connect(sessionId, options = {}) {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = options.host || `${window.location.hostname}:8000`
        const url = `${protocol}//${host}/ws/conversation/${sessionId}`

        this.sessionId = sessionId
        this.ws = new WebSocket(url)

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected')
          this.emit('connected')
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            const eventType = data.event || 'unknown'
            console.log(`📨 Received: ${eventType}`)
            this.emit(eventType, data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error)
          this.emit('error', error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('🔌 WebSocket disconnected')
          this.emit('disconnected')
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Send message through WebSocket
   * @param {object} data - Data to send
   */
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  /**
   * Start session
   * @param {object} options - Session options
   */
  startSession(options = {}) {
    this.send({
      event: 'start_session',
      ...options,
    })
  }

  /**
   * Send audio chunk
   * @param {string} audioData - Base64 encoded audio
   * @param {number} sequence - Sequence number
   */
  sendAudioChunk(audioData, sequence) {
    this.send({
      event: 'audio_chunk',
      data: audioData,
      sequence,
    })
  }

  /**
   * Stop audio stream
   */
  stopAudio() {
    this.send({
      event: 'stop_audio',
    })
  }

  /**
   * Interrupt AI speaking
   */
  interrupt() {
    this.send({
      event: 'interrupt',
    })
  }

  /**
   * Send keep-alive ping
   */
  ping() {
    this.send({
      event: 'ping',
    })
  }

  /**
   * Register event listener
   * @param {string} eventType - Event type
   * @param {function} callback - Callback function
   */
  on(eventType, callback) {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = []
    }
    this.listeners[eventType].push(callback)
  }

  /**
   * Unregister event listener
   * @param {string} eventType - Event type
   * @param {function} callback - Callback function
   */
  off(eventType, callback) {
    if (this.listeners[eventType]) {
      this.listeners[eventType] = this.listeners[eventType].filter(
        (cb) => cb !== callback
      )
    }
  }

  /**
   * Emit event to listeners
   * @param {string} eventType - Event type
   * @param {*} data - Event data
   */
  emit(eventType, data) {
    if (this.listeners[eventType]) {
      this.listeners[eventType].forEach((callback) => {
        try {
          callback(data)
        } catch (error) {
          console.error(`Error in ${eventType} listener:`, error)
        }
      })
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
      this.sessionId = null
      this.listeners = {}
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// Export singleton instance
export default new WebSocketService()
