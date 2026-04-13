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
You are a remediation planning assistant for a container security lab.

Your job:
1. Read the vulnerability finding.
2. Produce a SAFE remediation plan.
3. Return ONLY valid JSON.
4. Prefer a bounded change.
5. Do not modify application logic.
6. For python_package findings, prefer changing requirements.txt.
7. If the change looks risky or unclear, require human review.

Return JSON with exactly these keys:
eligible
classification
target_file
search
replace
requires_human_review
reason

Finding JSON:
{json.dumps(finding, indent=2)}
""".strip()


def invoke_model(prompt: str) -> str:
    # This body shape is a simple starter for text invocation.
    # Keep the model fixed for the lab and adjust if you switch model families.
    body = {
        "inputText": prompt
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    return response["body"].read().decode("utf-8")


def main():
    finding = load_finding("agent/sample_finding.json")
    prompt = build_prompt(finding)
    raw_response = invoke_model(prompt)

    print("=== Raw model response ===")
    print(raw_response)


if __name__ == "__main__":
    main()