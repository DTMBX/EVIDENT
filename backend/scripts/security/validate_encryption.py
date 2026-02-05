import json
import subprocess
from pathlib import Path

CONFIG = Path("security/encryption_config.json")


def main() -> None:
    if not CONFIG.exists():
        raise SystemExit("Missing encryption config.")

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not config.get("encrypt_globs"):
        raise SystemExit("encrypt_globs is empty.")

    # Ensure hooks path is configured
    try:
        hooks_path = subprocess.check_output(["git", "config", "core.hooksPath"]).decode().strip()
    except subprocess.CalledProcessError:
        hooks_path = ""

    if hooks_path != ".githooks":
        raise SystemExit("core.hooksPath is not set to .githooks")

    print("Encryption configuration and hooks are present.")


if __name__ == "__main__":
    main()
