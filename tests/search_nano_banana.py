#!/usr/bin/env python3
"""
搜索nano banana模型的正确路径
"""

import asyncio
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, format_error_message

async def search_banana_model():
    """搜索banana相关模型"""
    print("=" * 60)
    print("搜索 Nano Banana 模型")
    print("=" * 60)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    try:
        async with ReplicateClient(token) as client:
            # 搜索多个关键词
            search_terms = ["banana", "nano banana", "nano-banana"]

            for term in search_terms:
                print(f"\n🔍 搜索: '{term}'")
                print("-" * 60)

                models = await client.list_models(search=term, limit=20)

                if models:
                    print(f"✅ 找到 {len(models)} 个模型:\n")
                    for i, model in enumerate(models, 1):
                        print(f"{i}. {model.owner}/{model.name}")
                        if model.description:
                            print(f"   描述: {model.description[:100]}...")
                        print()
                else:
                    print("   未找到相关模型")

            # 尝试一些可能的路径
            possible_paths = [
                ("fofr", "nano-banana"),
                ("fofr", "banana"),
                ("stability-ai", "banana"),
                ("replicate", "banana"),
            ]

            print("\n" + "=" * 60)
            print("尝试可能的模型路径")
            print("=" * 60)

            for owner, name in possible_paths:
                try:
                    print(f"\n🔍 尝试: {owner}/{name}")
                    details = await client.get_model_details(owner, name)
                    print(f"   ✅ 找到模型!")
                    print(f"   描述: {details.get('description', 'N/A')}")
                    print(f"   URL: {details.get('url')}")
                    return True
                except Exception as e:
                    print(f"   ❌ 未找到")

            return False

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 搜索失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行搜索"""
    asyncio.run(search_banana_model())

if __name__ == "__main__":
    main()