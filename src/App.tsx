import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  Bot,
  Aperture,
  Copy,
  KeyRound,
  Command,
  Cpu,
  Database,
  Globe,
  Layers3,
  MessageSquarePlus,
  Play,
  Shield,
  Trash2,
  TerminalSquare,
} from 'lucide-react';
import SplashScreen from './SplashScreen';

type TabId = 'overview' | 'chat' | 'access';

type StatusPayload = {
  name: string;
  provider: string;
  model: string;
  platform: string;
  memory_entries: number;
  autonomy_mode: string;
  interfaces: string[];
  capabilities: string[];
  default_runserver_address: string;
  updated_at: string;
};

type AccessKeyRecord = {
  id: number;
  name: string;
  prefix: string;
  platform_name: string;
  business_type: string;
  audience: string;
  tone: string;
  assistant_goal: string;
  custom_instructions: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
};

type Message = {
  id: string;
  role: 'user' | 'aida';
  text: string;
  sources?: Array<{ title: string; url: string }>;
};

type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
  lastActivity: string;
};

const quickPrompts = [
  'Menga bugungi ish uchun aniq plan tuzib ber.',
  'Kod va mahsulot sifati uchun 5 ta kuchli tavsiya ber.',
  'Murakkab vazifani qanday bo`lib ishlashni ayt.',
];

const tabs: Array<{ id: TabId; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }> = [
  { id: 'overview', label: 'Overview', icon: Layers3 },
  { id: 'chat', label: 'Chat', icon: Bot },
  { id: 'access', label: 'Access', icon: KeyRound },
];

function loadStoredSessions(): ChatSession[] {
  const stored = localStorage.getItem('aida_sessions');
  if (!stored) return [makeSession()];

  try {
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : [makeSession()];
  } catch {
    return [makeSession()];
  }
}

function makeSession(): ChatSession {
  return {
    id: crypto.randomUUID(),
    title: 'Yangi suhbat',
    messages: [
      {
        id: 'boot',
        role: 'aida',
        text: 'AIDA tayyor. Vazifani yozing, men uni tartibli, foydali va ishchi javobga aylantiraman.',
      },
    ],
    lastActivity: new Date().toISOString(),
  };
}

export default function App() {
  const [isBooting, setIsBooting] = useState(true);
  const [tab, setTab] = useState<TabId>('overview');
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [statusError, setStatusError] = useState('');

  // Multi-session state
  const [sessions, setSessions] = useState<ChatSession[]>(loadStoredSessions);
  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const storedActiveId = localStorage.getItem('aida_active_session');
    const storedSessions = loadStoredSessions();
    if (storedActiveId && storedSessions.some(session => session.id === storedActiveId)) {
      return storedActiveId;
    }
    return storedSessions[0]?.id ?? makeSession().id;
  });

  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [researchMode, setResearchMode] = useState(false);
  const [autoCopy, setAutoCopy] = useState(false);
  const [copiedId, setCopiedId] = useState('');
  const [keys, setKeys] = useState<AccessKeyRecord[]>([]);
  const [newKeyName, setNewKeyName] = useState('Platform key');
  const [platformName, setPlatformName] = useState('');
  const [businessType, setBusinessType] = useState('Kiyim do`koni');
  const [audience, setAudience] = useState('');
  const [tone, setTone] = useState('Iliq va ishonchli');
  const [assistantGoal, setAssistantGoal] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [newSecret, setNewSecret] = useState('');
  const [creatingKey, setCreatingKey] = useState(false);
  const feedRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find(s => s.id === activeSessionId) ?? sessions[0];
  const messages = activeSession?.messages ?? [];

  // Persist sessions to localStorage on every change
  useEffect(() => {
    localStorage.setItem('aida_sessions', JSON.stringify(sessions));
    localStorage.setItem('aida_active_session', activeSessionId);
  }, [sessions, activeSessionId]);

  useEffect(() => {
    const fetchBootstrap = async () => {
      try {
        const [statusResponse, keyResponse] = await Promise.all([
          fetch('/api/status/'),
          fetch('/api/keys/'),
        ]);
        if (!statusResponse.ok) throw new Error('Status endpoint unavailable');
        const statusPayload: StatusPayload = await statusResponse.json();
        setStatus(statusPayload);
        if (keyResponse.ok) {
          const keyPayload = await keyResponse.json();
          setKeys(keyPayload.items ?? []);
        }
        setStatusError('');
      } catch (error) {
        setStatusError(error instanceof Error ? error.message : 'Unknown status error');
      }
    };
    fetchBootstrap();
  }, []);

  useEffect(() => {
    feedRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  useEffect(() => {
    setAutoCopy(localStorage.getItem('aida_auto_copy') === 'true');
    setResearchMode(localStorage.getItem('aida_research_mode') === 'true');
  }, []);

  const updateSession = (id: string, updater: (s: ChatSession) => ChatSession) => {
    setSessions(prev => prev.map(s => s.id === id ? updater(s) : s));
  };

  const addNewSession = () => {
    const newSession = makeSession();
    setSessions(prev => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setTab('chat');
  };

  const deleteSession = (id: string) => {
    setSessions(prev => {
      const next = prev.filter(s => s.id !== id);
      if (next.length === 0) {
        const fresh = makeSession();
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      if (id === activeSessionId) {
        setActiveSessionId(next[0].id);
      }
      return next;
    });
  };

  const copyText = async (value: string, id: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(''), 1600);
    } catch {
      setCopiedId('');
    }
  };

  const sendPrompt = async (promptText?: string) => {
    const prompt = (promptText ?? input).trim();
    if (!prompt || sending) return;

    const userMessage: Message = { id: crypto.randomUUID(), role: 'user', text: prompt };

    // Derive session title from first user message
    const sessionTitle = activeSession.title === 'Yangi suhbat' ? prompt.slice(0, 40) : activeSession.title;

    updateSession(activeSessionId, s => ({
      ...s,
      title: sessionTitle,
      messages: [...s.messages, userMessage],
      lastActivity: new Date().toISOString(),
    }));
    setInput('');
    setSending(true);

    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, research: researchMode, session_id: activeSessionId }),
      });
      const payload = await response.json();

      if (!response.ok) throw new Error(payload.error || 'AIDA request failed');

      const aidaMessage: Message = {
        id: crypto.randomUUID(),
        role: 'aida',
        text: payload.message,
        sources: payload.sources ?? [],
      };
      updateSession(activeSessionId, s => ({
        ...s,
        messages: [...s.messages, aidaMessage],
        lastActivity: new Date().toISOString(),
      }));
      setStatus(payload.status);
      if (autoCopy && payload.message) await copyText(payload.message, 'auto-copy');
    } catch (error) {
      updateSession(activeSessionId, s => ({
        ...s,
        messages: [...s.messages, {
          id: crypto.randomUUID(),
          role: 'aida',
          text: `So'rovda uzilish bo'ldi: ${error instanceof Error ? error.message : 'unknown error'}`,
        }],
      }));
    } finally {
      setSending(false);
    }
  };

  const stats = [
    { label: 'Provider', value: status?.provider ?? 'loading', icon: Cpu, tone: 'mint' },
    { label: 'Platform', value: status?.platform ?? 'loading', icon: Globe, tone: 'amber' },
    { label: 'Memory', value: String(status?.memory_entries ?? 0), icon: Database, tone: 'ice' },
    { label: 'Mode', value: status?.autonomy_mode ?? 'guarded', icon: Shield, tone: 'rose' },
  ];

  const createKey = async () => {
    if (!newKeyName.trim() || creatingKey) return;
    setCreatingKey(true);
    try {
      const response = await fetch('/api/keys/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newKeyName, platform_name: platformName, business_type: businessType, audience, tone, assistant_goal: assistantGoal, custom_instructions: customInstructions }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Key create failed');
      setNewSecret(payload.secret);
      setKeys(c => [{ id: payload.id, name: payload.name, prefix: payload.prefix, platform_name: payload.platform_name, business_type: payload.business_type, audience: payload.audience, tone: payload.tone, assistant_goal: payload.assistant_goal, custom_instructions: payload.custom_instructions, created_at: payload.created_at, last_used_at: null, is_active: true }, ...c]);
      setPlatformName(''); setBusinessType('Kiyim do`koni'); setAudience(''); setTone('Iliq va ishonchli'); setAssistantGoal(''); setCustomInstructions('');
    } finally {
      setCreatingKey(false);
    }
  };

  const handleAutoCopyChange = (v: boolean) => { setAutoCopy(v); localStorage.setItem('aida_auto_copy', String(v)); };
  const handleResearchChange = (v: boolean) => { setResearchMode(v); localStorage.setItem('aida_research_mode', String(v)); };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <AnimatePresence mode="wait">
        {isBooting ? (
          <SplashScreen onComplete={() => setIsBooting(false)} />
        ) : (
          <motion.div
            key="shell"
            className="shell-grid min-h-screen"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1 }}
          >
            {/* SIDEBAR */}
            <aside className="sidebar">
              <div>
                <div className="eyebrow">AIDA System</div>
                <h1 className="brand">AIDA</h1>
                <p className="sidebar-copy">
                  Kuchli kirish, toza boshqaruv va tezkor fikrlash uchun yig'ilgan markaziy ish paneli.
                </p>
              </div>

              <nav className="nav-stack" aria-label="Sections">
                {tabs.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setTab(item.id)}
                    className={`nav-button ${tab === item.id ? 'nav-button-active' : ''}`}
                  >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                  </button>
                ))}
              </nav>

              {/* CHAT SESSIONS LIST */}
              <div className="sessions-panel">
                <div className="sessions-header">
                  <span className="eyebrow" style={{ margin: 0 }}>Suhbatlar</span>
                  <button
                    type="button"
                    className="new-session-btn"
                    onClick={addNewSession}
                    title="Yangi suhbat"
                  >
                    <MessageSquarePlus size={16} />
                  </button>
                </div>
                <div className="sessions-list">
                  {sessions.map(s => (
                    <div
                      key={s.id}
                      className={`session-item ${s.id === activeSessionId ? 'session-item-active' : ''}`}
                      onClick={() => { setActiveSessionId(s.id); setTab('chat'); }}
                    >
                      <span className="session-title">{s.title}</span>
                      <button
                        type="button"
                        className="session-delete"
                        onClick={(e) => { e.stopPropagation(); deleteSession(s.id); }}
                        title="O'chirish"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="sidebar-foot">
                <div className="foot-kicker">Deploy</div>
                <div className="foot-copy">
                  Django API backendda ishlaydi. Frontend build tayyor bo'lsa shu panelni serve qiladi.
                </div>
              </div>
            </aside>

            {/* MAIN */}
            <main className="main-panel">
              <header className="topbar">
                <div>
                  <div className="eyebrow">Operational View</div>
                  <div className="topbar-title">{status?.name ?? 'AIDA booting'}</div>
                </div>
                <div className="topbar-meta">
                  <span className="status-pill"><Cpu size={14} />{status?.provider ?? 'local-core'}</span>
                  <span className="status-pill"><TerminalSquare size={14} />{status?.default_runserver_address ?? '127.0.0.1:8001'}</span>
                </div>
              </header>

              <AnimatePresence mode="wait">
                {tab === 'overview' && (
                  <motion.section key="overview" className="view" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
                    <section className="hero-band">
                      <motion.div className="hero-copy" initial="initial" animate="animate" variants={{ initial: { opacity: 0 }, animate: { opacity: 1, transition: { staggerChildren: 0.08, delayChildren: 0.1 } } }}>
                        <motion.div className="hero-badge" variants={{ initial: { opacity: 0, scale: 0.8 }, animate: { opacity: 1, scale: 1, transition: { duration: 0.5 } } }}>
                          <Aperture size={14} /><span>AIDA online</span>
                        </motion.div>
                        <motion.div className="hero-wordmark" variants={{ initial: { opacity: 0, y: 30 }, animate: { opacity: 1, y: 0, transition: { duration: 0.8 } } }}>AIDA</motion.div>
                        <motion.h2 variants={{ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0, transition: { duration: 0.6 } } }}>
                          Kirishingiz bilan tayyor turadigan chiroyli va aniq sun'iy ong paneli.
                        </motion.h2>
                        <motion.p variants={{ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0, transition: { duration: 0.6 } } }}>
                          Birinchi ekranning o'zida brend, holat va ishga kirish nuqtalari ko'rinadi. AIDA esa local core sifatida javoblarni tartibli va foydali shaklda tayyorlaydi.
                        </motion.p>
                        <motion.div className="hero-signals" variants={{ initial: { opacity: 0, y: 15 }, animate: { opacity: 1, y: 0, transition: { duration: 0.5 } } }}>
                          <span>Local core</span><span>Fast response</span><span>Memory active</span>
                          <span>{sessions.length} ta suhbat</span>
                        </motion.div>
                      </motion.div>
                      <motion.div className="hero-visual" aria-hidden="true" initial={{ opacity: 0, scale: 0.8, rotate: -5 }} animate={{ opacity: 1, scale: 1, rotate: 0 }} transition={{ duration: 1.2, delay: 0.3 }}>
                        <div className="visual-grid">
                          <div className="visual-plaque">
                            <div className="visual-plaque-label">AIDA Presence</div>
                            <div className="visual-plaque-title">AIDA</div>
                            <div className="visual-plaque-copy">Tizim markazi ishga tayyor.</div>
                          </div>
                        </div>
                        <div className="visual-core"><Command size={46} /></div>
                        <div className="visual-ring visual-ring-a" />
                        <div className="visual-ring visual-ring-b" />
                      </motion.div>
                    </section>

                    <section className="stats-grid">
                      {stats.map((item, i) => (
                        <motion.article key={item.label} className={`stat-card tone-${item.tone}`} initial={{ opacity: 0, y: 20, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 0.6, delay: 0.4 + i * 0.1 }}>
                          <item.icon size={18} />
                          <div className="stat-label">{item.label}</div>
                          <div className="stat-value">{item.value}</div>
                        </motion.article>
                      ))}
                    </section>

                    <section className="detail-grid">
                      <article className="detail-panel">
                        <div className="panel-kicker">Capabilities</div>
                        <div className="cap-list">
                          {(status?.capabilities ?? []).map(c => <span key={c} className="cap-chip">{c}</span>)}
                        </div>
                      </article>
                      <article className="detail-panel">
                        <div className="panel-kicker">Focus mode</div>
                        <p className="panel-copy">Javoblar foydali, aniq va operatsion usulda beriladi. Ortiqcha ichki texnik tafsilotlar foydalanuvchi ekraniga chiqarilmaydi.</p>
                      </article>
                      <article className="detail-panel">
                        <div className="panel-kicker">Runserver memory</div>
                        <p className="panel-copy">
                          {statusError ? `Status xatosi: ${statusError}` : `Default manzil: ${status?.default_runserver_address ?? '127.0.0.1:8001'}`}
                        </p>
                      </article>
                    </section>
                  </motion.section>
                )}

                {tab === 'chat' && (
                  <motion.section key={`chat-${activeSessionId}`} className="view chat-view" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
                    <section className="chat-column">
                      <div className="chat-head">
                        <div>
                          <div className="eyebrow">Interactive Session</div>
                          <h2>{activeSession?.title ?? 'AIDA bilan ishlash'}</h2>
                        </div>
                        <div className="chat-controls">
                          <label className="switch-row">
                            <input type="checkbox" checked={researchMode} onChange={e => handleResearchChange(e.target.checked)} />
                            <span>Internet research</span>
                          </label>
                          <label className="switch-row">
                            <input type="checkbox" checked={autoCopy} onChange={e => handleAutoCopyChange(e.target.checked)} />
                            <span>Auto-copy</span>
                          </label>
                          <button type="button" className="quick-button" onClick={addNewSession}>
                            <MessageSquarePlus size={14} style={{ display: 'inline', marginRight: 6 }} />
                            Yangi suhbat
                          </button>
                        </div>
                        <div className="quick-row">
                          {quickPrompts.map(p => (
                            <button key={p} type="button" className="quick-button" onClick={() => sendPrompt(p)}>{p}</button>
                          ))}
                        </div>
                      </div>

                      <div className="chat-feed">
                        {messages.map(message => (
                          <div key={message.id} className={`message-row ${message.role === 'user' ? 'message-user' : 'message-aida'}`}>
                            <div className="message-meta-row">
                              <div className="message-meta">
                                {message.role === 'user' ? <Play size={12} /> : <Bot size={12} />}
                                <span>{message.role === 'user' ? 'Operator' : 'AIDA'}</span>
                              </div>
                              {message.role === 'aida' && (
                                <button type="button" className="copy-button" onClick={() => copyText(message.text, message.id)}>
                                  <Copy size={12} />
                                  <span>{copiedId === message.id ? 'Copied' : 'Copy'}</span>
                                </button>
                              )}
                            </div>
                            <div className="message-bubble" style={{ whiteSpace: 'pre-wrap' }}>{message.text}</div>
                            {!!message.sources?.length && (
                              <div className="source-list">
                                {message.sources.map(src => (
                                  <a key={src.url} href={src.url} target="_blank" rel="noreferrer">{src.title}</a>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                        {sending && (
                          <div className="message-row message-aida">
                            <div className="message-meta"><Bot size={12} /><span>AIDA</span></div>
                            <div className="message-bubble typing-indicator">
                              <span /><span /><span />
                            </div>
                          </div>
                        )}
                        <div ref={feedRef} />
                      </div>

                      <form className="composer" onSubmit={e => { e.preventDefault(); sendPrompt(); }}>
                        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Masalan: bugungi backend ishini 4 qismga bo`l" />
                        <button type="submit" disabled={sending || !input.trim()}>Yuborish</button>
                      </form>
                    </section>
                  </motion.section>
                )}

                {tab === 'access' && (
                  <motion.section key="access" className="view architecture-view" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
                    <section className="architecture-band">
                      <article className="arch-step"><div className="arch-index">01</div><h3>Local core</h3><p>AIDA default holatda local core rejimida ishlaydi va tashqi modelga bog'lanmaydi.</p></article>
                      <article className="arch-step"><div className="arch-index">02</div><h3>Saved address</h3><p>Oxirgi ishlatilgan `runserver` manzili eslab qolinadi va keyingi safar o'sha port ochiladi.</p></article>
                      <article className="arch-step"><div className="arch-index">03</div><h3>Access key</h3><p>Bu yerda yaratilgan key bilan boshqa platforma sizning AIDA endpoint'ingizga ulanadi.</p></article>
                      <article className="arch-step"><div className="arch-index">04</div><h3>External endpoint</h3><p>`/api/platform/chat/` orqali platformalararo chat oqimi ishlaydi.</p></article>
                    </section>
                    <section className="detail-grid">
                      <article className="detail-panel">
                        <div className="panel-kicker">Create access key</div>
                        <div className="key-create-block">
                          <input value={newKeyName} onChange={e => setNewKeyName(e.target.value)} placeholder="Key nomi" />
                          <input value={platformName} onChange={e => setPlatformName(e.target.value)} placeholder="Platforma nomi" />
                          <input value={businessType} onChange={e => setBusinessType(e.target.value)} placeholder="Business type" />
                          <input value={audience} onChange={e => setAudience(e.target.value)} placeholder="Auditoriya" />
                          <input value={tone} onChange={e => setTone(e.target.value)} placeholder="Javob ohangi" />
                          <input value={assistantGoal} onChange={e => setAssistantGoal(e.target.value)} placeholder="Assistant goal" />
                          <textarea value={customInstructions} onChange={e => setCustomInstructions(e.target.value)} placeholder="Maxsus ko'rsatmalar" />
                          <button type="button" onClick={createKey} disabled={creatingKey || !newKeyName.trim()}>
                            {creatingKey ? 'Yaratilmoqda...' : 'Key yaratish'}
                          </button>
                        </div>
                        {newSecret && (
                          <div className="secret-box">
                            <div className="panel-kicker">Yangi secret</div>
                            <code>{newSecret}</code>
                          </div>
                        )}
                      </article>
                      <article className="detail-panel">
                        <div className="panel-kicker">Platform ulanish</div>
                        <p className="panel-copy">Endpoint: <code>/api/platform/chat/</code><br />Header: <code>X-AIDA-Key: sizning_secret</code></p>
                      </article>
                      <article className="detail-panel">
                        <div className="panel-kicker">Mavjud keylar</div>
                        <div className="key-list">
                          {keys.length === 0 && <p className="panel-copy">Hali access key yaratilmagan.</p>}
                          {keys.map(item => (
                            <div key={item.id} className="key-item">
                              <div className="key-item-head"><KeyRound size={14} /><span>{item.name}</span></div>
                              <div className="key-item-meta"><span>{item.prefix}...</span><span>{item.last_used_at ? 'used' : 'new'}</span></div>
                              <div className="key-item-profile">
                                <span>{item.platform_name || 'Platforma yo`q'}</span>
                                <span>{item.business_type || 'Umumiy'}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </article>
                    </section>
                  </motion.section>
                )}
              </AnimatePresence>
            </main>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
