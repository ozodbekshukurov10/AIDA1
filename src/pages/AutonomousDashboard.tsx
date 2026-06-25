import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Info,
  Loader2,
  Network,
  Server,
  TrendingDown,
  TrendingUp,
  Users,
  Wifi,
  WifiOff,
  Zap,
} from 'lucide-react';

interface Metric {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  trend: 'up' | 'down' | 'neutral';
}

interface Agent {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  performance: {
    success_rate: number;
    avg_time: number;
    total_calls: number;
  };
}

interface Alert {
  level: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
}

interface DataPoint {
  time: string;
  value: number;
}

function MetricCard({ label, value, icon: Icon, trend }: Metric) {
  const trendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : null;
  const trendColor = trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-rose-400' : 'text-gray-400';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5 flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-widest text-[var(--muted)]">{label}</span>
        <Icon size={18} className="text-[var(--mint)]" />
      </div>
      <div className="flex items-end gap-3">
        <span className="text-3xl font-extrabold text-[var(--text)]">{value}</span>
        {trendIcon && (
          <trendIcon size={18} className={`${trendColor} mb-1`} />
        )}
      </div>
    </motion.div>
  );
}

function AgentMonitor({ agents }: { agents: Agent[] }) {
  const statusColor = (s: Agent['status']) =>
    s === 'active' ? 'text-green-400' : s === 'idle' ? 'text-amber-400' : 'text-rose-400';
  const statusBg = (s: Agent['status']) =>
    s === 'active' ? 'bg-green-500/10 border-green-500/20' : s === 'idle' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-rose-500/10 border-rose-500/20';

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)] mb-4">Agents Monitor</div>
      <div className="flex flex-col gap-3">
        {agents.map((agent, i) => (
          <motion.div
            key={agent.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`flex items-center gap-4 rounded-lg border p-3 ${statusBg(agent.status)}`}
          >
            <div className={`w-2 h-2 rounded-full ${statusColor(agent.status)}`} />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-[var(--text)] truncate">{agent.name}</div>
              <div className="text-xs text-[var(--muted)] mt-0.5">
                {agent.performance.total_calls} calls · {agent.performance.success_rate}% success · {agent.performance.avg_time}ms
              </div>
            </div>
            <span className={`text-[10px] uppercase tracking-wider ${statusColor(agent.status)}`}>{agent.status}</span>
          </motion.div>
        ))}
        {agents.length === 0 && (
          <div className="text-sm text-[var(--muted)] text-center py-6">No agents connected</div>
        )}
      </div>
    </div>
  );
}

function AlertList({ alerts }: { alerts: Alert[] }) {
  const levelIcon = (l: Alert['level']) =>
    l === 'error' ? AlertCircle : l === 'warning' ? AlertTriangle : Info;
  const levelColor = (l: Alert['level']) =>
    l === 'error' ? 'text-rose-400 border-rose-500/20 bg-rose-500/10' : l === 'warning' ? 'text-amber-400 border-amber-500/20 bg-amber-500/10' : 'text-sky-400 border-sky-500/20 bg-sky-500/10';

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)] mb-4">System Alerts</div>
      <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
        <AnimatePresence>
          {alerts.map((alert, i) => {
            const Icon = levelIcon(alert.level);
            return (
              <motion.div
                key={`${alert.timestamp}-${i}`}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`flex items-start gap-3 rounded-lg border p-3 text-sm ${levelColor(alert.level)}`}
              >
                <Icon size={16} className="mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-[var(--text)]">{alert.message}</div>
                  <div className="text-[10px] text-[var(--muted)] mt-1">{alert.timestamp}</div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        {alerts.length === 0 && (
          <div className="text-sm text-[var(--muted)] text-center py-6">No alerts</div>
        )}
      </div>
    </div>
  );
}

function PerformanceChart({ data }: { data: DataPoint[] }) {
  if (data.length < 2) {
    return (
      <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5">
        <div className="text-xs uppercase tracking-widest text-[var(--muted)] mb-4">Performance</div>
        <div className="flex items-center justify-center h-48 text-sm text-[var(--muted)]">Waiting for data...</div>
      </div>
    );
  }

  const values = data.map(d => d.value);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const width = 600;
  const height = 180;
  const padding = { top: 10, right: 10, bottom: 20, left: 10 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;
  const stepX = chartW / (data.length - 1);

  const pathD = data
    .map((d, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + chartH - ((d.value - min) / range) * chartH;
      return `${i === 0 ? 'M' : 'L'}${x},${y}`;
    })
    .join(' ');

  const areaD = `${pathD} L${padding.left + (data.length - 1) * stepX},${padding.top + chartH} L${padding.left},${padding.top + chartH} Z`;

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)] mb-4">Performance</div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto max-h-48" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--mint)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--mint)" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#chartGrad)" />
        <path d={pathD} fill="none" stroke="var(--mint)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {data.filter((_, i) => i % Math.max(1, Math.floor(data.length / 6)) === 0 || i === data.length - 1).map((d, i, arr) => {
          const idx = data.indexOf(d);
          const x = padding.left + idx * stepX;
          const y = padding.top + chartH - ((d.value - min) / range) * chartH;
          return (
            <g key={d.time}>
              <text x={x} y={height - 4} textAnchor="middle" className="fill-[var(--muted)]" fontSize="9">{d.time}</text>
              {i === arr.length - 1 && (
                <text x={x} y={y - 6} textAnchor="end" className="fill-[var(--text)]" fontSize="10">{d.value}</text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function ModelUsage({ models }: { models: Array<{ name: string; usage: number; color: string }> }) {
  const total = models.reduce((s, m) => s + m.usage, 0) || 1;
  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5">
      <div className="text-xs uppercase tracking-widest text-[var(--muted)] mb-4">Models Usage</div>
      <div className="flex flex-col gap-3">
        {models.map((m) => (
          <div key={m.name}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-[var(--text)] truncate">{m.name}</span>
              <span className="text-[var(--muted)]">{Math.round((m.usage / total) * 100)}%</span>
            </div>
            <div className="h-2 rounded-full bg-[var(--bg-soft)] overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(m.usage / total) * 100}%` }}
                className="h-full rounded-full"
                style={{ backgroundColor: m.color }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              />
            </div>
          </div>
        ))}
        {models.length === 0 && (
          <div className="text-sm text-[var(--muted)] text-center py-6">No model data</div>
        )}
      </div>
    </div>
  );
}

export default function AutonomousDashboard() {
  const [metrics, setMetrics] = useState<Record<string, number | string>>({});
  const [agents, setAgents] = useState<Agent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [history, setHistory] = useState<DataPoint[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const addAlert = useCallback((level: Alert['level'], message: string) => {
    setAlerts(prev => [{ level, message, timestamp: new Date().toLocaleTimeString() }, ...prev].slice(0, 50));
  }, []);

  const processStatus = useCallback((data: any) => {
    setMetrics({
      health_score: data.health_score ?? data.health ?? 0,
      success_rate: data.success_rate ?? 0,
      avg_response_time: data.avg_response_time ?? data.avg_time ?? 0,
      active_tasks: data.active_tasks ?? data.active_agents ?? 0,
    });
    if (data.agents) setAgents(data.agents);
    if (data.alerts) setAlerts(data.alerts);
    if (data.history) setHistory(data.history);
    setError('');
    setLoading(false);
  }, []);

  const connectWs = useCallback(() => {
    const wsUrl = 'ws://localhost:8000/ws/metrics/';
    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
    } catch {
      return;
    }
    ws.onopen = () => {
      setConnected(true);
      setLoading(false);
      addAlert('info', 'Real-time monitoring connected');
    };
    ws.onmessage = (e) => {
      try {
        processStatus(JSON.parse(e.data));
      } catch {
        /**/
      }
    };
    ws.onclose = () => {
      setConnected(false);
      setLoading(false);
    };
    ws.onerror = () => {
      ws.close();
    };
    wsRef.current = ws;
  }, [processStatus, addAlert]);

  const fetchRest = useCallback(async () => {
    try {
      const res = await fetch('/api/monitoring/status/');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      processStatus(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fetch failed');
      setLoading(false);
    }
  }, [processStatus]);

  useEffect(() => {
    const shouldUseWs = false;
    if (shouldUseWs) {
      connectWs();
    }
    fetchRest();
    pollRef.current = setInterval(fetchRest, 5000);
    addAlert('info', 'Monitoring dashboard initialized');
    return () => {
      wsRef.current?.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [connectWs, fetchRest, addAlert]);

  const metricCards: Metric[] = [
    { label: 'Health Score', value: metrics.health_score ?? '--', icon: Activity, trend: 'up' },
    { label: 'Success Rate', value: metrics.success_rate != null ? `${metrics.success_rate}%` : '--', icon: CheckCircle2, trend: 'up' },
    { label: 'Avg Response Time', value: metrics.avg_response_time != null ? `${metrics.avg_response_time}ms` : '--', icon: Clock, trend: 'down' },
    { label: 'Active Tasks', value: metrics.active_tasks ?? '--', icon: Zap, trend: 'neutral' },
  ];

  const modelUsage = [
    { name: 'GPT-4', usage: 45, color: 'var(--mint)' },
    { name: 'Claude 3', usage: 30, color: 'var(--amber)' },
    { name: 'Llama 3', usage: 25, color: 'var(--ice)' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center gap-3 text-[var(--muted)]"
        >
          <Loader2 size={20} className="animate-spin" />
          <span>Loading monitoring data...</span>
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col gap-5"
    >
      <div className="flex items-center gap-3 mb-1">
        <Server size={18} className="text-[var(--mint)]" />
        <h2 className="text-xl font-bold text-[var(--text)]">Autonomous Monitoring</h2>
        {connected ? (
          <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-500/10 border border-green-500/20 rounded-full px-3 py-1">
            <Wifi size={12} /> Live
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-full px-3 py-1">
            <WifiOff size={12} /> Polling
          </span>
        )}
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-4 py-3"
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </motion.div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((m) => (
          <MetricCard key={m.label} {...m} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <AgentMonitor agents={agents} />
        <ModelUsage models={modelUsage} />
        <AlertList alerts={alerts} />
      </div>

      <PerformanceChart data={history} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5 flex items-center gap-4"
        >
          <Network size={22} className="text-[var(--ice)]" />
          <div>
            <div className="text-xs uppercase tracking-widest text-[var(--muted)]">System Load</div>
            <div className="text-lg font-bold text-[var(--text)]">{metrics.system_load ?? '--'}%</div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5 flex items-center gap-4"
        >
          <Cpu size={22} className="text-[var(--amber)]" />
          <div>
            <div className="text-xs uppercase tracking-widest text-[var(--muted)]">Memory Usage</div>
            <div className="text-lg font-bold text-[var(--text)]">{metrics.memory_usage ?? '--'}%</div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5 flex items-center gap-4"
        >
          <Users size={22} className="text-[var(--rose)]" />
          <div>
            <div className="text-xs uppercase tracking-widest text-[var(--muted)]">Active Users</div>
            <div className="text-lg font-bold text-[var(--text)]">{metrics.active_users ?? '--'}</div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-xl border border-[var(--line)] bg-[var(--panel)] backdrop-blur-xl p-5 flex items-center gap-4"
        >
          <Loader2 size={22} className="text-[var(--mint)]" />
          <div>
            <div className="text-xs uppercase tracking-widest text-[var(--muted)]">Queue</div>
            <div className="text-lg font-bold text-[var(--text)]">{metrics.queue_size ?? '--'}</div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
