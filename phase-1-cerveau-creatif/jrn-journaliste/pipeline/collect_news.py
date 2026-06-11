from pathlib import Path


def collect_sources():
    source_file = Path("sources/rss_sources.yml")
    if not source_file.exists():
        print("JRN: no source file")
        return

    print("JRN: sources ready")
    print(source_file.read_text(errors="ignore"))


if __name__ == "__main__":
    collect_sources()
