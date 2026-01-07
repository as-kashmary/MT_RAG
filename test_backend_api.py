#!/usr/bin/env python3
"""
Quick Test Script for Backend API Endpoints
Tests the user authentication endpoints without frontend
"""

import requests
import json
import sys

API_BASE = "http://localhost:8001"

def test_signup():
    """Test user signup endpoint"""
    print("\n=== Testing Signup ===")
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password_hash": "hashed_password_123"
    }
    try:
        response = requests.post(f"{API_BASE}/users/create", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_login():
    """Test user login endpoint"""
    print("\n=== Testing Login ===")
    email = "testuser@example.com"
    password = "hashed_password_123"
    try:
        response = requests.get(
            f"{API_BASE}/users/login",
            params={"email": email, "password_hash": password}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_all_users():
    """Test get all users endpoint"""
    print("\n=== Testing Get All Users ===")
    try:
        response = requests.get(f"{API_BASE}/users/ids")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\n=== Testing CORS ===")
    try:
        response = requests.options(
            f"{API_BASE}/users/login",
            headers={"Origin": "http://localhost:5173"}
        )
        print(f"Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Backend API Test Suite")
    print("======================")
    print(f"Testing API at: {API_BASE}")
    
    results = {
        "CORS": test_cors(),
        "Signup": test_signup(),
        "Get All Users": test_get_all_users(),
        "Login": test_login(),
    }
    
    print("\n=== Test Results ===")
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
