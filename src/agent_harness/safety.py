from pathlib import Path
import re

ALLOWED_SUFFIXES = {".py", ".md", ".toml", ".ini", ".cfg", ".txt", ".yaml", ".yml", ".json"}
EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "credentials", "secrets.json"}

def safe_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    candidate = Path(relative)
    if candidate.is_absolute():
        raise ValueError("Absolute paths are not permitted")
    if any(part == ".." for part in candidate.parts):
        raise ValueError("Parent-directory traversal is not permitted")
    target = (root / candidate).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path escapes approved project root")
    if target.name.lower() in SECRET_NAMES or target.name.lower().startswith(".env"):
        raise ValueError("Credential/configuration file access is blocked")
    if target.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("File extension is not allowed")
    if target.exists() and target.is_symlink():
        raise ValueError("Symlink access is blocked")
    return target

def redact(text: str) -> str:
    text = re.sub(r'(?i)(api[_-]?key|authorization|password|secret)(\s*[:=]\s*)[^\s,;]+', r'\1\2[REDACTED]', text)
    text = re.sub(r'\bsk-[A-Za-z0-9_-]{12,}\b', '[REDACTED_API_KEY]', text)
    return text
