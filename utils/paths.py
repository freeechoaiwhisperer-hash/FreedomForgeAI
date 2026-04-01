"""Centralised path definitions and version for FreedomForge AI."""
from pathlib import Path

APP_VERSION = "0.1.0-alpha"

APP_ROOT    = Path(__file__).resolve().parent.parent
MODELS_DIR  = APP_ROOT / "models"
LOGS_DIR    = APP_ROOT / "logs"
CRASH_DIR   = APP_ROOT / "crash_reports"
ASSETS_DIR  = APP_ROOT / "assets"
CONFIG_FILE = APP_ROOT / "config.json"
KEY_FILE    = APP_ROOT / ".forge_key"

# Training directories
TRAINING_DIR = APP_ROOT / "training"
ADAPTERS_DIR = TRAINING_DIR / "adapters"  # persistent training state per model
PRACTICE_DIR = TRAINING_DIR / "practice"  # logs of practice runs
EXAMPLES_DIR = TRAINING_DIR / "examples"  # (future) user-provided examples
RATINGS_DIR = TRAINING_DIR / "ratings"    # (future) user ratings


def ensure_dirs() -> None:
    """Create all required application directories."""
    for d in (MODELS_DIR, LOGS_DIR, CRASH_DIR, ASSETS_DIR,
              TRAINING_DIR, ADAPTERS_DIR, PRACTICE_DIR,
              EXAMPLES_DIR, RATINGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
