#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "🔑 Fetching gcloud OAuth access token..."
ACCESS_TOKEN=$(gcloud auth print-access-token)

echo "🚀 Initializing Terraform..."
terraform init

echo "📋 Planning Terraform deployment..."
terraform plan -var="access_token=${ACCESS_TOKEN}" -out=tfplan

echo "⚡ Applying Terraform deployment..."
terraform apply -auto-approve tfplan

echo "🎉 Terraform deployment finished successfully!"
terraform output
