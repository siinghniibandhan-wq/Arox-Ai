import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const initialMessages = [{ role: 'assistant', text: 'Welcome to KPMC AI. Connect your backend to start chatting. Choose Auto for free-first routing, or select a configured provider.' }];
function App() {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('kpmc-api-url') || '');
  const [token, setToken] = useState('');
  const [provider, setProvider] = useState('auto');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState(initialMessages);
  const [busy, setBusy] = useState(false);
  const [providers, setProviders] = useState([]);
  const [notice, setNotice] = useState('Backend not connected');
  const [showSettings, setShowSettings] = useState(true);

  const base = apiUrl.trim().replace(/\/$/, '');
  async function connect() {
    if (!base || !token.trim()) { setNotice('Enter your backend URL and access token.'); return; }
    localStorage.setItem('kpmc-api-url', base);
    try {
      const res = await fetch(`${base}/api/providers`, { headers: { Authorization: `Bearer ${token.trim()}` } });
      if (!res.ok) throw new Error(`Connection failed (${res.status})`);
      const data = await res.json(); setProviders(data.providers || []); setNotice('Backend connected'); setShowSettings(false);
    } catch (e) { setNotice(`${e.message}. Check URL, token and backend CORS settings.`); }
  }
  async function send(e) {
    e?.preventDefault(); const text = message.trim();
    if (!text || busy) return;
    if (!base || !token.trim()) { setNotice('Connect your backend first in Settings.'); setShowSettings(true); return; }
    setMessages(prev => [...prev, { role: 'user', text }]); setMessage(''); setBusy(true);
    try {
      const res = await fetch(`${base}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token.trim()}` }, body: JSON.stringify({ message: text, provider }) });
      const data = await res.json(); if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
      setMessages(prev => [...prev, { role: 'assistant', text: data.reply, provider: data.provider }]);
    } catch (err) { setMessages(prev => [...prev, { role: 'error', text: `${err.message}. Confirm the selected provider is configured on your backend.` }]); }
    finally { setBusy(false); }
  }
  return <div className="shell">
    <aside className="sidebar"><div className="brand"><div className="logo">K</div><div><strong>KPMC AI</strong><small>One AI workspace</small></div></div>
      <button className="nav active">✦ <span>AI Chat</span></button><button className="nav" onClick={() => setProvider('auto')}>⌘ <span>Smart Routing</span></button><button className="nav" onClick={() => setNotice('GodMode multi-model orchestration is planned; it is not connected yet.')}>◈ <span>GodMode</span><em>Planned</em></button><button className="nav" onClick={() => setNotice('Provider status comes from your connected backend.')}>◎ <span>Providers</span></button>
      <div className="sidebar-bottom"><div className="status-dot"/><span>{notice}</span><button className="icon-btn" title="Settings" onClick={() => setShowSettings(!showSettings)}>⚙</button></div>
    </aside>
    <main className="main"><header><div><div className="eyebrow">YOUR AI WORKSPACE</div><h1>What can we build today?</h1><p>One interface. Multiple AI providers. Your choice of model.</p></div><button className="settings-btn" onClick={() => setShowSettings(!showSettings)}>⚙ Settings</button></header>
      {showSettings && <section className="settings panel"><div className="panel-title"><div><h2>Connect your backend</h2><p>API keys stay on your server. Never paste provider keys here.</p></div><span className="badge">Setup</span></div><div className="form-grid"><label>Backend base URL<input value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="https://your-ec2-domain.example" /></label><label>AROX access token<input type="password" value={token} onChange={e => setToken(e.target.value)} placeholder="Bearer token value" autoComplete="off" /></label></div><div className="settings-actions"><span>{notice}</span><button className="primary" onClick={connect}>Connect backend ↗</button></div></section>}
      <section className="toolbar"><div><span className="label">MODEL ROUTING</span><select value={provider} onChange={e => setProvider(e.target.value)}><option value="auto">Auto · Free-first</option><option value="freellmapi">FreeLLMAPI</option><option value="omniroute">OmniRoute</option><option value="claude">Claude</option><option value="openai">OpenAI</option></select></div><div className="provider-chips">{providers.length ? providers.map(p => <span key={p.id} className={`chip ${p.configured ? 'ready' : ''}`}><i/> {p.id}</span>) : <span className="chip">Connect to see providers</span>}</div></section>
      <section className="chat panel"><div className="chat-head"><div><h2>Conversation</h2><p>Ask, explore, code and create.</p></div><button className="clear-btn" onClick={() => setMessages(initialMessages)}>New chat ＋</button></div><div className="messages">{messages.map((m, i) => <div key={i} className={`message ${m.role}`}><div className="avatar">{m.role === 'user' ? 'Y' : m.role === 'error' ? '!' : 'K'}</div><div className="bubble"><div className="message-meta">{m.role === 'user' ? 'YOU' : m.role === 'error' ? 'NOTICE' : `KPMC AI${m.provider ? ` · ${m.provider}` : ''}`}</div><div className="message-text">{m.text}</div></div></div>)}{busy && <div className="message assistant"><div className="avatar">K</div><div className="bubble"><div className="message-meta">KPMC AI</div><div className="dots"><i/><i/><i/></div></div></div>}</div><form className="composer" onSubmit={send}><textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="Message KPMC AI…" rows="2" onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }} /><div className="composer-bottom"><span>Enter to send · Shift + Enter for new line</span><button className="primary send" disabled={busy || !message.trim()}>{busy ? 'Working…' : 'Send ↑'}</button></div></form></section>
      <footer>Built for KPMC Enterprises <span>•</span> Provider availability and free-tier limits vary.</footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
