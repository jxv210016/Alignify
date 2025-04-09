'use client'

import { useEffect, useRef, useState } from 'react'
import useWebSocket from 'react-use-websocket'

interface Landmark {
  x: number
  y: number
  z: number
  visibility: number
}

interface PoseData {
  type: string
  landmarks?: { [key: string]: Landmark }
  timestamp: string
}

const POSES = [
  { name: 'Warrior 1', image: '/poses/warrior1.png' },
  { name: 'Warrior 2', image: '/poses/warrior2.png' },
  { name: 'Star', image: '/poses/star.png' },
  { name: 'Goddess', image: '/poses/goddess.png' },
]

export default function YogaInterface() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isCalibrating, setIsCalibrating] = useState(false)
  const [currentPose, setCurrentPose] = useState(0)
  const [phase, setPhase] = useState<'welcome' | 'calibration' | 'session'>('welcome')
  const [feedback, setFeedback] = useState('')

  const { sendMessage, lastMessage } = useWebSocket('ws://localhost:8000/ws/pose', {
    shouldReconnect: () => true,
  })

  useEffect(() => {
    if (lastMessage) {
      const data: PoseData = JSON.parse(lastMessage.data)
      if (data.type === 'pose_data' && data.landmarks) {
        // Process pose data and provide feedback
        processPoseData(data.landmarks)
      }
    }
  }, [lastMessage])

  useEffect(() => {
    if (phase === 'calibration' || phase === 'session') {
      startCamera()
    }
  }, [phase])

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      startPoseDetection()
    } catch (error) {
      console.error('Error accessing camera:', error)
    }
  }

  const startPoseDetection = () => {
    if (!videoRef.current || !canvasRef.current) return

    const detectPose = () => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState !== 4) {
        requestAnimationFrame(detectPose)
        return
      }

      const context = canvas.getContext('2d')
      if (!context) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      // Draw video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height)

      // Convert canvas to base64
      const imageData = canvas.toDataURL('image/jpeg', 0.5)
      
      // Send to backend
      sendMessage(JSON.stringify({ image: imageData }))

      requestAnimationFrame(detectPose)
    }

    requestAnimationFrame(detectPose)
  }

  const processPoseData = (landmarks: { [key: string]: Landmark }) => {
    // Implement pose comparison and feedback logic
    // This will be similar to the Python implementation
    setFeedback('Processing pose...')
  }

  const startCalibration = () => {
    setPhase('calibration')
    setIsCalibrating(true)
    setCurrentPose(0)
  }

  const startSession = () => {
    setPhase('session')
    setIsCalibrating(false)
    setCurrentPose(0)
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8">Alignify</h1>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Video Feed */}
        <div className="flex-1">
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="absolute inset-0 w-full h-full object-cover"
            />
            <canvas
              ref={canvasRef}
              className="absolute inset-0 w-full h-full"
              style={{ display: 'none' }}
            />
          </div>
        </div>

        {/* Controls and Info Panel */}
        <div className="flex-1 bg-white p-6 rounded-lg shadow-lg">
          {phase === 'welcome' ? (
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-4">Welcome to Alignify</h2>
              <p className="mb-8">Your personal yoga pose alignment assistant</p>
              <button
                onClick={startCalibration}
                className="bg-blue-500 text-white px-8 py-3 rounded-full hover:bg-blue-600 transition-colors"
              >
                Begin
              </button>
            </div>
          ) : phase === 'calibration' ? (
            <div>
              <h2 className="text-2xl font-semibold mb-4">Calibration</h2>
              <p className="mb-4">Current Pose: {POSES[currentPose].name}</p>
              <div className="mb-4">
                <img
                  src={POSES[currentPose].image}
                  alt={POSES[currentPose].name}
                  className="w-full max-w-sm mx-auto rounded-lg"
                />
              </div>
              <p className="text-gray-600">{feedback}</p>
            </div>
          ) : (
            <div>
              <h2 className="text-2xl font-semibold mb-4">Yoga Session</h2>
              <p className="mb-4">Current Pose: {POSES[currentPose].name}</p>
              <p className="text-gray-600">{feedback}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 