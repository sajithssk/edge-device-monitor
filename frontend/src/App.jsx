import React, { useState, useEffect } from 'react'
import DeviceCard from './components/DeviceCard'
import ConfigForm from './components/ConfigForm'
import useWebSocket from './hooks/useWebSocket'

const API_BASE = '/api'

function App() {
  const [devices, setDevices] = useState([])
  const [telemetry, setTelemetry] = useState({})
  const [configs, setConfigs] = useState({})
  const { lastMessage, readyState } = useWebSocket('ws://localhost:8000/ws')

  useEffect(() => {
    fetch(`${API_BASE}/devices`)
      .then(r => r.json())
      .then(data => {
        setDevices(data)
        const init = {}
        data.forEach(d => { init[d.id] = [] })
        setTelemetry(init)
        data.forEach(d => {
          fetch(`${API_BASE}/devices/${d.id}/config/latest`)
            .then(r => r.ok ? r.json() : null)
            .then(cfg => {
              if (cfg) setConfigs(prev => ({ ...prev, [d.id]: cfg }))
            })
            .catch(() => {})
        })
      })
  }, [])

  useEffect(() => {
    if (!lastMessage) return
      let msg
      try {
          msg = JSON.parse(lastMessage)
      } catch {
        return;
      }
    if (msg.type === 'telemetry') {
      setTelemetry(prev => {
        const arr = prev[msg.device_id] || []
        const next = [...arr, {
          ts: new Date(msg.ts),
          name: msg.metric_name,
          value: msg.metric_value,
        }].slice(-50)
        return { ...prev, [msg.device_id]: next }
      })
    } else if (msg.type === 'config_update') {
      fetch(`${API_BASE}/devices/${msg.device_id}/config/latest`)
        .then(r => r.json())
        .then(cfg => {
          setConfigs(prev => ({ ...prev, [msg.device_id]: cfg }))
        })
        .catch(() => {})
    }
  }, [lastMessage])

  const pushConfig = async (deviceId, config) => {
    const res = await fetch(`${API_BASE}/devices/${deviceId}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config }),
    })
    if (!res.ok) throw new Error('Failed to push config')
    const cfg = await res.json()
    setConfigs(prev => ({ ...prev, [deviceId]: cfg }))
    return cfg
  }

  return (
    <div style={{ padding: '2rem', maxWidth: 1200, margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: 0, color: '#38bdf8' }}>Edge Device Monitor</h1>
        <p style={{ color: '#94a3b8', marginTop: 8 }}>
          Connection: {readyState === 1 ? '🟢 Live' : readyState === 0 ? '🟡 Connecting...' : '🔴 Disconnected'}
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {devices.map(device => (
          <DeviceCard
            key={device.id}
            device={device}
            telemetry={telemetry[device.id] || []}
            config={configs[device.id]}
          />
        ))}
      </div>

      <ConfigForm devices={devices} onPush={pushConfig} />
    </div>
  )
}

export default App
