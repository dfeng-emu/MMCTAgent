#!/bin/bash
# Assigns RBAC roles to a user principal on all MMCT Azure resources.
# Usage: ./04-assign-user-roles.sh <user-email>
# Requires: Owner or User Access Administrator role (elevate via PIM first)

set -e
export MSYS_NO_PATHCONV=1

USER_PRINCIPAL="${1:?Usage: $0 <user-email>}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/00-setup-env-vars.sh"

subscriptionId=$(az account show --query id -o tsv)
echo "Subscription: $subscriptionId"
echo "Assigning roles to: $USER_PRINCIPAL"
echo ""

# Role assignments: resourceName|role|resourceType
assignments=(
  "$storageAccountName|Storage Blob Data Contributor|Microsoft.Storage/storageAccounts"
  "$aiSearchServiceName|Search Index Data Contributor|Microsoft.Search/searchServices"
  "$aiSearchServiceName|Search Service Contributor|Microsoft.Search/searchServices"
  "$azureSpeechServiceName|Cognitive Services Speech Contributor|Microsoft.CognitiveServices/accounts"
  "$eventhubName|Azure Event Hubs Data Owner|Microsoft.EventHub/namespaces"
)

for entry in "${assignments[@]}"; do
  IFS='|' read -r resourceName role resourceType <<< "$entry"

  RESOURCE_SCOPE="/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/$resourceType/$resourceName"

  echo "Assigning '$role' on '$resourceName'..."
  if az role assignment create \
    --assignee "$USER_PRINCIPAL" \
    --role "$role" \
    --scope "$RESOURCE_SCOPE" \
    --output none 2>&1; then
    echo "  Done."
  else
    echo "  FAILED — may need Owner/UAA elevation via PIM."
  fi
  echo ""
done

echo "All role assignments complete."
