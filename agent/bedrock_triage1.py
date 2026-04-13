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
    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    )

    return response["output"]["message"]["content"][0]["text"]


def main():
    finding = load_finding("agent/sample_finding.json")
    prompt = build_prompt(finding)
    raw_response = invoke_model(prompt)

    print("=== Raw model response ===")
    print(raw_response)

    Path("agent/bedrock_plan.json").write_text(raw_response)
    print("Saved remediation plan to agent/bedrock_plan.json")


if __name__ == "__main__":
    main()