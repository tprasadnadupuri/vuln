import json
import os
from pathlib import Path

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def load_finding(path: str) -> dict:
    return json.loads(Path(path).read_text())


def build_prompt(finding: dict) -> str:
    return f"""
You are a remediation planning assistant for container vulnerability remediation.

Return ONLY one valid JSON object.
Do not include markdown.
Do not include explanations outside JSON.
Do not include triple backticks.

Required top-level keys:
eligible
change_type
operations
requires_human_review
reason

Allowed operation types:
1. replace_exact
2. replace_line_contains
3. insert_after_line_contains
4. manual_review

Important rules:

General:
- Prefer one bounded change.
- Do not modify application business logic.
- Do not invent files that do not exist.
- All operations must target real lines likely to exist in the target file.

For python_package findings:
- Only use replace_exact for requirements.txt if the vulnerable package is directly declared there.
- If the vulnerable package is NOT directly declared in requirements.txt, treat it as a transitive dependency.
- For transitive dependencies, return manual_review.
- Do not invent a new package declaration in requirements.txt.

For os_package findings:
- Do NOT use the OS package name (for example libssl3, openssl, zlib) as the "contains" value for Dockerfile edits.
- Dockerfile edits must target a real Dockerfile line, usually the FROM line.
- Prefer replacing the Dockerfile FROM line with a newer patched base image tag if a safe bounded change is possible.
- If no safe base image change can be inferred, return manual_review.

Operation schemas:

1) replace_exact
{{
  "op": "replace_exact",
  "target_file": "requirements.txt",
  "search": "requests==2.28.2",
  "replace": "requests==2.31.0"
}}

2) replace_line_contains
{{
  "op": "replace_line_contains",
  "target_file": "Dockerfile",
  "contains": "FROM python:3.11-slim-bookworm",
  "replace_line": "FROM python:3.11.15-slim-bookworm"
}}

3) insert_after_line_contains
{{
  "op": "insert_after_line_contains",
  "target_file": "Dockerfile",
  "contains": "COPY requirements.txt .",
  "new_line": "RUN pip install --no-cache-dir --upgrade pip"
}}

4) manual_review
{{
  "op": "manual_review",
  "target_file": "requirements.txt",
  "reason": "Transitive dependency or unclear remediation"
}}

If the finding is python_package and the package is directly in requirements.txt, a good response looks like:
{{
  "eligible": true,
  "change_type": "dependency_fix",
  "operations": [
    {{
      "op": "replace_exact",
      "target_file": "requirements.txt",
      "search": "requests==2.28.2",
      "replace": "requests==2.31.0"
    }}
  ],
  "requires_human_review": false,
  "reason": "Direct dependency can be safely updated."
}}

If the finding is python_package but the package appears to be transitive, a good response looks like:
{{
  "eligible": false,
  "change_type": "manual_review",
  "operations": [
    {{
      "op": "manual_review",
      "target_file": "requirements.txt",
      "reason": "Package appears transitive and is not directly declared in requirements.txt."
    }}
  ],
  "requires_human_review": true,
  "reason": "Transitive dependency remediation requires parent dependency analysis."
}}

If the finding is os_package, a good response looks like:
{{
  "eligible": true,
  "change_type": "base_image_fix",
  "operations": [
    {{
      "op": "replace_line_contains",
      "target_file": "Dockerfile",
      "contains": "FROM python:3.11-slim-bookworm",
      "replace_line": "FROM python:3.11.15-slim-bookworm"
    }}
  ],
  "requires_human_review": true,
  "reason": "OS-level vulnerability should be addressed through a patched base image."
}}

If the finding is os_package and the safe base image fix is unclear, return manual_review.

Finding:
{json.dumps(finding, indent=2)}
""".strip()


def invoke_model(prompt: str) -> str:
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": prompt}
                ]
            }
        ]
    )
    return response["output"]["message"]["content"][0]["text"]


def main():
    import sys

    input_file = "agent/normalized_finding.json"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    finding = load_finding(input_file)
    prompt = build_prompt(finding)
    raw_response = invoke_model(prompt)

    print("=== Raw model response ===")
    print(raw_response)

    Path("agent/bedrock_plan.json").write_text(raw_response)
    print("Saved remediation plan to agent/bedrock_plan.json")


if __name__ == "__main__":
    main()
