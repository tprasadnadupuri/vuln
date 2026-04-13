from pathlib import Path
import json

from triage import load_finding, classify_finding


def apply_patch(target_file: str, search: str, replace: str):
    path = Path(target_file)
    content = path.read_text()

    if search not in content:
        raise ValueError(f"Could not find '{search}' in {target_file}")

    updated = content.replace(search, replace, 1)
    path.write_text(updated)


if __name__ == "__main__":
    finding = load_finding("agent/sample_finding.json")
    plan = classify_finding(finding)

    if not plan["eligible"]:
        print("Manual review required")
        raise SystemExit(1)

    apply_patch(
        target_file=plan["target_file"],
        search=plan["search"],
        replace=plan["replace"]
    )

    print(json.dumps({
        "status": "patched",
        "file": plan["target_file"]
    }, indent=2))