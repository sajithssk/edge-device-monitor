import React, { useState } from 'react'

export default function ConfigForm({ devices, onPush }) {
  const [selectedDevice, setSelectedDevice] = useState('')
  const [configJson, setConfigJson] = useState('{\n  "sampling_rate_ms": 2000,\n  "threshold": 75.5\n}')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedDevice) return
    let config
    try {
      config = JSON.parse(configJson)
    } catch {
      setStatus({ type: 'error', text: 'Invalid JSON' })
      return
    }
    setLoading(true)
    setStatus({ type: 'info', text: 'Pushing...' })
    try {
      const start = performance.now()
      await onPush(selectedDevice, config)
      const elapsed = (performance.now() - start).toFixed(0)
      setStatus({ type: 'success', text: `Config pushed! HTTP round-trip: ${elapsed}ms (pending device ack)` })
    } catch (err) {
      setStatus({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      marginTop: '2rem',
      background: '#1e293b',
      borderRadius: 12,
      padding: '1.5rem',
      border: '1px solid #334155',
    }}>
      <h3 style={{ marginTop: 0, color: '#f8fafc' }}>Push Configuration</h3>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: 6, color: '#94a3b8', fontSize: 14 }}>Device</label>
          <select
            value={selectedDevice}
            onChange={e => setSelectedDevice(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 6,
              border: '1px solid #475569',
              background: '#0f172a',
              color: '#e2e8f0',
              fontSize: 14,
            }}
          >
            <option value="">Select device...</option>
            {devices.map(d => (
              <option key={d.id} value={d.id}>{d.name} ({d.id})</option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: 6, color: '#94a3b8', fontSize: 14 }}>Config JSON</label>
          <textarea
            value={configJson}
            onChange={e => setConfigJson(e.target.value)}
            rows={5}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 6,
              border: '1px solid #475569',
              background: '#0f172a',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: 13,
            }}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !selectedDevice}
          style={{
            padding: '10px 20px',
            borderRadius: 6,
            border: 'none',
            background: '#0ea5e9',
            color: '#fff',
            fontWeight: 600,
            cursor: 'pointer',
            opacity: loading || !selectedDevice ? 0.6 : 1,
          }}
        >
          {loading ? 'Pushing...' : 'Push Config'}
        </button>

        {status && (
          <div style={{
            marginTop: '1rem',
            padding: '10px 14px',
            borderRadius: 6,
            fontSize: 14,
            background: status.type === 'error' ? '#450a0a' : status.type === 'success' ? '#064e3b' : '#1e3a8a',
            color: status.type === 'error' ? '#f87171' : status.type === 'success' ? '#4ade80' : '#93c5fd',
          }}>
            {status.text}
          </div>
        )}
      </form>
    </div>
  )
}
