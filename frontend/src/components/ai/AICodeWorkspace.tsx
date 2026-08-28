import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Terminal, 
  Play, 
  FileCode, 
  Plus, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

interface FileMap {
  [filename: string]: string;
}

export default function AICodeWorkspace() {
  const [activeFile, setActiveFile] = useState('main.py');
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [terminalLines, setTerminalLines] = useState<string[]>([
    "AIDA Code Environment initialized.",
    "Root directory: C:/AIDA1-main",
    "Ready for agent pair programming instructions..."
  ]);

  const [files, setFiles] = useState<FileMap>({
    'main.py': `from fastapi import FastAPI, Depends, HTTPException\nfrom database import get_db\n\napp = FastAPI(title="AIDA Core Engine")\n\n@app.get("/")\ndef read_root():\n    return {"status": "AIDA operational", "latency": "4ms"}\n\n@app.get("/system/stats")\ndef get_stats(db = Depends(get_db)):\n    return {"cpu": "22%", "memory": "48%", "agents": "active"}\n`,
    'database.py': `import sqlite3\n\nDATABASE_URL = "db.sqlite3"\n\ndef get_db():\n    conn = sqlite3.connect(DATABASE_URL)\n    try:\n        yield conn\n    finally:\n        conn.close()\n`,
    'requirements.txt': `fastapi>=0.100.0\nuvicorn>=0.22.0\nsqlite3`
  });

  const terminalEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLines]);

  const addTerminalLine = (line: string) => {
    setTerminalLines(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${line}`]);
  };

  const handleRunCode = () => {
    addTerminalLine(`Running: uvicorn main:app --reload --port 8000`);
    setTimeout(() => {
      addTerminalLine(`INFO:     Started server process [8000]`);
      addTerminalLine(`INFO:     Waiting for application startup.`);
      addTerminalLine(`INFO:     Application startup complete.`);
      addTerminalLine(`INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`);
    }, 800);
  };

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isProcessing) return;

    setIsProcessing(true);
    addTerminalLine(`User request: "${prompt}"`);
    addTerminalLine(`[AIDA Agent] Starting code generation and refactoring cycle...`);

    setTimeout(() => {
      addTerminalLine(`[Research] Scanning project workspace tree for files...`);
    }, 600);

    setTimeout(() => {
      addTerminalLine(`[Modify] Analyzing main.py dependencies and functions...`);
    }, 1500);

    setTimeout(() => {
      // Simulate modifying main.py and adding auth.py dynamically!
      setFiles(prev => {
        const updated = { ...prev };
        updated['auth.py'] = `from jose import JWTError, jwt\nfrom datetime import datetime, timedelta\n\nSECRET_KEY = "AIDA_SECRET"\nALGORITHM = "HS256"\n\ndef create_access_token(data: dict):\n    to_encode = data.copy()\n    expire = datetime.utcnow() + timedelta(minutes=15)\n    to_encode.update({"exp": expire})\n    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n`;
        updated['main.py'] = prev['main.py'] + `\n# Added by AIDA Agent\nfrom auth import create_access_token\n\n@app.post("/auth/login")\ndef login(user: dict):\n    token = create_access_token({"sub": user.get("username")})\n    return {"access_token": token, "token_type": "bearer"}\n`;
        return updated;
      });
      addTerminalLine(`[File Create] Created new module: auth.py`);
      addTerminalLine(`[File Edit] Added "/auth/login" endpoint in main.py`);
      setActiveFile('auth.py');
    }, 2800);

    setTimeout(() => {
      addTerminalLine(`[Verification] Executing test suite: pytest tests/test_auth.py...`);
    }, 3800);

    setTimeout(() => {
      addTerminalLine(`tests/test_auth.py::test_login_success PASSED [100%]`);
      addTerminalLine(`[Completed] Code refactored and verified successfully!`);
      setIsProcessing(false);
      setPrompt('');
    }, 4800);
  };

  return (
    <div className="w-full h-[620px] rounded-3xl border border-[#5FE8FF]/10 bg-[#08111F]/20 backdrop-blur-xl grid grid-cols-12 overflow-hidden shadow-[0_25px_60px_rgba(0,0,0,0.5)]">
      
      {/* 1. Left Sidebar: File Explorer */}
      <div className="col-span-12 md:col-span-3 border-b md:border-b-0 md:border-r border-[#F5F7FA]/5 bg-[#05070D]/40 p-5 flex flex-col justify-between">
        <div className="flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-[#F5F7FA]/5 pb-3">
            <span className="text-[10px] font-mono tracking-widest text-[#F5F7FA]/40 uppercase">WORKSPACE FILES</span>
            <Plus className="w-3.5 h-3.5 text-[#5FE8FF] opacity-60 hover:opacity-100 cursor-pointer" />
          </div>

          <div className="flex flex-col gap-1.5">
            {Object.keys(files).map((name) => (
              <button
                key={name}
                onClick={() => setActiveFile(name)}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-left text-xs font-mono transition-all cursor-pointer ${
                  activeFile === name 
                    ? 'bg-[#5FE8FF]/10 border border-[#5FE8FF]/20 text-[#5FE8FF]' 
                    : 'text-[#F5F7FA]/65 hover:bg-[#F5F7FA]/5'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                <span>{name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="text-[9px] font-mono text-[#F5F7FA]/30 uppercase mt-4">
          Status: Synchronized
        </div>
      </div>

      {/* 2. Center: Code Editor & Terminal */}
      <div className="col-span-12 md:col-span-6 flex flex-col h-full min-w-0">
        
        {/* Editor Toolbar */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-[#F5F7FA]/5 bg-[#05070D]/20">
          <span className="text-xs font-mono text-[#F5F7FA]/40">{activeFile}</span>
          <button 
            onClick={handleRunCode}
            className="flex items-center gap-1.5 px-3 py-1 bg-[#5FE8FF]/10 hover:bg-[#5FE8FF]/20 border border-[#5FE8FF]/20 text-[#5FE8FF] rounded-lg text-[10px] font-mono cursor-pointer"
          >
            <Play className="w-3 h-3" />
            <span>Run Server</span>
          </button>
        </div>

        {/* Code Editor Area */}
        <div className="flex-1 bg-[#05070D]/40 p-5 overflow-auto font-mono text-xs leading-relaxed text-[#F5F7FA]/80">
          <pre className="whitespace-pre-wrap select-text">
            <code>{files[activeFile]}</code>
          </pre>
        </div>

        {/* Bottom Terminal Output */}
        <div className="h-44 border-t border-[#F5F7FA]/5 bg-[#05070D]/70 flex flex-col overflow-hidden">
          <div className="px-5 py-2 border-b border-[#F5F7FA]/5 bg-[#05070D] flex justify-between items-center">
            <span className="text-[9px] font-mono text-[#F5F7FA]/30 uppercase tracking-wider">Agent Terminal Console</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#5FE8FF] animate-pulse" />
          </div>
          <div className="flex-1 p-4 overflow-y-auto font-mono text-[10px] text-[#F5F7FA]/60 flex flex-col gap-1 select-text">
            {terminalLines.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap break-all leading-normal">
                {line.startsWith('[') ? (
                  <span className="text-[#5FE8FF]/70">{line}</span>
                ) : (
                  line
                )}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
        </div>

      </div>

      {/* 3. Right: AIDA AI Assistant Instruct Console */}
      <div className="col-span-12 md:col-span-3 border-t md:border-t-0 md:border-l border-[#F5F7FA]/5 p-5 flex flex-col justify-between bg-[#05070D]/30 backdrop-blur-xl">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2 pb-2 border-b border-[#F5F7FA]/5">
            <Sparkles className="w-4 h-4 text-[#5FE8FF] animate-pulse" />
            <span className="text-xs font-bold text-[#F5F7FA] tracking-wide">AIDA Code</span>
          </div>
          
          <p className="text-[11px] text-[#F5F7FA]/40 font-light leading-relaxed">
            Enter prompt parameters below. AIDA Agent will read, edit, execute, and verify workspace code dynamically.
          </p>

          <form onSubmit={handleCommandSubmit} className="flex flex-col gap-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. Add JWT auth endpoints..."
              disabled={isProcessing}
              className="w-full h-32 p-3 bg-[#05070D]/60 border border-[#F5F7FA]/10 rounded-xl text-xs text-[#F5F7FA] font-light placeholder-[#F5F7FA]/20 outline-none transition-all focus:border-[#5FE8FF]"
            />
            <button
              type="submit"
              disabled={isProcessing || !prompt.trim()}
              className="py-3 bg-[#5FE8FF] hover:bg-[#5FE8FF]/95 disabled:opacity-45 text-[#05070D] font-bold text-xs tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {isProcessing ? (
                <div className="w-3.5 h-3.5 border-2 border-[#05070D]/40 border-t-[#05070D] rounded-full animate-spin" />
              ) : (
                <>
                  <span>Instruct Agent</span>
                  <Send className="w-3 h-3" />
                </>
              )}
            </button>
          </form>
        </div>

        <div className="flex flex-col gap-2 bg-[#05070D]/50 border border-[#F5F7FA]/5 p-3.5 rounded-xl text-[10px] font-mono leading-relaxed">
          <span className="text-[#5FE8FF] font-bold uppercase tracking-wider flex items-center gap-1.5">
            {isProcessing ? (
              <>
                <AlertCircle className="w-3.5 h-3.5 animate-spin" />
                <span>Status: Processing</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Status: Ready</span>
              </>
            )}
          </span>
          <span className="text-[#F5F7FA]/30 mt-1">Agent loop is active. Changes auto-verify.</span>
        </div>
      </div>

    </div>
  );
}
