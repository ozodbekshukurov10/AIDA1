import React, { useEffect, useRef, useState } from 'react';
<<<<<<< HEAD
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
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    const stored = localStorage.getItem('aida_sessions');
    if (stored) {
      try { return JSON.parse(stored); } catch { /* ignore */ }
    }
    return [makeSession()];
  });
  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const stored = localStorage.getItem('aida_sessions');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        return parsed[0]?.id ?? crypto.randomUUID();
      } catch { /* ignore */ }
    }
    return sessions[0]?.id ?? '';
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
          <SplashScreen key="splash" onComplete={() => setIsBooting(false)} />
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
=======
import { motion, AnimatePresence } from 'motion/react';
import {
  Activity,
  BookOpen,
  Brain,
  Database,
  Fingerprint,
  Globe,
  Lock,
  MessageSquare,
  Search,
  ShieldAlert,
  Terminal,
  X,
} from 'lucide-react';

interface MessageRecord {
  id: string;
  text: string;
  sender: 'user' | 'aida';
}

interface CommandRecord {
  id: string;
  command: string;
  output: string;
}

interface MemorySummary {
  id: string;
  kind: 'conversation' | 'knowledge' | 'reflection';
  title: string;
  content: string;
  source?: string;
}

type EmotionType = 'mehribonlik' | 'gazab' | 'hursandchilik' | 'sevgi' | 'nafrat' | 'masuliyat';

interface EmotionState {
  mehribonlik: number;
  gazab: number;
  hursandchilik: number;
  sevgi: number;
  nafrat: number;
  masuliyat: number;
  dominant: EmotionType;
  description: string;
}

interface SystemState {
  memoryCount: number;
  knowledgeCount: number;
  lastLearnedTopic: string | null;
  autoLearnEnabled: boolean;
  internetResearchEnabled: boolean;
  localModelEnabled: boolean;
  profile: {
    name: string;
    description: string;
  };
  emotions?: EmotionState;
}

const initialState: SystemState = {
  memoryCount: 0,
  knowledgeCount: 0,
  lastLearnedTopic: null,
  autoLearnEnabled: false,
  internetResearchEnabled: false,
  localModelEnabled: false,
  profile: {
    name: 'AIDA',
    description: 'Bulut xotira ulanmoqda...',
  },
};

async function readJsonSafely<T>(response: Response): Promise<T | null> {
  const raw = await response.text();

  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/html')) {
      throw new Error('Server JSON o‘rniga HTML qaytardi.');
    }
    throw new Error('Serverdan noto‘liq yoki yaroqsiz JSON keldi.');
  }
}

export default function App() {
  const [view, setView] = useState<'core' | 'terminal' | 'chat'>('core');
  const [commands, setCommands] = useState<CommandRecord[]>([]);
  const [cmdInput, setCmdInput] = useState('');
  const [messages, setMessages] = useState<MessageRecord[]>([
    {
      id: 'boot',
      text: "AIDA onlayn. Xotira, learning va research yadro sinxronlashmoqda. Buyruq bering.",
      sender: 'aida',
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessingCmd, setIsProcessingCmd] = useState(false);
  const [systemState, setSystemState] = useState<SystemState>(initialState);
  const [memoryPreview, setMemoryPreview] = useState<MemorySummary[]>([]);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [coreColor, setCoreColor] = useState('#10b981');
  const [isAdapting, setIsAdapting] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const terminalEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (view === 'terminal') {
      terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    if (view === 'chat') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [commands, messages, view, isTyping, isProcessingCmd]);

  useEffect(() => {
    void refreshState();
    void refreshMemory();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (systemState.memoryCount > 0) {
        setIsAdapting(true);
        setCoreColor((prev) => (prev === '#10b981' ? '#06b6d4' : '#10b981'));
        setTimeout(() => setIsAdapting(false), 1800);
      }
    }, 12000);

    return () => clearInterval(interval);
  }, [systemState.memoryCount]);

  useEffect(() => {
    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setCameraActive(true);
        setCameraError(null);
      } catch (error: any) {
        setCameraActive(false);
        if (error?.name === 'NotAllowedError') {
          setCameraError("Kameraga ruxsat berilmadi.");
        } else if (error?.name === 'NotFoundError') {
          setCameraError("Kamera topilmadi.");
        } else {
          setCameraError("Kameraga ulanishda xatolik.");
        }
      }
    }

    void setupCamera();
  }, []);

  async function refreshState() {
    try {
      const response = await fetch('/api/state');
      if (!response.ok) {
        return null;
      }
      const data = await readJsonSafely<SystemState>(response);
      if (data) {
        setSystemState(data);
        return data;
      }
    } catch {
      // UI fallback state keeps the app usable even if the API is offline.
    }

    return null;
  }

  async function refreshMemory() {
    try {
      const response = await fetch('/api/memory');
      if (!response.ok) {
        return;
      }
      const data = await readJsonSafely<MemorySummary[]>(response);
      if (data) {
        setMemoryPreview(data.slice(0, 5));
      }
    } catch {
      // Ignore preview errors to avoid interrupting the main UI.
    }
  }

  async function sendMessage(message: string, channel: 'chat' | 'terminal') {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, channel }),
    });

    const data = await readJsonSafely<{
      reply?: string;
      state?: SystemState;
      error?: string;
    }>(response);

    if (!response.ok) {
      throw new Error(data?.error || 'AIDA javob bera olmadi.');
    }

    if (!data) {
      throw new Error('Server bo‘sh javob qaytardi.');
    }

    if (data.state) {
      setSystemState(data.state);
    }

    void refreshMemory();
    return data.reply || 'Javob bo‘sh qaytdi.';
  }

  async function learnTopic(topic: string) {
    const response = await fetch('/api/learn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });

    const data = await readJsonSafely<{
      learned?: MemorySummary;
      state?: SystemState;
      error?: string;
    }>(response);

    if (!response.ok) {
      throw new Error(data?.error || 'Learning muvaffaqiyatsiz tugadi.');
    }

    if (!data) {
      throw new Error('Server bo‘sh javob qaytardi.');
    }

    if (data.state) {
      setSystemState(data.state);
    }

    void refreshMemory();
    return data.learned;
  }

  async function runResearch(query: string) {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const data = await readJsonSafely<{
      report?: {
        query: string;
        summary: string;
      };
      state?: SystemState;
      error?: string;
    }>(response);

    if (!response.ok) {
      throw new Error(data?.error || 'Research muvaffaqiyatsiz tugadi.');
    }

    if (!data?.report) {
      throw new Error('Research bo‘sh javob qaytardi.');
    }

    if (data.state) {
      setSystemState(data.state);
    }

    void refreshMemory();
    return data.report.summary;
  }

  const handleCommand = async (event: React.FormEvent) => {
    event.preventDefault();
    const command = cmdInput.trim();
    if (!command || isProcessingCmd) {
      return;
    }

    const id = crypto.randomUUID();
    setCommands((prev) => [...prev, { id, command, output: 'Kognitiv tahlil bajarilmoqda...' }]);
    setCmdInput('');
    setIsProcessingCmd(true);

    try {
      if (command.toLowerCase() === 'tozalash') {
        setCommands([]);
        setIsProcessingCmd(false);
        return;
      }

      if (command.toLowerCase() === 'memory.status') {
        const latestState = await refreshState();
        const stateToShow = latestState || systemState;
        setCommands((prev) =>
          prev.map((item) =>
            item.id === id
              ? {
                  ...item,
                  output: `MEMORY: ${stateToShow.memoryCount}\nKNOWLEDGE: ${stateToShow.knowledgeCount}\nLAST TOPIC: ${stateToShow.lastLearnedTopic || 'yo‘q'}`,
                }
              : item,
          ),
        );
        setIsProcessingCmd(false);
        return;
      }

      if (command.toLowerCase().startsWith('learn ')) {
        const topic = command.slice(6).trim();
        const learned = await learnTopic(topic);
        setCommands((prev) =>
          prev.map((item) =>
            item.id === id
              ? {
                  ...item,
                  output: `[LEARNED] ${learned?.title || topic}\n${learned?.content || 'Mazmun saqlandi.'}`,
                }
              : item,
          ),
        );
        setIsProcessingCmd(false);
        return;
      }

      if (
        command.toLowerCase().startsWith('research ')
        || command.toLowerCase().startsWith('izla ')
        || command.toLowerCase().startsWith('qidir ')
      ) {
        const query = command.replace(/^(research|izla|qidir)\s+/i, '').trim();
        const summary = await runResearch(query);
        setCommands((prev) =>
          prev.map((item) =>
            item.id === id
              ? {
                  ...item,
                  output: summary,
                }
              : item,
          ),
        );
        setIsProcessingCmd(false);
        return;
      }

      if (command.toLowerCase() === 'emotion.status' || command.toLowerCase() === 'his-tuyg\'u') {
        const latestState = await refreshState();
        const emotions = latestState?.emotions || systemState.emotions;
        if (emotions) {
          setCommands((prev) =>
            prev.map((item) =>
              item.id === id
                ? {
                    ...item,
                    output: `EMOTION STATE:
DOMINANT: ${emotions.dominant.toUpperCase()} (${emotions.description})
MEHRIBONLIK: ${emotions.mehribonlik}%
GAZAB: ${emotions.gazab}%
HURSANDCHILIK: ${emotions.hursandchilik}%
SEVGI: ${emotions.sevgi}%
NAFRAT: ${emotions.nafrat}%
MAS'ULIYAT: ${emotions.masuliyat}%`,
                  }
                : item,
            ),
          );
        } else {
          setCommands((prev) =>
            prev.map((item) =>
              item.id === id
                ? { ...item, output: 'His-tuyg\'ular hali yuklanmagan.' }
                : item,
            ),
          );
        }
        setIsProcessingCmd(false);
        return;
      }

      if (command.toLowerCase() === 'emotion.reset') {
        try {
          const response = await fetch('/api/emotion/reset', { method: 'POST' });
          const data = await readJsonSafely<{ message: string; emotions: EmotionState }>(response);
          await refreshState();
          setCommands((prev) =>
            prev.map((item) =>
              item.id === id
                ? { ...item, output: `[RESET] ${data?.message || "His-tuyg'ular qaytarildi."}` }
                : item,
            ),
          );
        } catch {
          setCommands((prev) =>
            prev.map((item) =>
              item.id === id
                ? { ...item, output: "[XATOLIK] His-tuyg'ularni qaytarib bo'lmadi." }
                : item,
            ),
          );
        }
        setIsProcessingCmd(false);
        return;
      }

      const reply = await sendMessage(command, 'terminal');
      setCommands((prev) =>
        prev.map((item) => (item.id === id ? { ...item, output: reply } : item)),
      );
    } catch (error: any) {
      setCommands((prev) =>
        prev.map((item) =>
          item.id === id
            ? { ...item, output: `XATOLIK: ${error?.message || 'Noma’lum muammo.'}` }
            : item,
        ),
      );
    }

    setIsProcessingCmd(false);
  };

  const handleChat = async (event: React.FormEvent) => {
    event.preventDefault();
    const message = chatInput.trim();
    if (!message || isTyping) {
      return;
    }

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), text: message, sender: 'user' }]);
    setChatInput('');
    setIsTyping(true);

    try {
      if (message.toLowerCase().startsWith('o‘rgan ') || message.toLowerCase().startsWith("o'rgan ")) {
        const topic = message.replace(/^o['‘]rgan\s+/i, '').trim();
        const learned = await learnTopic(topic);
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            text: `${learned?.title || topic} mavzusi xotiraga yozildi. Endi bu bilim keyingi javoblarga ulanadi.`,
            sender: 'aida',
          },
        ]);
      } else if (
        message.toLowerCase().startsWith('izla ')
        || message.toLowerCase().startsWith('qidir ')
        || message.toLowerCase().startsWith('research ')
      ) {
        const query = message.replace(/^(research|izla|qidir)\s+/i, '').trim();
        const summary = await runResearch(query);
        setMessages((prev) => [...prev, { id: crypto.randomUUID(), text: summary, sender: 'aida' }]);
      } else {
        const reply = await sendMessage(message, 'chat');
        setMessages((prev) => [...prev, { id: crypto.randomUUID(), text: reply, sender: 'aida' }]);
      }
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          text: `Aloqa uzildi: ${error?.message || 'noma’lum xatolik'}`,
          sender: 'aida',
        },
      ]);
    }

    setIsTyping(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0f0d] text-emerald-500 font-mono overflow-hidden relative scanlines">
      <div className="absolute inset-0 z-0 bg-black flex items-center justify-center">
        {cameraActive ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover opacity-30 grayscale contrast-150"
            style={{ filter: 'sepia(1) hue-rotate(90deg) saturate(2) brightness(0.7)' }}
          />
        ) : (
          <div
            className="absolute inset-0 w-full h-full bg-cover bg-center opacity-20 grayscale"
            style={{
              backgroundImage:
                "url('https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?q=80&w=2000&auto=format&fit=crop')",
              filter: 'sepia(1) hue-rotate(90deg) saturate(2) brightness(0.5)',
            }}
          />
        )}
      </div>

      <motion.div
        className="absolute left-0 right-0 h-[2px] bg-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.8)] z-0 pointer-events-none"
        animate={{ top: ['-10%', '110%'] }}
        transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
      />

      <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 40 }).map((_, index) => (
          <motion.div
            key={index}
            className="absolute w-1 h-1 bg-emerald-500/40 rounded-full"
            initial={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              y: [0, -100 - Math.random() * 200],
              opacity: [0, 0.8, 0],
            }}
            transition={{
              duration: Math.random() * 5 + 5,
              repeat: Infinity,
              ease: 'linear',
              delay: Math.random() * 5,
            }}
          />
        ))}
      </div>

      {cameraError && !cameraActive && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 bg-red-950/80 border border-red-500/50 text-red-400 px-4 py-2 rounded-sm flex items-center gap-2 text-xs backdrop-blur-sm">
          <ShieldAlert size={14} />
          <span>{cameraError}</span>
        </div>
      )}

      <div className="absolute inset-0 z-0 pointer-events-none">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="absolute top-6 left-6 flex flex-col gap-1"
        >
          <div className="flex items-center gap-2 text-emerald-400">
            <Globe size={24} className="animate-[spin_10s_linear_infinite]" />
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-widest">AIDA CLOUD MEMORY NETWORK</span>
              <span className="text-[10px] tracking-widest opacity-70">PERSISTENT // LEARNING // RETRIEVAL</span>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="absolute top-6 right-6 flex flex-col items-end gap-1 text-[10px] text-emerald-400/70 tracking-widest"
        >
          <div className="flex items-center gap-2">
            <Database size={12} />
            <span>MEMORY BLOCKS:</span>
            <span className="text-emerald-300 font-bold">{systemState.memoryCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <BookOpen size={12} />
            <span>KNOWLEDGE:</span>
            <span className="text-emerald-300 font-bold">{systemState.knowledgeCount}</span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <Activity size={12} className="animate-pulse text-emerald-500" />
            <span>{systemState.autoLearnEnabled ? 'AUTO-LEARN ACTIVE' : 'MANUAL LEARN MODE'}</span>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <Globe size={12} />
            <span>{systemState.internetResearchEnabled ? 'WEB RESEARCH READY' : 'WEB RESEARCH OFF'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Brain size={12} />
            <span>{systemState.localModelEnabled ? 'LOCAL MODEL READY' : 'RULE-BASED CORE'}</span>
          </div>
          {systemState.emotions && (
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-emerald-500/20">
              <Activity size={12} className={`
                ${systemState.emotions.dominant === 'hursandchilik' ? 'text-yellow-400' : ''}
                ${systemState.emotions.dominant === 'mehribonlik' ? 'text-pink-400' : ''}
                ${systemState.emotions.dominant === 'gazab' ? 'text-red-400' : ''}
                ${systemState.emotions.dominant === 'sevgi' ? 'text-rose-400' : ''}
                ${systemState.emotions.dominant === 'nafrat' ? 'text-gray-400' : ''}
                ${systemState.emotions.dominant === 'masuliyat' ? 'text-blue-400' : ''}
              `} />
              <span className={`
                uppercase font-bold
                ${systemState.emotions.dominant === 'hursandchilik' ? 'text-yellow-400' : ''}
                ${systemState.emotions.dominant === 'mehribonlik' ? 'text-pink-400' : ''}
                ${systemState.emotions.dominant === 'gazab' ? 'text-red-400' : ''}
                ${systemState.emotions.dominant === 'sevgi' ? 'text-rose-400' : ''}
                ${systemState.emotions.dominant === 'nafrat' ? 'text-gray-400' : ''}
                ${systemState.emotions.dominant === 'masuliyat' ? 'text-blue-400' : ''}
              `}>
                {systemState.emotions.dominant.toUpperCase()}
              </span>
              <span className="opacity-70">({systemState.emotions.description})</span>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.6 }}
          className="absolute bottom-6 left-6 flex items-center gap-3 text-emerald-400/70"
        >
          <Fingerprint size={32} className="opacity-50" />
          <div className="flex flex-col text-[10px] tracking-widest">
            <span>PROFILE: {systemState.profile.name}</span>
            <span>{systemState.profile.description}</span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.8 }}
          className="absolute bottom-6 right-6 flex flex-col items-end gap-1 text-[10px] text-emerald-400/70 tracking-widest"
        >
          <div className="flex items-center gap-2">
            <Brain size={12} />
            <span>LAST LEARNED:</span>
            <span>{systemState.lastLearnedTopic || 'YO‘Q'}</span>
          </div>
          <div className="flex items-center gap-2">
            <Lock size={12} />
            <span>MODE: SAFE AUTONOMY</span>
          </div>
        </motion.div>

        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-emerald-500/10 rounded-full flex items-center justify-center">
          <div className="w-[450px] h-[450px] border border-emerald-500/20 rounded-full animate-[spin_30s_linear_infinite]" style={{ borderStyle: 'dashed' }} />
          <div className="absolute w-[400px] h-[400px] border border-emerald-500/10 rounded-full flex items-center justify-center">
            <div className="w-full h-[1px] bg-emerald-500/20 absolute" />
            <div className="h-full w-[1px] bg-emerald-500/20 absolute" />
          </div>
        </div>
      </div>

      <div
        className="absolute inset-0 z-0 opacity-10 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(to right, #10b981 1px, transparent 1px), linear-gradient(to bottom, #10b981 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none">
        <motion.div
          className="relative flex items-center justify-center mb-10"
          animate={{ scale: isAdapting ? [1, 1.02, 1] : 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="absolute w-72 h-72 rounded-full border border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] animate-[spin_15s_linear_infinite]" />
          <div className="absolute w-56 h-56 rounded-full border-t-2 border-b-2 border-emerald-400/40 animate-[spin_10s_linear_infinite_reverse]" />
          <motion.div
            className="w-40 h-40 rounded-full bg-emerald-950/60 backdrop-blur-md border-2 border-emerald-500/50 flex items-center justify-center shadow-[0_0_40px_rgba(16,185,129,0.2)] aida-core"
            style={{ '--core-color': coreColor } as React.CSSProperties}
          >
            <div className="text-center">
              <div className="text-3xl font-bold tracking-widest text-emerald-400 drop-shadow-[0_0_10px_rgba(16,185,129,0.8)] glitch-text" data-text="AIDA">
                AIDA
              </div>
              <div className="text-[9px] text-emerald-500 mt-2 tracking-[0.2em]">CLOUD MEMORY</div>
              <div className="text-[9px] text-emerald-500 tracking-[0.2em]">LEARNING ENGINE</div>
            </div>
          </motion.div>
          {isAdapting && (
            <div className="absolute -bottom-10 text-xs text-emerald-400 animate-pulse flex items-center gap-2 bg-emerald-950/80 px-3 py-1 border border-emerald-500/50">
              <Search size={12} /> MEMORY INDEX REFRESH...
            </div>
          )}
        </motion.div>

        <div className="w-full max-w-5xl px-6 mb-8">
          <div className="grid md:grid-cols-3 gap-4 pointer-events-auto">
            {memoryPreview.map((item) => (
              <div key={item.id} className="hud-panel p-4 text-xs text-emerald-300 min-h-[120px]">
                <div className="tracking-widest text-emerald-500 mb-2">{item.kind.toUpperCase()}</div>
                <div className="font-bold text-sm text-emerald-200 mb-2">{item.title}</div>
                <div className="line-clamp-4 opacity-80">{item.content}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex gap-8 pointer-events-auto">
          <button
            onClick={() => setView('terminal')}
            className={`flex items-center gap-3 px-8 py-3 rounded-sm border transition-all duration-300 ${view === 'terminal' ? 'bg-emerald-900/60 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.3)] text-emerald-100' : 'bg-black/60 border-emerald-900/50 text-emerald-600 hover:border-emerald-500 hover:text-emerald-400 hover:bg-emerald-950/40'}`}
          >
            <Terminal size={18} />
            <span className="tracking-widest text-sm font-bold">MEMORY TERMINAL</span>
          </button>
          <button
            onClick={() => setView('chat')}
            className={`flex items-center gap-3 px-8 py-3 rounded-sm border transition-all duration-300 ${view === 'chat' ? 'bg-emerald-900/60 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.3)] text-emerald-100' : 'bg-black/60 border-emerald-900/50 text-emerald-600 hover:border-emerald-500 hover:text-emerald-400 hover:bg-emerald-950/40'}`}
          >
            <MessageSquare size={18} />
            <span className="tracking-widest text-sm font-bold">NEURAL COMMS</span>
          </button>
        </div>
      </div>

      <AnimatePresence>
        {view === 'terminal' && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-4xl h-[65vh] z-20 hud-panel flex flex-col pointer-events-auto border border-emerald-500/30 shadow-[0_0_50px_rgba(0,0,0,0.8)]"
          >
            <div className="h-12 border-b border-emerald-900/50 flex items-center px-6 justify-between bg-emerald-950/80 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <Terminal size={16} className="text-emerald-400" />
                <span className="text-sm font-bold tracking-widest text-emerald-400">PERSISTENT MEMORY TERMINAL</span>
              </div>
              <button onClick={() => setView('core')} className="text-emerald-600 hover:text-emerald-300 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4 text-sm bg-[#050a08]/90 backdrop-blur-md">
              {commands.map((cmd) => (
                <div key={cmd.id} className="mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-600 font-bold">OVERSEER@AIDA:~$</span>
                    <span className="text-emerald-100">{cmd.command}</span>
                  </div>
                  <div className="text-cyan-400 ml-4 mt-2 mb-4 whitespace-pre-wrap">{cmd.output}</div>
                </div>
              ))}
              <div className="text-[11px] text-emerald-600">
                Tavsiya: `research suniy intellekt`, `learn matematika`, `memory.status`, yoki oddiy savol yozing.
              </div>
              <div ref={terminalEndRef} />
            </div>

            <form onSubmit={handleCommand} className="p-5 border-t border-emerald-900/50 flex items-center gap-3 bg-[#020504]">
              <span className="text-emerald-600 font-bold">OVERSEER@AIDA:~$</span>
              <input
                type="text"
                value={cmdInput}
                onChange={(event) => setCmdInput(event.target.value)}
                disabled={isProcessingCmd}
                className="flex-1 bg-transparent border-none outline-none text-emerald-100 font-mono disabled:opacity-50"
                autoFocus
                autoComplete="off"
                spellCheck="false"
              />
            </form>
          </motion.div>
        )}

        {view === 'chat' && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2 w-full max-w-3xl h-[65vh] z-20 hud-panel flex flex-col pointer-events-auto border border-emerald-500/30 shadow-[0_0_50px_rgba(0,0,0,0.8)]"
          >
            <div className="h-12 border-b border-emerald-900/50 flex items-center px-6 justify-between bg-emerald-950/80 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <Lock size={16} className="text-emerald-400" />
                <span className="text-sm font-bold tracking-widest text-emerald-400">ENCRYPTED MEMORY CHANNEL</span>
              </div>
              <button onClick={() => setView('core')} className="text-emerald-600 hover:text-emerald-300 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-[#050a08]/90 backdrop-blur-md flex flex-col">
              {messages.map((msg) => (
                <div key={msg.id} className={`max-w-[85%] p-4 rounded-sm ${msg.sender === 'user' ? 'self-end bg-emerald-950/40 border border-emerald-800/50 text-emerald-100' : 'self-start bg-black/60 border border-emerald-900/50 text-emerald-300'}`}>
                  <div className="text-[10px] font-bold tracking-widest opacity-50 mb-2 border-b border-emerald-900/30 pb-1">
                    {msg.sender === 'user' ? 'OVERSEER' : 'AIDA'}
                  </div>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</div>
                </div>
              ))}
              {isTyping && (
                <div className="self-start bg-black/60 border border-emerald-900/50 text-emerald-300 p-4 rounded-sm">
                  <div className="flex gap-2 items-center">
                    <span className="text-xs tracking-widest opacity-70">XOTIRA VA BILIM QATLAYOTGAN JAVOB</span>
                    <div className="flex gap-1">
                      <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0 }} className="w-1.5 h-1.5 bg-emerald-500 rounded-none" />
                      <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-1.5 h-1.5 bg-emerald-500 rounded-none" />
                      <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-1.5 h-1.5 bg-emerald-500 rounded-none" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <form onSubmit={handleChat} className="p-5 border-t border-emerald-900/50 flex items-center gap-4 bg-[#020504]">
              <input
                type="text"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                disabled={isTyping}
                placeholder="Savol bering, `izla suniy intellekt` yoki `o'rgan matematika` deb yozing..."
                className="flex-1 bg-emerald-950/20 border border-emerald-900/50 rounded-sm px-4 py-3 outline-none text-emerald-100 font-mono text-sm focus:border-emerald-500 transition-colors disabled:opacity-50"
                autoFocus
                autoComplete="off"
              />
              <button
                type="submit"
                disabled={isTyping || !chatInput.trim()}
                className="bg-emerald-900/40 text-emerald-300 px-6 py-3 rounded-sm border border-emerald-700 hover:bg-emerald-800/60 hover:text-emerald-100 transition-colors disabled:opacity-50 font-bold tracking-widest text-sm"
              >
                YUBORISH
              </button>
            </form>
>>>>>>> b051280dea8d539a47236a4d85212f3580c11b5a
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
