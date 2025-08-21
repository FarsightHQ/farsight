#!/usr/bin/env python3
"""
Python script to test the Farsight API
Requires: pip install requests
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api():
    print("🐍 Testing Farsight API with Python...")
    print("=" * 40)
    
    try:
        # Test 1: Root endpoint
        print("\n1. Testing root endpoint:")
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 2: Health check
        print("\n2. Testing health check:")
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 3: Get all items (initially empty)
        print("\n3. Getting all items (should be empty initially):")
        response = requests.get(f"{BASE_URL}/items")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test 4: Create items
        print("\n4. Creating items:")
        items_to_create = [
            {"name": "Python Test Item", "description": "Created via Python script"},
            {"name": "API Test", "description": "Testing the API endpoints"},
            {"name": "FastAPI Demo", "description": "Demonstrating FastAPI capabilities"}
        ]
        
        created_items = []
        for item in items_to_create:
            response = requests.post(f"{BASE_URL}/items", params=item)
            print(f"Created item: Status {response.status_code}")
            if response.status_code == 200:
                created_item = response.json()
                created_items.append(created_item)
                print(f"  -> ID: {created_item['id']}, Name: {created_item['name']}")
        
        # Test 5: Get all items again
        print("\n5. Getting all items after creation:")
        response = requests.get(f"{BASE_URL}/items")
        print(f"Status: {response.status_code}")
        items = response.json()
        print(f"Total items: {len(items)}")
        for item in items:
            print(f"  - {item['name']} (ID: {item['id']})")
        
        # Test 6: Get specific items
        print("\n6. Testing individual item retrieval:")
        for item in created_items[:2]:  # Test first 2 items
            response = requests.get(f"{BASE_URL}/items/{item['id']}")
            print(f"Item {item['id']}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"  -> {response.json()['name']}")
        
        # Test 7: Test error handling
        print("\n7. Testing error handling (non-existent item):")
        response = requests.get(f"{BASE_URL}/items/9999")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        print("\n✅ All tests completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the service is running.")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    test_api()
