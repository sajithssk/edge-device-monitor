import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function DeviceCard({ device, telemetry, config }) {
  const timeMap = {}
  telemetry.forEach(t => {
    const key = t.ts.toLocaleTimeString()
    if (!timeMap[key]) timeMap[key] = { time: key }
    timeMap[key][t.name] = t.value
  })
  const chartData = Object.values(timeMap)
  const metricNames = [...new Set(telemetry.map(t => t.name))]
  const colors = ['#38bdf8', '#4ade80', '#f472b6', '#fbbf24']

  return (
    <div style={{
      background: '#1e293b',
      borderRadius: 12,
      padding: '1.5rem',
      border: '1px solid #334155',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ margin: 0, color: '#f8fafc' }}>{device.name}</h3>
          <code style={{ color: '#94a3b8', fontSize: 12 }}>{device.id}</code>
        </div>
        {config && (
          <div style={{
            padding: '4px 10px',
            borderRadius: 20,
            fontSize: 12,
            fontWeight: 600,
            background: config.state === 'applied' ? '#064e3b' : config.state === 'pending' ? '#713f12' : '#450a0a',
            color: config.state === 'applied' ? '#4ade80' : config.state === 'pending' ? '#fbbf24' : '#f87171',
          }}>
            {config.state.toUpperCase()}
          </div>
        )}
      </div>

      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
            <YAxis stroke="#94a3b8" fontSize={12} />
            <Tooltip
              contentStyle={{ background: '#0f172a', border: '1px solid #334155' }}
              labelStyle={{ color: '#94a3b8' }}
            />
            <Legend />
            {metricNames.map((name, i) => (
              <Line
                key={name}
                type="monotone"
                dataKey={name}
                stroke={colors[i % colors.length]}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {config && (
        <div style={{ marginTop: '1rem', fontSize: 13, color: '#94a3b8' }}>
          <strong>Latest Config:</strong> {config.config_payload}
          {config.applied_at && (
            <div style={{ fontSize: 11, marginTop: 4 }}>
              Applied at {new Date(config.applied_at).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
