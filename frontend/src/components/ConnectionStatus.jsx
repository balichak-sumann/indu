import React from 'react'
import useConversationStore from '../store/conversationStore'

/**
 * Connection Status Component
 * Displays current connection status
 */
function ConnectionStatus() {
  const { connectionStatus } = useConversationStore()

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-400'
      case 'connecting':
        return 'text-yellow-400'
      case 'disconnected':
        return 'text-red-400'
      case 'error':
        return 'text-red-500'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return '● Connected'
      case 'connecting':
        return '⟳ Connecting...'
      case 'disconnected':
        return '○ Disconnected'
      case 'error':
        return '✕ Error'
      default:
        return 'Initializing...'
    }
  }

  return (
    <div className={`text-sm font-medium ${getStatusColor()}`}>
      {getStatusText()}
    </div>
  )
}

export default ConnectionStatus
