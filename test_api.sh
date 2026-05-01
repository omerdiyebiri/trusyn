#!/bin/bash
set -x
curl -v -X POST "http://localhost:8000/api/v1/login/access-token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@trusyn.io&password=password123" > token.json
TOKEN=$(cat token.json | jq -r .access_token)

curl -v -X POST "http://localhost:8000/api/v1/brands/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "TrusynBank", "official_domains": "trusynbank.com", "keywords": "bank,finance", "logo_url": ""}' > brand.json

cat brand.json
