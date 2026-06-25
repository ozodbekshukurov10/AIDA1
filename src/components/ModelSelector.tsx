import React, { useState, useEffect, useCallback } from "react";

interface Model {
  id: string;
  name: string;
  provider: "ollama" | "lmstudio";
  size?: string;
}

interface ModelSelectorProps {
  onModelChange?: (modelId: string) => void;
}

const BASE_URL = "/api";

export function ModelSelector({ onModelChange }: ModelSelectorProps) {
  const [models, setModels] = useState<Model[]>([]);
  const [currentModel, setCurrentModel] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [ollamaRunning, setOllamaRunning] = useState<boolean>(false);
  const [lmstudioRunning, setLmstudioRunning] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [successMessage, setSuccessMessage] = useState<string>("");

  const fetchModels = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${BASE_URL}/models/list/`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const data = await res.json();
      setModels(data.models || []);
      setCurrentModel(data.current || "");
      setOllamaRunning(data.ollama_running ?? false);
      setLmstudioRunning(data.lmstudio_running ?? false);
    } catch (err: any) {
      setError(err.message || "Failed to fetch models");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleModelSelect = async (modelId: string) => {
    setError("");
    setSuccessMessage("");
    try {
      const res = await fetch(`${BASE_URL}/models/select/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: modelId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setCurrentModel(data.current);
      setSuccessMessage(`Model switched to ${data.current}`);
      onModelChange?.(data.current);
    } catch (err: any) {
      setError(err.message || "Failed to select model");
    }
  };

  const handleRefresh = () => {
    setSuccessMessage("");
    fetchModels();
  };

  return (
    <div
      style={{
        padding: "16px",
        border: "1px solid #e2e8f0",
        borderRadius: "8px",
        backgroundColor: "#ffffff",
        fontFamily: "system-ui, -apple-system, sans-serif",
        maxWidth: "400px",
        width: "100%",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 600 }}>
          Model Selection
        </h3>
        <button
          onClick={handleRefresh}
          disabled={loading}
          style={{
            padding: "6px 12px",
            fontSize: "13px",
            border: "1px solid #cbd5e1",
            borderRadius: "4px",
            backgroundColor: loading ? "#f1f5f9" : "#ffffff",
            cursor: loading ? "not-allowed" : "pointer",
            color: "#334155",
          }}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
        <ServerBadge name="Ollama" running={ollamaRunning} />
        <ServerBadge name="LM Studio" running={lmstudioRunning} />
      </div>

      {loading && (
        <div
          style={{
            padding: "20px",
            textAlign: "center",
            color: "#64748b",
            fontSize: "14px",
          }}
        >
          Loading models...
        </div>
      )}

      {error && (
        <div
          style={{
            padding: "8px 12px",
            marginBottom: "12px",
            backgroundColor: "#fef2f2",
            color: "#dc2626",
            borderRadius: "4px",
            fontSize: "13px",
          }}
        >
          {error}
          <button
            onClick={fetchModels}
            style={{
              marginLeft: "8px",
              padding: "2px 8px",
              fontSize: "12px",
              border: "1px solid #fca5a5",
              borderRadius: "4px",
              backgroundColor: "transparent",
              cursor: "pointer",
              color: "#dc2626",
            }}
          >
            Retry
          </button>
        </div>
      )}

      {successMessage && (
        <div
          style={{
            padding: "8px 12px",
            marginBottom: "12px",
            backgroundColor: "#f0fdf4",
            color: "#16a34a",
            borderRadius: "4px",
            fontSize: "13px",
          }}
        >
          {successMessage}
        </div>
      )}

      {!loading && models.length === 0 && !error && (
        <div
          style={{
            padding: "20px",
            textAlign: "center",
            color: "#94a3b8",
            fontSize: "14px",
          }}
        >
          No models available. Ensure Ollama or LM Studio is running.
        </div>
      )}

      {models.length > 0 && (
        <select
          value={currentModel}
          onChange={(e) => handleModelSelect(e.target.value)}
          style={{
            width: "100%",
            padding: "10px 12px",
            fontSize: "14px",
            border: "1px solid #cbd5e1",
            borderRadius: "4px",
            backgroundColor: "#ffffff",
            color: "#1e293b",
            cursor: "pointer",
            outline: "none",
            boxSizing: "border-box",
          }}
        >
          {models.map((m) => (
            <option key={m.id} value={m.name}>
              {m.name} ({m.provider})
            </option>
          ))}
        </select>
      )}
    </div>
  );
}

function ServerBadge({ name, running }: { name: string; running: boolean }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "4px 10px",
        borderRadius: "999px",
        fontSize: "12px",
        fontWeight: 500,
        backgroundColor: running ? "#dcfce7" : "#fef2f2",
        color: running ? "#166534" : "#dc2626",
        border: `1px solid ${running ? "#bbf7d0" : "#fecaca"}`,
      }}
    >
      <span
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          backgroundColor: running ? "#22c55e" : "#ef4444",
          display: "inline-block",
        }}
      />
      {name} {running ? "Running" : "Offline"}
    </div>
  );
}
