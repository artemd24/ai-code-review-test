from pathlib import Path

SERVICE_ROOT_DIR = Path(__file__).parent.parent.resolve()
DOT_ENV_PATH = SERVICE_ROOT_DIR.parent / ".env"
TMP_PATH = SERVICE_ROOT_DIR.parent / "tmp"
