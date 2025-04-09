import { useEffect, useRef, useState } from 'react'

// Define the structure of pose data
export interface PoseData {
  landmarks: {
    [key: number]: {
      x: number
      y: number
      z: number
    }
  }
  feedback?: string
  message?: string
  calibration_success?: boolean
  reference_landmarks?: {
    [key: number]: {
      x: number
      y: number
      z: number
    }
  }
}

// WebSocket hook for handling pose data
export function useWebSocket() {
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [poseData, setPoseData] = useState<PoseData | null>(null)
  const [lastMessage, setLastMessage] = useState<string | null>(null)
  const [lastEvent, setLastEvent] = useState<any>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [referenceLandmarks, setReferenceLandmarks] = useState<Record<string, any>>({})
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // Set up WebSocket connection to backend
    const connectWebSocket = () => {
      // Close any existing connection
      if (wsRef.current) {
        wsRef.current.close()
      }
      
      // Create new WebSocket connection
      const ws = new WebSocket('ws://127.0.0.1:5000/ws')
      wsRef.current = ws
      
      // Connection opened
      ws.addEventListener('open', () => {
        console.log('WebSocket connection established')
        setIsConnected(true)
        // Clear any pending reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      })
      
      // Listen for messages
      ws.addEventListener('message', (event) => {
        try {
          const data = JSON.parse(event.data) as PoseData
          setPoseData(data)
          
          // Process feedback
          if (data.feedback) {
            setFeedback(data.feedback)
          }
          
          // If there's a message, store it
          if (data.message) {
            setLastMessage(data.message)
          }
          
          // Store the full event for debugging and state tracking
          setLastEvent(data)
          
          // Handle calibration success
          if (data.calibration_success) {
            console.log('Calibration successful!')
            setFeedback(`Calibration successful! Your pose has been recorded.`)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      })
      
      // Handle connection close
      ws.addEventListener('close', () => {
        console.log('WebSocket connection closed')
        setIsConnected(false)
        setFeedback('Connection lost. Attempting to reconnect...')
        
        // Attempt to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connectWebSocket()
        }, 2000) // Reconnect after 2 seconds
      })
      
      // Handle connection errors
      ws.addEventListener('error', (error) => {
        console.error('WebSocket error:', error)
        setFeedback('Connection error. Please check if the backend server is running.')
      })
    }
    
    // Initial connection
    connectWebSocket()
    
    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])
  
  // Function to send messages to the WebSocket server
  const sendMessage = (message: any) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected. Message not sent:', message)
      setFeedback('Cannot communicate with server. Please check your connection.')
    }
  }
  
  // Function to start a calibration process
  const startCalibration = (pose: string) => {
    setFeedback(`Calibrating ${pose} pose... Please hold the pose steady.`)
    sendMessage({
      action: 'calibrate',
      pose: pose
    })
  }
  
  // Function to start a pose session
  const startSession = (pose: string) => {
    setFeedback(`Starting session with ${pose}. Follow the reference pose on screen.`)
    sendMessage({
      action: 'startSession',
      pose: pose
    })
  }
  
  // Function to end a session
  const endSession = () => {
    setFeedback('Ending session. Great job!')
    sendMessage({
      action: 'endSession'
    })
  }
  
  // Function to change the active pose
  const changePose = (pose: string) => {
    setFeedback(`Changing to ${pose} pose. Please adjust your position.`)
    sendMessage({
      action: 'changePose',
      pose: pose
    })
  }
  
  return { 
    isConnected, 
    poseData, 
    lastMessage,
    lastEvent,
    feedback,
    sendMessage,
    startCalibration,
    startSession,
    endSession,
    changePose 
  }
} 