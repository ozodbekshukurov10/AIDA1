import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Cpu,
  Globe,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronDown,
  Zap,
  Shield,
  Database,
  Download,
  Trash2,
  Search,
} from 'lucide-react';

type ProviderName = 'ollama' | 'lmstudio' | 'local';

interface DiscoveredModel {
  id: string;
  name: string;
  provider: ProviderName;
  size_gb?: number;
  quantization?: string;
  parameter_size?: string;
  family?: string;
}

interface ManagerModel {
  id: string;
  name: string;
  provider: ProviderName;
  size_gb?: number;
  quantization?: string;
}

interface ProviderStatus {
  name: ProviderName;
  displayName: string;
  status: 'running' | 'stopped' | 'error' | 'not_installed';
  url: string;
  availableModels: string[];
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

interface ModelSelectorProps {
  currentProvider: ProviderName;
  onProviderChange: (provider: ProviderName) => void;
  currentModel: string;
  onModelChange: (model: string) => void;
  className?: string;
}

const DEFAULT_PROVIDERS: ProviderStatus[] = [
  {
    name: 'local', displayName: 'Local Core', status: 'running',
    url: 'local', availableModels: ['default'], icon: Cpu,
  },
  {
    name: 'ollama', displayName: 'Ollama', status: 'stopped',
    url: 'http://localhost:11434', availableModels: [], icon: Database,
  },
  {
    name: 'lmstudio', displayName: 'LM Studio', status: 'stopped',
    url: 'http://localhost:1234', availableModels: [], icon: Cpu,
  },
];

const PROVIDER_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  local: Cpu, ollama: Database, lmstudio: Cpu,
};

export default function ModelSelector({
  currentProvider, onProviderChange, currentModel, onModelChange, className = '',
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [providers, setProviders] = useState<ProviderStatus[]>(DEFAULT_PROVIDERS);
  const [discovered, setDiscovered] = useState<DiscoveredModel[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<ProviderStatus>(
    DEFAULT_PROVIDERS.find(p => p.name === 'ollama') || DEFAULT_PROVIDERS[0]
  );
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'providers' | 'models'>('providers');

  const fetchAll = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [statusRes, discoverRes, listRes] = await Promise.all([
        fetch('/api/models/status/'),
        fetch('/api/models/discover/'),
        fetch('/api/models/manage/list/'),
      ]);
      if (statusRes.ok) {
        const data = await statusRes.json();
        setProviders(data.providers || DEFAULT_PROVIDERS);
      }
      if (discoverRes.ok) {
        const data = await discoverRes.json();
        setDiscovered(data.models || []);
      }
      if (listRes.ok) {
        const data = await listRes.json();
        if (data.models?.length) {
          setDiscovered(data.models);
        }
      }
    } catch { /* ignore */ }
    setIsRefreshing(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    const p = providers.find(x => x.name === currentProvider);
    if (p) setSelectedProvider(p);
  }, [currentProvider, providers]);

  const modelsForProvider = discovered.filter(m => m.provider === selectedProvider.name);

  const handleProviderSelect = (p: ProviderStatus) => {
    setSelectedProvider(p);
    onProviderChange(p.name);
    setIsOpen(false);
  };

  const handleModelSelect = (modelName: string) => {
    onModelChange(modelName);
  };

  const startProvider = async (name: ProviderName) => {
    try {
      const r = await fetch(`/api/models/start/${name}`, { method: 'POST' });
      if (r.ok) fetchAll();
    } catch { /* ignore */ }
  };

  const stopProvider = async (name: ProviderName) => {
    try {
      const r = await fetch(`/api/models/stop/${name}`, { method: 'POST' });
      if (r.ok) fetchAll();
    } catch { /* ignore */ }
  };

  const pullModel = async (modelId: string) => {
    try {
      const r = await fetch('/api/models/manage/pull/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId }),
      });
      if (r.ok) fetchAll();
    } catch { /* ignore */ }
  };

  const removeModel = async (modelId: string) => {
    try {
      const r = await fetch('/api/models/manage/remove/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelId }),
      });
      if (r.ok) fetchAll();
    } catch { /* ignore */ }
  };

  const statusIcon = (s: ProviderStatus['status']) => {
    switch (s) {
      case 'running': return <CheckCircle size={16} className="text-green-500" />;
      case 'stopped': return <XCircle size={16} className="text-gray-400" />;
      case 'error': return <XCircle size={16} className="text-red-500" />;
      default: return <XCircle size={16} className="text-orange-500" />;
    }
  };

  const SelectedIcon = PROVIDER_ICONS[selectedProvider.name] || Cpu;

  return (
    <div className={`model-selector ${className}`}>
      <div className="model-selector-header">
        <button type="button" className="model-selector-button" onClick={() => setIsOpen(!isOpen)}>
          <SelectedIcon size={18} />
          <span className="model-selector-name">{selectedProvider.displayName}</span>
          {currentModel && <span className="model-selector-model">/{currentModel}</span>}
          <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
        <button type="button" className="refresh-button" onClick={fetchAll} disabled={isRefreshing} title="Yangilash">
          <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
        </button>
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="model-selector-dropdown"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <div className="model-selector-tabs">
              <button
                type="button"
                className={`ms-tab ${activeTab === 'providers' ? 'ms-tab-active' : ''}`}
                onClick={() => setActiveTab('providers')}
              >Provider</button>
              <button
                type="button"
                className={`ms-tab ${activeTab === 'models' ? 'ms-tab-active' : ''}`}
                onClick={() => setActiveTab('models')}
              >Modellar ({discovered.length})</button>
            </div>

            {activeTab === 'providers' && (
              <div className="provider-list">
                {providers.map(p => {
                  const isSelected = p.name === selectedProvider.name;
                  const ProviderIcon = PROVIDER_ICONS[p.name] || Cpu;
                  return (
                    <div
                      key={p.name}
                      className={`provider-item ${isSelected ? 'selected' : ''}`}
                      onClick={() => handleProviderSelect(p)}
                    >
                      <div className="provider-info">
                        <ProviderIcon size={18} />
                        <div className="provider-details">
                          <div className="provider-name">
                            {p.displayName}
                            {isSelected && <CheckCircle size={14} className="text-green-500" />}
                          </div>
                          <div className="provider-status">
                            {statusIcon(p.status)}
                            <span>{p.status === 'running' ? 'Ishlayapti' : p.status === 'stopped' ? 'To\'xtatilgan' : 'Xatolik'}</span>
                          </div>
                        </div>
                      </div>
                      <div className="provider-actions">
                        {p.status === 'stopped' && p.name !== 'local' && (
                          <button type="button" className="action-button start-button"
                            onClick={e => { e.stopPropagation(); startProvider(p.name); }} title="Ishga tushirish">
                            <Zap size={14} />
                          </button>
                        )}
                        {p.status === 'running' && p.name !== 'local' && (
                          <button type="button" className="action-button stop-button"
                            onClick={e => { e.stopPropagation(); stopProvider(p.name); }} title="To'xtatish">
                            <XCircle size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {activeTab === 'models' && (
              <div className="model-list">
                {discovered.length === 0 && (
                  <div className="model-list-empty">
                    <Search size={18} />
                    <span>Model topilmadi. Ollama'ga pull qiling yoki LM Studio'da model yuklang.</span>
                  </div>
                )}
                {modelsForProvider.map(m => (
                  <div
                    key={m.id}
                    className={`model-item ${currentModel === m.id ? 'selected' : ''}`}
                    onClick={() => handleModelSelect(m.id)}
                  >
                    <div className="model-item-info">
                      <div className="model-item-name">{m.name}</div>
                      <div className="model-item-meta">
                        <span className="provider-badge">{m.provider}</span>
                        {m.size_gb && <span>{m.size_gb} GB</span>}
                        {m.quantization && <span>{m.quantization}</span>}
                        {m.parameter_size && <span>{m.parameter_size}</span>}
                      </div>
                    </div>
                    <div className="model-item-actions">
                      {currentModel === m.id && <CheckCircle size={14} className="text-green-500" />}
                      {m.provider === 'ollama' && (
                        <button type="button" className="action-button remove-button"
                          onClick={e => { e.stopPropagation(); removeModel(m.id); }} title="O'chirish">
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                <div className="model-pull-bar">
                  <input
                    type="text"
                    placeholder="Model nomi (mas: llama3.2:3b)"
                    className="model-pull-input"
                    onKeyDown={e => {
                      if (e.key === 'Enter' && (e.target as HTMLInputElement).value.trim()) {
                        pullModel((e.target as HTMLInputElement).value.trim());
                        (e.target as HTMLInputElement).value = '';
                      }
                    }}
                  />
                  <button type="button" className="model-pull-btn" title="Pull model"
                    onClick={e => {
                      const input = (e.target as HTMLElement).previousElementSibling as HTMLInputElement;
                      if (input?.value?.trim()) {
                        pullModel(input.value.trim());
                        input.value = '';
                      }
                    }}
                  ><Download size={14} /> Pull</button>
                </div>
              </div>
            )}

            {selectedProvider.status === 'error' && (
              <div className="provider-error">
                <Shield size={14} />
                <span>{selectedProvider.url} — server mavjud emas</span>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
