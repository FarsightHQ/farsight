#!/bin/bash

# Quick IP Rules Lookup Script
# Usage: ./ip_lookup.sh 10.177.58.43

if [ -z "$1" ]; then
    echo "Usage: $0 <IP_ADDRESS>"
    echo "Example: $0 10.177.58.43"
    exit 1
fi

IP_ADDRESS=$1
API_BASE="http://localhost:8000/api/v1"

echo "🔍 Looking up firewall rules for IP: $IP_ADDRESS"
echo "=" $(printf "%0.s=" {1..50})

echo ""
echo "📊 SUMMARY:"
curl -s "$API_BASE/ip/$IP_ADDRESS/summary" | jq -r '
"📍 IP Address: \(.ip_address)",
"📈 Total Rules: \(.total_rules)",
"",
"🚀 Can reach (\(.can_reach | length) destinations):",
(.can_reach[] | "  → \(.)"),
"",
"🎯 Can be reached by (\(.can_be_reached_by | length) sources):",
(.can_be_reached_by[] | "  ← \(.)"),
"",
"🔧 Services:",
(.services[] | "  📡 \(.)")
'

echo ""
echo "=" $(printf "%0.s=" {1..50})
echo "💡 For detailed rules: curl $API_BASE/ip/$IP_ADDRESS/rules"
echo "💡 Interactive docs: http://localhost:8000/docs"
