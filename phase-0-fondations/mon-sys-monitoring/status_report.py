import json
from pathlib import Path
from health_check import check_health


def save_status_report():
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    health = check_health()
    timestamp = health["timestamp"].replace(":", "-").replace(".", "-")
    output_file = reports_dir / f"status-{timestamp}.json"

    output_file.write_text(json.dumps(health, indent=2))
    print(f"MON-SYS: report saved -> {output_file}")


if __name__ == "__main__":
    save_status_report()
