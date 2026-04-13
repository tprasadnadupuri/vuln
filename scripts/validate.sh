#!/usr/bin/env bash
set -e

curl -s http://localhost:8081/health
echo
curl -s -X POST http://localhost:8081/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Tulasi","email":"tulasi@example.com"}'
echo
curl -s http://localhost:8081/users
echo