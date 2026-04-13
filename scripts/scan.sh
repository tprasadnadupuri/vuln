#!/usr/bin/env bash
set -e

if ! command -v trivy >/dev/null 2>&1; then
  echo "Trivy is not installed."
  echo "Install it on macOS with: brew install trivy"
  exit 1
fi

trivy image --format json -o trivy-report.json user-crud-lab:latest
echo "Saved report to trivy-report.json"