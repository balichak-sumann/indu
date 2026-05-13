import React, { useState, useEffect, useRef } from 'react'
import useConversationStore from './store/conversationStore'
import WebSocketService from './services/websocket'
import AudioService from './services/audio'
import ConversationContainer from './components/ConversationContainer'
import ConnectionStatus from './components/ConnectionStatus'
import ProductSetup from './components/ProductSetup'

/**
 * Main App Component
 * Product setup → AI initiates sales call → Natural conversation
 */
function App() {
  const [productConfig, setProductConfig] = useState(null)

  if (!productConfig) {
    return <ProductSetup onStart={setProductConfig} />
  }

  return <ConversationApp productConfig={productConfig} onBack={() => setProductConfig(null)} />
}

/**
 * Conversation App - real-time voice conversation with streaming pipeline
 */
function ConversationApp({ productConfig, onBack }) {
  const {
    sessionId,
    isConnected,
    setSessionId,
    setConnected,
    setConnectionStatus,
    setLastError,
    setIsAISpeaking,
    setIsRecording,
    setCurrentTranscription,
    addMessage,
    reset,
    lastError,
    volume,
    isMuted,
  } = useConversationStore()

  const [isInitializing, setIsInitializing] = useState(false)
  const [processingStage, setProcessingStage] = useState(null)
  const [isReady, setIsReady] = useState(false)
  const volumeRef = useRef(volume)
  const isMutedRef = useRef(isMuted)

  useEffect(() => { volumeRef.current = volume }, [volume])
  useEffect(() => { isMutedRef.current = isMuted }, [isMuted])

  /**
   * Initialize on mount
   */
  useEffect(() => {
    const initialize = async () => {
      try {
        setIsInitializing(true)
        setConnectionStatus('initializing')

        // Initialize audio with always-on mic (Silero VAD)
        const audioReady = await AudioService.initialize()
        if (!audioReady) {
          throw new Error('Failed to initialize audio - please allow microphone access')
        }

        // Create session
        const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        setSessionId(newSessionId)

        // Connect WebSocket
        await WebSocketService.connect(newSessionId)
        setConnected(true)
        setConnectionStatus('connected')

        // Start session with product config
        WebSocketService.startSession({
          language: productConfig.language || 'en',
          personality: 'sales',
          productConfig: productConfig,
        })

        // Start always-on listening
        AudioService.startListening()
        setIsReady(true)

        console.log('✅ Initialized - AI sales call active')
      } catch (error) {
        console.error('❌ Init error:', error)
        setConnectionStatus('error')
        setLastError(error.message)
      } finally {
        setIsInitializing(false)
      }
    }

    initialize()

    return () => {
      AudioService.cleanup()
      WebSocketService.disconnect()
      reset()
    }
  }, [])

  /**
   * VAD events - core conversation loop
   */
  useEffect(() => {
    if (!isReady) return

    const handleSpeechStart = () => {
      console.log('🗣️ User speaking...')
      setIsRecording(true)
      setCurrentTranscription('')
      setProcessingStage(null)
      setLastError(null)

      // Interrupt AI if it's been playing long enough
      if (AudioService.canInterrupt()) {
        console.log('🛑 Interrupting AI')
        AudioService.stopPlayback()
        setIsAISpeaking(false)
        WebSocketService.interrupt()
      }
    }

    const handleSpeechEnd = async (audioBlob) => {
      console.log('📤 Sending audio, size:', audioBlob.size)
      setIsRecording(false)

      try {
        const base64 = await AudioService.blobToBase64(audioBlob)
        WebSocketService.sendAudioChunk(base64, 0)
        WebSocketService.stopAudio()
      } catch (error) {
        console.error('Error sending audio:', error)
        setLastError('Failed to send audio')
      }
    }

    const handleAISpeakingStart = () => {
      setIsAISpeaking(true)
    }

    const handleAISpeakingEnd = () => {
      setIsAISpeaking(false)
    }

    AudioService.on('speech_start', handleSpeechStart)
    AudioService.on('speech_end', handleSpeechEnd)
    AudioService.on('ai_speaking_start', handleAISpeakingStart)
    AudioService.on('ai_speaking_end', handleAISpeakingEnd)

    return () => {
      AudioService.off('speech_start', handleSpeechStart)
      AudioService.off('speech_end', handleSpeechEnd)
      AudioService.off('ai_speaking_start', handleAISpeakingStart)
      AudioService.off('ai_speaking_end', handleAISpeakingEnd)
    }
  }, [isReady])

  /**
   * WebSocket events from backend
   */
  useEffect(() => {
    if (!isReady) return

    const handleDisconnected = () => {
      setConnected(false)
      setConnectionStatus('disconnected')
    }

    const handleTranscription = (data) => {
      console.log('📝 Transcription:', data.text)
      setCurrentTranscription(data.text)
      if (data.is_final) {
        addMessage({
          role: 'user',
          content: data.text,
          timestamp: new Date().toISOString(),
        })
        setCurrentTranscription('')
      }
    }

    const handleAIResponse = (data) => {
      console.log('🤖 AI:', data.text)
      addMessage({
        role: 'assistant',
        content: data.text,
        timestamp: data.timestamp || new Date().toISOString(),
      })
    }

    const handleAIAudio = (data) => {
      // Don't play if user is currently speaking
      if (useConversationStore.getState().isRecording) return
      if (isMutedRef.current) return

      // Set AI playing and queue the audio chunk
      AudioService.setAIPlaying(true)
      setIsAISpeaking(true)
      AudioService.queueAudio(data.audio, volumeRef.current / 100)
    }

    const handleProcessingComplete = () => {
      setProcessingStage(null)
    }

    const handleStatus = (data) => {
      setProcessingStage(data.stage)
    }

    const handleError = (data) => {
      if (data && data.message) {
        console.error('Backend error:', data.message)
        setLastError(data.message)
        setProcessingStage(null)
      }
    }

    WebSocketService.on('disconnected', handleDisconnected)
    WebSocketService.on('transcription', handleTranscription)
    WebSocketService.on('ai_response', handleAIResponse)
    WebSocketService.on('ai_audio', handleAIAudio)
    WebSocketService.on('status', handleStatus)
    WebSocketService.on('processing_complete', handleProcessingComplete)
    WebSocketService.on('error', handleError)

    return () => {
      WebSocketService.off('disconnected', handleDisconnected)
      WebSocketService.off('transcription', handleTranscription)
      WebSocketService.off('ai_response', handleAIResponse)
      WebSocketService.off('ai_audio', handleAIAudio)
      WebSocketService.off('status', handleStatus)
      WebSocketService.off('processing_complete', handleProcessingComplete)
      WebSocketService.off('error', handleError)
    }
  }, [isReady])

  return (
    <div className="w-full h-screen flex flex-col bg-gradient-to-br from-primary to-secondary overflow-hidden">
      {/* Header */}
      <header className="bg-secondary/50 backdrop-blur-md border-b border-accent/10 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent animate-pulse"></div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-accent to-accent-light bg-clip-text text-transparent">
              AI Sales Agent
            </h1>
          </div>
          <ConnectionStatus />
        </div>
      </header>

      {lastError && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-200 px-6 py-2 text-sm flex items-center justify-between">
          <span>{lastError}</span>
          <button onClick={() => setLastError(null)} className="text-red-300 hover:text-red-100 ml-4">×</button>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {isInitializing ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-accent/30 border-t-accent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-lg text-accent">Initializing AI Agent...</p>
              <p className="text-sm text-gray-400 mt-2">Please allow microphone access</p>
            </div>
          </div>
        ) : (
          <ConversationContainer processingStage={processingStage} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-secondary/30 backdrop-blur-md border-t border-accent/10 px-6 py-3 text-center text-sm text-gray-400">
        <p>Always listening • Speak naturally • Powered by Sarvam AI</p>
      </footer>
    </div>
  )
}

export default App
