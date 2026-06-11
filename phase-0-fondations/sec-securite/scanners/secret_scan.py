import sys
from pathlib import Path

SENSITIVE_WORDS = [
    "api_key",
    "api-key",
    "secret",
    "token",
    "password",
    "private_key",
    "private key",
    "aws_access_key_id",
    "aws_secret_access_key",
    "bearer",
]

SCAN_EXTS = {".py", ".js", ".ts", ".sh", ".yml", ".yaml", ".json", ".txt", ".env"}
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}
SKIP_FILES = {"README.md", "security_rules.yml", "vault_paths.yml", "alert_rules.yml"}


def is_text_file(path):
    return path.is_file() and (path.suffix.lower() in SCAN_EXTS or path.name == ".env")


def should_skip(path):
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_FILES:
        return True
    if path.name == "secret_scan.py":
        return True
    return False


def scan_file(path):
    findings = []
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception:
        return findings
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for word in SENSITIVE_WORDS:
            if word in low:
                findings.append(f"{path}:{i}: {line.strip()}")
                break
    return findings


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    findings = []
    for path in root.rglob("*"):
        if should_skip(path):
            continue
        if is_text_file(path):
            findings.extend(scan_file(path))
    if findings:
        print(
            "\
".join(findings)
        )
        sys.exit(1)
    print("SEC: scan clean")
    sys.exit(0)


if __name__ == "__main__":
    main()
