#!/usr/bin/env python3
# ============================================================
#  FreedomForge AI
#  Copyright (c) 2026 Ryan Dennison
#  Licensed under AGPL-3.0 + Commons Clause
#
#  Dedicated to Miranda.
#  She will never be forgotten.
#
#  Built by Ryan Dennison for his son and the world.
#  Utilizing AI assistance.
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.paths import ensure_dirs
ensure_dirs()

from core import logger, config, encryption, crash_reporter

def _bootstrap():
    config.load_config()
    logger.init()
    logger.info("FreedomForge AI starting")
    crash_reporter.install_handler()
    encryption.init_encryption(manual_key=config.get("manual_encryption_key"))

_bootstrap()

from ui.app import App


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
