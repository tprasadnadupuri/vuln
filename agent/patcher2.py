import json
import shutil
from pathlib import Path


def load_plan(path: str) -> dict:
    raw = Path(path).read_text().strip()

    if not raw:
        raise ValueError(f"{path} is empty. Run bedrock_triage.py first.")

    if raw.startswith("```json"):
        raw = raw[len("```json"):].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    elif raw.startswith("```"):
        raw = raw[3:].strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    start = raw.find("{")
    end = raw.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"{path} does not contain a JSON object. Content: {raw[:200]!r}")

    raw = raw[start:end + 1]
    return json.loads(raw)


def backup_file(target_file: str):
    path = Path(target_file)
    backup = Path(f"{target_file}.bak")
    shutil.copy2(path, backup)
    print(f"Backup created: {backup}")


def replace_exact(target_file: str, search: str, replace: str):
    path = Path(target_file)
    content = path.read_text()

    if search not in content:
        print("=== Current file content ===")
        print(content)
        print("=== Expected search string ===")
        print(search)
        raise ValueError(f"Could not find exact text {search!r} in {target_file}")

    updated = content.replace(search, replace, 1)
    path.write_text(updated)
    print(f"Applied replace_exact to {target_file}")


def replace_line_contains(target_file: str, contains: str, replace_line: str):
    path = Path(target_file)
    lines = path.read_text().splitlines()

    replaced = False
    new_lines = []

    for line in lines:
        if not replaced and contains in line:
            new_lines.append(replace_line)
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        raise ValueError(f"Could not find line containing {contains!r} in {target_file}")

    path.write_text("\n".join(new_lines) + "\n")
    print(f"Applied replace_line_contains to {target_file}")


def insert_after_line_contains(target_file: str, contains: str, new_line: str):
    path = Path(target_file)
    lines = path.read_text().splitlines()

    inserted = False
    result = []

    for line in lines:
        result.append(line)
        if not inserted and contains in line:
            result.append(new_line)
            inserted = True

    if not inserted:
        raise ValueError(f"Could not find line containing {contains!r} in {target_file}")

    path.write_text("\n".join(result) + "\n")
    print(f"Applied insert_after_line_contains to {target_file}")


def apply_operation(op: dict):
    op_type = op["op"]

    if op_type == "replace_exact":
        replace_exact(
            target_file=op["target_file"],
            search=op["search"],
            replace=op["replace"]
        )
    elif op_type == "replace_line_contains":
        replace_line_contains(
            target_file=op["target_file"],
            contains=op["contains"],
            replace_line=op["replace_line"]
        )
    elif op_type == "insert_after_line_contains":
        insert_after_line_contains(
            target_file=op["target_file"],
            contains=op["contains"],
            new_line=op["new_line"]
        )
    elif op_type == "manual_review":
        raise ValueError(f"Manual review requested for {op.get('target_file')}: {op.get('reason')}")
    else:
        raise ValueError(f"Unsupported operation type: {op_type}")


if __name__ == "__main__":
    plan = load_plan("agent/bedrock_plan.json")

    if not plan.get("eligible"):
        print("Plan says manual review required")
        print(json.dumps(plan, indent=2))
        raise SystemExit(1)

    touched_files = set()
    for operation in plan.get("operations", []):
        target_file = operation.get("target_file")
        if target_file and target_file not in touched_files:
            backup_file(target_file)
            touched_files.add(target_file)

        apply_operation(operation)

    print(json.dumps({
        "status": "patched",
        "change_type": plan.get("change_type"),
        "requires_human_review": plan.get("requires_human_review", True)
    }, indent=2))