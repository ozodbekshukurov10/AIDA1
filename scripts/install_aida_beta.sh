#!/usr/bin/env bash
# AIDA Beta — Standalone Code Assistant Installer (Linux / macOS)
# Usage: bash scripts/install_aida_beta.sh

set -euo pipefail
AIDA_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║    AIDA Beta — Code Assistant Installer  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Check Ollama
echo "[1/5] Ollama tekshirilmoqda..."
if ! command -v ollama &>/dev/null; then
    echo "  Ollama topilmadi. https://ollama.com dan o'rnating."
    exit 1
fi
echo "  Ollama: $(command -v ollama)"

# 2. Download base model
echo "[2/5] Base model yuklanmoqda (qwen2.5-coder:3b)..."
ollama pull qwen2.5-coder:3b
echo "  Model yuklandi."

# 3. Build AIDA Beta model
echo "[3/5] AIDA Beta modeli build qilinmoqda..."
ollama create aida-beta -f "$AIDA_DIR/aida_beta/Modelfile"
echo "  AIDA Beta modeli build qilindi."

# 4. Install Python package
echo "[4/5] Python paket o'rnatilmoqda..."
if [ -f "$AIDA_DIR/.venv/bin/python" ]; then
    "$AIDA_DIR/.venv/bin/python" -m pip install -e "$AIDA_DIR" --quiet 2>/dev/null
else
    python3 -m pip install -e "$AIDA_DIR" --quiet 2>/dev/null
fi
echo "  Python paket o'rnatildi."

# 5. Install CLI globally
echo "[5/5] CLI o'rnatilmoqda..."
CLI_PATH="$AIDA_DIR/aida_beta/cli.py"
chmod +x "$CLI_PATH"

# Create launcher script in /usr/local/bin
sudo tee /usr/local/bin/aida-beta > /dev/null << LAUNCHER
#!/usr/bin/env bash
exec python3 "$CLI_PATH" "\$@"
LAUNCHER
sudo chmod +x /usr/local/bin/aida-beta

# Also create 'aida' alias
sudo ln -sf /usr/local/bin/aida-beta /usr/local/bin/aida 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    O'RNATISH TUGALLANDI!                 ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Buyruqlar:                              ║"
echo "║    aida-beta          — Interactive REPL ║"
echo "║    aida               — qisqa alias      ║"
echo "║    aida-beta 'sozlov' — bir martalik     ║"
echo "║    aida-beta --help   — yordam           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Terminalni qayta oching yoki: source ~/.bashrc"
