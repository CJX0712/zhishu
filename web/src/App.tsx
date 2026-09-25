import { useState } from 'react'

type Citation = { index: number; source: string; text: string }
type Msg = {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export default function App() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<'rag' | 'agent'>('rag')
  const [loading, setLoading] = useState(false)

  async function send() {
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      const resp = await fetch(`/api/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })
      const data = await resp.json()
      const ans: Msg = { role: 'assistant', content: data.answer ?? JSON.stringify(data) }
      if (data.citations) ans.citations = data.citations
      setMessages((m) => [...m, ans])
    } catch (e: any) {
      setMessages((m) => [...m, { role: 'assistant', content: '请求失败: ' + e.message }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>智枢 ZhiShu</h1>
        <div className="modes">
          <button className={mode === 'rag' ? 'on' : ''} onClick={() => setMode('rag')}>
            RAG 问答
          </button>
          <button className={mode === 'agent' ? 'on' : ''} onClick={() => setMode('agent')}>
            Agent 推理
          </button>
        </div>
      </header>

      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={'msg ' + m.role}>
            <div className="bubble">{m.content}</div>
            {m.citations && m.citations.length > 0 && (
              <div className="cites">
                {m.citations.map((c) => (
                  <div key={c.index} className="cite">
                    [{c.index}] {c.source}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="msg assistant">
            <div className="bubble">思考中…</div>
          </div>
        )}
      </div>

      <div className="input">
        <input
          value={input}
          placeholder="输入问题，回车发送"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') send()
          }}
        />
        <button onClick={send} disabled={loading}>
          发送
        </button>
      </div>
    </div>
  )
}
