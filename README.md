# ⚒️ FreedomForge AI

**Local AI chat, completely offline. No cloud. No account. No subscription. Ever.**

FreedomForge AI is a desktop chat application that runs powerful open-source AI models entirely on your own computer. Your conversations stay on your machine — nothing is ever sent to a server.

> *Dedicated to Miranda. She will never be forgotten.*

---

## ✨ Features

- 💬 **Streaming AI chat** — token-by-token responses, just like ChatGPT, but fully local
- 📦 **One-click model downloads** — 100+ curated models from TinyLlama to Llama 3, Mistral, Phi, Qwen, Gemma, and more
- 🎤 **Voice input & output** — speak your questions, hear the answers (optional)
- 🔒 **Privacy controls** — network kill switch cuts all internet access while you chat
- 🖥️ **System dashboard** — live CPU/GPU/RAM monitoring
- 🎓 **Training mode** — practice-based skill tracker with session logs
- 🎬 **Video generation** — optional ComfyUI integration
- 🌍 **Multilingual UI** — English, Spanish, French, German, Portuguese
- 🔐 **Encrypted storage** — AES encryption for sensitive data

---

## 🖥️ Requirements

| | Minimum | Recommended |
|---|---|---|
| **OS** | Windows 10+, Ubuntu 20.04+, macOS 12+ | Windows 11, Ubuntu 22.04+, macOS 13+ |
| **Python** | 3.10 | 3.11 or 3.12 |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 2 GB free (for a small model) | 10 GB+ |
| **GPU** | None (CPU works) | NVIDIA GPU (CUDA) or Apple Silicon |

---

## 🚀 Installation

### Linux / macOS

```bash
# 1. Clone the repository
git clone https://github.com/freeechoaiwhisperer-hash/FreedomForgeAI.git
cd FreedomForgeAI

# 2. Run the installer (one command — handles everything)
bash install.sh
```

The installer will:
- Check your Python version
- Create a virtual environment (`.venv`)
- Install all dependencies
- Detect your GPU (NVIDIA CUDA / Apple Silicon Metal / CPU)
- Create a desktop shortcut
- Offer to launch the app

### Windows

```
1. Download or clone this repository
2. Double-click  install.bat
   (or right-click install.ps1 → "Run with PowerShell")
```

The installer creates a `launch.bat` file and a desktop shortcut.

> **Note:** If PowerShell blocks the script, run this first in PowerShell:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

---

## ▶️ Launching the App

After installation:

**Linux / macOS:**
```bash
bash launch.sh
```
Or use the desktop shortcut created during installation.

**Windows:**
```
Double-click launch.bat
```
Or use the desktop shortcut.

**Any platform (manual):**
```bash
# Activate the virtual environment first
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate             # Windows

python main.py
```

---

## 🗺️ First-Run Walkthrough

1. **Splash screen** — the app loads (~2 seconds)
2. **Setup Wizard** — on your very first launch, a wizard will:
   - Welcome you
   - Show the license agreement
   - Ask you to choose a folder for AI models (e.g. `~/Models` or any folder with a few GB free)
3. **Main window opens** — you'll land on the **💬 Chat** tab

---

## 📦 Downloading Your First Model

Before you can chat, you need to download an AI model.

1. Click **📦 Models** in the left sidebar
2. Browse the curated list — models are grouped by size:
   - **⚡ TinyLlama 1.1B** — 670 MB, runs on *any* computer with 2 GB RAM. Best starting point.
   - **🔷 Phi-4 Mini 3.8B** — 2.3 GB, excellent quality for 4 GB RAM systems
   - **🦙 Llama 3.1 8B** — 4.7 GB, great all-rounder for 8 GB+ RAM
3. Click **⬇ Download** next to the model you want
4. Wait for the download to finish (progress bar shown)
5. The model auto-loads when done

**Tip:** Start with **TinyLlama 1.1B** if you're unsure — it's fast and works everywhere.

---

## 💬 Chatting

1. Go to the **💬 Chat** tab
2. Select your model from the dropdown at the top (it auto-selects the last used model)
3. Type your message in the box at the bottom
4. Press **Enter** (or click **Send**)
5. Watch the response stream in real time

**Keyboard shortcuts:**
- `Enter` — send message
- `Shift+Enter` — new line in your message

**Top bar toggles:**
- 🎤 **Mic** — enable voice input (speak instead of type)
- 🔊 **Voice** — enable text-to-speech (hear responses read aloud)
- 🖱️ **Let Bot Click** — enable the agent module (allows the AI to run commands)

---

## 🎭 Personalities

Click the **⚒️ FreedomForge AI** logo **5 times** to cycle through AI personalities:

| Mode | Style |
|------|-------|
| ✨ Normal | Warm, helpful, direct |
| 🔥 Chaos | Unfiltered, opinionated, zero chill |
| 🎯 Focus | Precise, technical, no fluff |

> Unlock required — see **⚙️ Settings → Special Features**

---

## 🔒 Privacy

- **Network Kill Switch** — Go to **🔒 Privacy** tab → toggle to cut all internet access
- **Encryption** — Enable AES encryption for stored data in the Privacy tab
- The app never phones home; there is no telemetry

---

## ⚙️ Settings

Available in the **⚙️ Settings** tab:

- **Theme** — Midnight (dark), Ocean, Forge, Light
- **Font size** — adjust chat text size
- **Context window** (`n_ctx`) — how much conversation history the AI remembers
- **Language** — UI language (English, Spanish, French, German, Portuguese)
- **Special Features** — unlock advanced personalities

---

## 🔧 Troubleshooting

### "No model loaded" / can't chat
→ Go to the **📦 Models** tab and download a model first.

### App won't start / import errors
→ Re-run the installer: `bash install.sh` (Linux/macOS) or `install.bat` (Windows)

### Model download fails
→ Check your internet connection. HuggingFace may occasionally be slow. Try again.

### Voice input doesn't work
→ PyAudio/microphone support requires extra system packages:
- **Ubuntu/Debian:** `sudo apt install portaudio19-dev python3-pyaudio`
- **macOS:** `brew install portaudio`
- **Windows:** The installer handles this automatically

### GPU not detected
→ For NVIDIA: ensure CUDA drivers are installed (`nvidia-smi` should work in terminal)  
→ For Apple Silicon: llama-cpp-python with Metal support is installed automatically by `install.sh`

### App crashes on start
→ Check `crash_reports/` folder in the app directory for the error JSON  
→ Check `logs/app.log` for detailed logs

### Windows: "execution policy" error
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## 🏗️ Project Structure

```
FreedomForgeAI/
├── main.py              # Entry point
├── install.sh           # Linux/macOS one-click installer
├── install.bat          # Windows installer launcher
├── install.ps1          # Windows PowerShell installer
├── launch.sh            # Linux/macOS launcher
├── config.json          # App settings
├── requirements.txt     # Python dependencies
│
├── core/                # Core logic
│   ├── model_manager.py # LLM loading & streaming inference
│   ├── config.py        # Settings management
│   ├── tts.py           # Text-to-speech & voice input
│   ├── privacy.py       # Network kill switch
│   ├── hardware.py      # GPU detection
│   └── trainer.py       # Skill training system
│
├── ui/                  # GUI panels
│   ├── app.py           # Main window
│   ├── chat.py          # Chat interface
│   ├── models_tab.py    # Model browser & downloader
│   ├── settings.py      # Settings panel
│   ├── privacy_tab.py   # Privacy controls
│   ├── system_tab.py    # System monitor
│   ├── wizard.py        # First-run setup wizard
│   └── splash.py        # Startup splash screen
│
├── modules/             # Optional modules
│   ├── agent.py         # Command execution
│   └── video.py         # Video generation (ComfyUI)
│
├── plugins/             # Extensible plugins
│   ├── calculator.py
│   ├── joke.py
│   ├── time_plugin.py
│   └── files.py
│
├── assets/              # Themes & internationalization
├── models/              # Downloaded AI models go here (or custom path)
├── logs/                # Application logs
└── crash_reports/       # Crash report files
```

---

## 📜 License

FreedomForge AI is licensed under **AGPL-3.0 + Commons Clause**.

- ✅ **Free for personal use** — always
- ✅ **Open source** — fork it, study it, improve it
- ❌ **Commercial use** (businesses over $250K revenue) requires a separate license
- ❌ **Reselling or rebranding** is not permitted

---

## 🙏 Credits

| Library | Purpose | Author |
|---------|---------|--------|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Modern GUI | Tom Schimansky |
| [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) | Local AI inference | Andrei Betlen |
| [SpeechRecognition](https://github.com/Uberi/speech_recognition) | Voice input | Anthony Zhang |
| [pyttsx3](https://github.com/nateshmbhat/pyttsx3) | Text-to-speech | Natesh M Bhat |
| [psutil](https://github.com/giampaolo/psutil) | System monitoring | Giampaolo Rodola |
| [HuggingFace](https://huggingface.co) | Model hosting | Hugging Face Inc. |
| TheBloke / bartowski | GGUF model conversions | Community |

---

*Built by Ryan Dennison. Free. Private. Yours. For everyone.*
