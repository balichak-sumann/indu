/**
 * Zustand store for application state management
 */

import { create } from 'zustand'

const useConversationStore = create((set) => ({
  // Session state
  sessionId: null,
  isConnected: false,
  language: 'en',
  personality: 'assistant',
  
  // Conversation state
  messages: [],
  currentTranscription: '',
  isRecording: false,
  isAISpeaking: false,
  
  // UI state
  isMuted: false,
  volume: 100,
  
  // Status
  connectionStatus: 'disconnected',
  lastError: null,
  
  // Actions
  setSessionId: (id) => set({ sessionId: id }),
  setConnected: (connected) => set({ isConnected: connected }),
  setLanguage: (lang) => set({ language: lang }),
  setPersonality: (personality) => set({ personality }),
  setIsRecording: (recording) => set({ isRecording: recording }),
  setIsAISpeaking: (speaking) => set({ isAISpeaking: speaking }),
  setMuted: (muted) => set({ isMuted: muted }),
  setVolume: (vol) => set({ volume: vol }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setLastError: (error) => set({ lastError: error }),
  setCurrentTranscription: (text) => set({ currentTranscription: text }),
  
  // Message actions
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  clearMessages: () => set({ messages: [] }),
  
  // Reset
  reset: () => set({
    sessionId: null,
    isConnected: false,
    messages: [],
    currentTranscription: '',
    isRecording: false,
    isAISpeaking: false,
    isMuted: false,
    connectionStatus: 'disconnected',
    lastError: null,
  }),
}))

export default useConversationStore
