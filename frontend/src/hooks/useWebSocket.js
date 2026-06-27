import { useEffect, useRef, useState, useCallback } from 'react'

export default function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null)
  const [readyState, setReadyState] = useState(WebSocket.CONNECTING)
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return

    const wsUrl = url.startsWith('ws://') || url.startsWith('wss://')
        ? url
        : 'ws://localhost:8000' + url
    const socket = new WebSocket(wsUrl)
    ws.current = socket

    socket.onopen = () => {
      setReadyState(WebSocket.OPEN)
      socket.send(JSON.stringify({ type: 'frontend' }))
    }

    socket.onmessage = (event) => {
      setLastMessage(event.data)
    }

    socket.onclose = () => {
      setReadyState(WebSocket.CLOSED)
      ws.current = null
      reconnectTimeout.current = setTimeout(connect, 3000)
    }

    socket.onerror = () => socket.close()
  }, [url])

  useEffect(() => {
    connect()
    const interval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send('ping')
      }
    }, 15000)
    return () => {
      clearInterval(interval)
      clearTimeout(reconnectTimeout.current)
      if (ws.current) ws.current.close()
    }
  }, [connect])

  const sendMessage = useCallback((msg) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
  }, [])

  return { lastMessage, sendMessage, readyState }
}
