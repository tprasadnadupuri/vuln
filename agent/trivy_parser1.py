import json
import sys
from pathlib import Path

SEVERITY_RANK = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 0,
}


def load_trivy_report(path: str) -> dict:
    return json.loads(Path(path).read_text())


def is_python_result(result: dict) -> bool:
    result_type = (result.get("Type") or "").lower()
    result_class = (result.get("Class") or "").lower()
    target = (result.get("Target") or "").lower()

    return (
        result_type in {"pip", "python-pkg", "poetry"} or
        result_class == "lang-pkgs" or
        "requirements.txt" in target or
        "site-packages" in target
    )


def is_os_result(result: dict) -> bool:
    result_type = (result.get("Type") or "").lower()
    result_class = (result.get("Class") or "").lower()

    return result_type in {"debian", "alpine", "rpm", "os"} or result_class == "os-pkgs"


def choose_best(candidates: list[dict], preferred_package: str | None = None) -> dict | None:
    if not candidates:
        return None

    if preferred_package:
        for c in candidates:
            if c["package_name"].lower() == preferred_package.lower():
                return c

    return sorted(
        candidates,
        key=lambda x: SEVERITY_RANK.get(x["severity"], 0),
        reverse=True
    )[0]


def collect_candidates(report: dict, mode: str) -> list[dict]:
    results = report.get("Results", [])
    candidates = []

    for result in results:
        vulnerabilities = result.get("Vulnerabilities") or []

        for vuln in vulnerabilities:
            pkg_name = vuln.get("PkgName")
            installed_version = vuln.get("InstalledVersion")
            fixed_version = vuln.get("FixedVersion")
            severity = vuln.get("Severity", "UNKNOWN")

            if not (pkg_name and installed_version and fixed_version):
                continue

            if mode == "python" and is_python_result(result):
                candidates.append({
                    "severity": severity,
                    "package_name": pkg_name,
                    "installed_version": installed_version,
                    "fixed_version": fixed_version,
                    "type": "python_package",
                    "file": "requirements.txt"
                })

            elif mode == "os" and is_os_result(result):
                candidates.append({
                    "severity": severity,
                    "package_name": pkg_name,
                    "installed_version": installed_version,
                    "fixed_version": fixed_version,
                    "type": "os_package",
                    "file": "Dockerfile"
                })

    return candidates


def build_normalized_finding(report: dict, mode: str, preferred_package: str | None = None) -> dict:
    candidates = collect_candidates(report, mode)
    chosen = choose_best(candidates, preferred_package=preferred_package)

    if not chosen:
        raise ValueError(f"No suitable {mode} vulnerability with fixed version found in trivy-report.json")

    return {
        "scanner": "trivy",
        "image": "user-crud-lab:latest",
        "finding": chosen
    }


def main():
    mode = "python"
    preferred_package = None

    if len(sys.argv) > 1:
        mode = sys.argv[1].strip().lower()
    if len(sys.argv) > 2:
        preferred_package = sys.argv[2].strip()

    if mode not in {"python", "os"}:
        raise ValueError("Mode must be either 'python' or 'os'")

    report = load_trivy_report("trivy-report.json")
    normalized = build_normalized_finding(report, mode, preferred_package)

    output_path = Path("agent/normalized_finding.json")
    output_path.write_text(json.dumps(normalized, indent=2))

    print(f"Saved normalized finding to {output_path}")
    print(json.dumps(normalized, indent=2))


if __name__ == "__main__":
    main()
