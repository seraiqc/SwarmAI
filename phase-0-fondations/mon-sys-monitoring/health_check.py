from datetime import datetime
from pathlib import Path


def load_alerts():
    config_path = Path("alerts.yml")
    if not config_path.exists():
        return {
            "latency_ms_warning": 500,
            "error_rate_warning": 5,
            "uptime_minimum_percent": 99
        }

    data = {}
    for line in config_path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("version:") or line.startswith("alerts:") or line.startswith("channels:"):
            continue
        if ":" in line and not line.startswith("-"):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    return {
        "latency_ms_warning": int(data.get("latency_ms_warning", 500)),
        "error_rate_warning": int(data.get("error_rate_warning", 5)),
        "uptime_minimum_percent": int(data.get("uptime_minimum_percent", 99))
    }


def check_health():
    alerts = load_alerts()

    current_latency = 120
    current_error_rate = 0
    current_uptime = 100

    status = "ok"
    issues = []

    if current_latency > alerts["latency_ms_warning"]:
        status = "warning"
        issues.append("latency too high")

    if current_error_rate > alerts["error_rate_warning"]:
        status = "warning"
        issues.append("error rate too high")

    if current_uptime < alerts["uptime_minimum_percent"]:
        status = "warning"
        issues.append("uptime below threshold")

    return {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "agents": ["sec-securite", "mem-archiviste", "cod-coder", "mon-sys-monitoring"],
        "latency_ms": current_latency,
        "error_rate": current_error_rate,
        "uptime_percent": current_uptime,
        "issues": issues
    }


if __name__ == "__main__":
    health = check_health()
    print("MON-SYS:", health)
