import json
from pathlib import Path


def load_finding(path: str) -> dict:
    return json.loads(Path(path).read_text())


def classify_finding(finding: dict) -> dict:
    vuln = finding["finding"]
    pkg_type = vuln["type"]

    if pkg_type == "python_package":
        return {
            "eligible": True,
            "classification": "dependency_fix",
            "target_file": vuln["file"],
            "search": f'{vuln["package_name"]}=={vuln["installed_version"]}',
            "replace": f'{vuln["package_name"]}=={vuln["fixed_version"]}'
        }

    return {
        "eligible": False,
        "classification": "manual_review"
    }


if __name__ == "__main__":
    finding = load_finding("agent/sample_finding.json")
    plan = classify_finding(finding)
    print(json.dumps(plan, indent=2))