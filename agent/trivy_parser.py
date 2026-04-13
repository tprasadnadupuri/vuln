import json
from pathlib import Path


SUPPORTED_TARGET_FILES = {
    "requirements.txt": "python_package",
    "Dockerfile": "dockerfile"
}


def load_trivy_report(path: str) -> dict:
    return json.loads(Path(path).read_text())


def find_python_dependency_vulnerability(report: dict):
    """
    Look through Trivy results and return the first Python package vulnerability
    that has a fixed version.
    """
    results = report.get("Results", [])

    for result in results:
        target = result.get("Target", "")
        vulnerabilities = result.get("Vulnerabilities") or []

        if "requirements.txt" not in target:
            continue

        for vuln in vulnerabilities:
            pkg_name = vuln.get("PkgName")
            installed_version = vuln.get("InstalledVersion")
            fixed_version = vuln.get("FixedVersion")
            severity = vuln.get("Severity")

            if pkg_name and installed_version and fixed_version:
                return {
                    "scanner": "trivy",
                    "image": "user-crud-lab:latest",
                    "finding": {
                        "severity": severity or "UNKNOWN",
                        "package_name": pkg_name,
                        "installed_version": installed_version,
                        "fixed_version": fixed_version,
                        "type": "python_package",
                        "file": "requirements.txt"
                    }
                }

    return None


def find_os_or_base_image_vulnerability(report: dict):
    """
    Optional fallback: if no requirements.txt vulnerability is found,
    look for a package vulnerability from the image OS packages.
    This does not directly know the fixed Dockerfile line, so we map
    it to a manual-review style normalized finding for now.
    """
    results = report.get("Results", [])

    for result in results:
        target = result.get("Target", "")
        vulnerabilities = result.get("Vulnerabilities") or []

        if "requirements.txt" in target:
            continue

        for vuln in vulnerabilities:
            pkg_name = vuln.get("PkgName")
            installed_version = vuln.get("InstalledVersion")
            fixed_version = vuln.get("FixedVersion")
            severity = vuln.get("Severity")

            if pkg_name and installed_version and fixed_version:
                return {
                    "scanner": "trivy",
                    "image": "user-crud-lab:latest",
                    "finding": {
                        "severity": severity or "UNKNOWN",
                        "package_name": pkg_name,
                        "installed_version": installed_version,
                        "fixed_version": fixed_version,
                        "type": "os_package",
                        "file": "Dockerfile"
                    }
                }

    return None


def build_normalized_finding(report: dict) -> dict:
    finding = find_python_dependency_vulnerability(report)
    if finding:
        return finding

    finding = find_os_or_base_image_vulnerability(report)
    if finding:
        return finding

    raise ValueError("No suitable vulnerability with a fixed version was found in trivy-report.json")


def main():
    report = load_trivy_report("trivy-report.json")
    normalized = build_normalized_finding(report)

    output_path = Path("agent/normalized_finding.json")
    output_path.write_text(json.dumps(normalized, indent=2))

    print("Saved normalized finding to agent/normalized_finding.json")
    print(json.dumps(normalized, indent=2))


if __name__ == "__main__":
    main()