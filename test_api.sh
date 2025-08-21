#!/bin/bash

echo "🚀 Testing Farsight API..."
echo "=========================="

BASE_URL="http://localhost:8000"

echo -e "\n1. Testing root endpoint:"
curl -s "$BASE_URL/" | jq .

echo -e "\n2. Testing health check:"
curl -s "$BASE_URL/health" | jq .

echo -e "\n3. Getting all items (should be empty initially):"
curl -s "$BASE_URL/items" | jq .

echo -e "\n4. Creating a new item:"
curl -s -X POST "$BASE_URL/items?name=Test%20Item&description=This%20is%20a%20test%20item" | jq .

echo -e "\n5. Creating another item:"
curl -s -X POST "$BASE_URL/items?name=Second%20Item&description=Another%20test%20item" | jq .

echo -e "\n6. Getting all items again (should show our new items):"
curl -s "$BASE_URL/items" | jq .

echo -e "\n7. Getting specific item by ID:"
curl -s "$BASE_URL/items/1" | jq .

echo -e "\n8. Testing non-existent item (should return 404):"
curl -s "$BASE_URL/items/999" | jq .

echo -e "\n✅ API testing complete!"
