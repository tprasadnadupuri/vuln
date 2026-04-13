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
You are a remediation planning assistant.

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

Rules:
- Prefer one bounded change.
- Do not modify application business logic.
- Only use these operation types:
  1. replace_exact
  2. replace_line_contains
  3. insert_after_line_contains
  4. manual_review
- For python_package findings, prefer changing requirements.txt.
- For base_image findings, prefer changing the Dockerfile FROM line.
- If the change is risky or unclear, return:
  "eligible": false
  "change_type": "manual_review"
  "operations": [
    {{
      "op": "manual_review",
      "target_file": "{finding["finding"].get("file", "")}",
      "reason": "..."
    }}
  ]

Operation schemas:

1) replace_exact
{{
  "op": "replace_exact",
  "target_file": "requirements.txt",
  "search": "requests==2.28.2",
  "replace": "requests==2.32.3"
}}

2) replace_line_contains
{{
  "op": "replace_line_contains",
  "target_file": "Dockerfile",
  "contains": "FROM python:3.11-slim",
  "replace_line": "FROM python:3.11-slim-bookworm"
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
  "target_file": "Dockerfile",
  "reason": "Major version change may be risky."
}}

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