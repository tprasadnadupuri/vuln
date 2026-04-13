import json
from pathlib import Path


def load_plan(path: str) -> dict:
    return json.loads(Path(path).read_text())


def apply_patch(target_file: str, search: str, replace: str):
    path = Path(target_file)
    content = path.read_text()

    if search not in content:
        raise ValueError(f"Could not find '{search}' in {target_file}")

    updated = content.replace(search, replace, 1)
    path.write_text(updated)


if __name__ == "__main__":
    plan = load_plan("agent/bedrock_plan.json")

    if not plan.get("eligible"):
        print("Plan says manual review required")
        raise SystemExit(1)

    apply_patch(
        target_file=plan["target_file"],
        search=plan["search"],
        replace=plan["replace"]
    )

    print(json.dumps({
        "status": "patched",
        "file": plan["target_file"],
        "requires_human_review": plan.get("requires_human_review", True)
    }, indent=2))