#!/usr/bin/env python3
"""
Test script for Replicate API connection
"""

import asyncio
import os
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, format_error_message

async def test_api_connection():
    """Test connection to Replicate API"""
    print("Testing Replicate API connection...")

    # Load API token
    token = load_api_token()
    if not token:
        print("❌ No API token found")
        print("Please set up your API token using the Replicate Config node in ComfyUI")
        return False

    try:
        # Test connection
        async with ReplicateClient(token) as client:
            # Try to list a few models
            models = await client.list_models(limit=5)

            if models:
                print(f"✅ Connection successful! Found {len(models)} models")
                print("\nAvailable models (first 5):")
                for model in models:
                    print(f"  - {model.owner}/{model.name}")
                    if model.description:
                        print(f"    {model.description[:100]}...")
                return True
            else:
                print("❌ No models found (unexpected)")
                return False

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"❌ Connection failed: {error_msg}")
        return False

def main():
    """Run the test"""
    print("Replicate API Connection Test")
    print("=" * 30)

    # Run async test
    success = asyncio.run(test_api_connection())

    if success:
        print("\n🎉 All tests passed! Your Replicate integration is ready to use.")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Check your API token is correct")
        print("2. Ensure you have internet connection")
        print("3. Verify your Replicate account is active")
        print("4. Check if you've reached API rate limits")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)