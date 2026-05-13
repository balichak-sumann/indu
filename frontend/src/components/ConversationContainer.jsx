import React, { useEffect, useRef } from 'react'
import useConversationStore from '../store/conversationStore'

/**
 * Conversation Container - shows messages and live status
 * No manual controls - everything is automatic
 */
function ConversationContainer({ processingStage }) {
  const { messages, currentTranscription, isRecording, isAISpeaking } =
    useConversationStore()
  const messagesEndRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentTranscription, processingStage])

  // No mic level polling needed - Silero VAD handles detection
  // isRecording state from store tells us when user is speaking

  const getStageLabel = (stage) => {
    switch (stage) {
      case 'transcribing': return 'Listening...'
      case 'thinking': return 'Thinking...'
      case 'speaking': return 'Responding...'
      default: return 'Processing...'
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !processingStage ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-6">
                {isAISpeaking ? '🔊' : '👂'}
              </div>
              <p className="text-gray-300 text-lg mb-2">
                {isAISpeaking ? 'AI is speaking...' : 'Listening...'}
              </p>
              <p className="text-gray-500 text-sm">
                Just start speaking naturally — no buttons needed
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-md px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-accent/20 border border-accent/40 text-accent rounded-br-sm'
                      : 'bg-secondary/60 border border-accent/15 text-gray-100 rounded-bl-sm'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className="text-xs opacity-40 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Live Status Bar */}
      <div className="border-t border-accent/10 bg-secondary/40 backdrop-blur-sm px-6 py-4">
        {/* Processing indicator */}
        {processingStage && (
          <div className="flex items-center gap-3 mb-3">
            <div className="w-3 h-3 border-2 border-accent/50 border-t-accent rounded-full animate-spin"></div>
            <p className="text-sm text-accent">{getStageLabel(processingStage)}</p>
          </div>
        )}

        {/* AI Speaking indicator */}
        {isAISpeaking && !processingStage && (
          <div className="flex items-center gap-3 mb-3">
            <div className="flex gap-0.5">
              {[...Array(4)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-accent rounded-full animate-wave"
                  style={{ height: '16px', animationDelay: `${i * 0.1}s` }}
                ></div>
              ))}
            </div>
            <p className="text-sm text-accent">AI speaking...</p>
          </div>
        )}

        {/* Status indicator */}
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${
            isAISpeaking ? 'bg-purple-500 animate-pulse' :
            isRecording ? 'bg-red-500 animate-pulse' :
            'bg-green-500'
          }`}></div>
          <span className="text-xs text-gray-500">
            {isAISpeaking
              ? '🔊 AI speaking'
              : isRecording
              ? '🗣️ Listening to you...'
              : '👂 Ready — speak anytime'}
          </span>
        </div>

        {/* Current transcription preview */}
        {currentTranscription && (
          <p className="text-sm text-gray-300 mt-2 italic">"{currentTranscription}"</p>
        )}
      </div>
    </div>
  )
}

export default ConversationContainer
