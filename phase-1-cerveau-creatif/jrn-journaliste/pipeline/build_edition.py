from pathlib import Path
from datetime import datetime


def build_edition():
    template = Path("sources/news_template.md")
    editions_dir = Path("editions")
    editions_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = editions_dir / f"edition-{date_str}.md"

    if template.exists():
        output_file.write_text(template.read_text(errors="ignore"))
        print(f"JRN: edition created -> {output_file}")
    else:
        print("JRN: template missing")


if __name__ == "__main__":
    build_edition()
