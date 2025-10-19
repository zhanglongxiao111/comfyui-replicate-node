#!/usr/bin/env python3
"""
简单测试预设模型列表
"""

import asyncio
from replicate_client import ReplicateClient
from utils import load_api_token

async def test_preset_models():
    """测试两个预设模型"""
    print("=" * 80)
    print("测试预设模型")
    print("=" * 80)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    # 预设模型列表
    presets = [
        ("google/nano-banana", "Nano Banana (Gemini 2.5 Flash Image)"),
        ("qwen/qwen-image-edit", "Qwen Image Edit")
    ]

    results = []

    async with ReplicateClient(token) as client:
        for model_path, model_name in presets:
            print(f"\n{'=' * 80}")
            print(f"测试: {model_name}")
            print(f"路径: {model_path}")
            print(f"{'=' * 80}")

            try:
                owner, name = model_path.split('/')

                # 获取模型详情
                details = await client.get_model_details(owner, name)

                print(f"\n✅ 模型可用!")
                print(f"   URL: {details.get('url')}")
                print(f"   描述: {details.get('description', '')[:150]}...")
                print(f"   运行次数: {details.get('run_count', 0):,}")

                # 获取版本和schema
                latest_version = details.get('latest_version')
                if latest_version:
                    version_id = latest_version.get('id')
                    print(f"   版本ID: {version_id[:40]}...")

                    # 提取schema
                    from utils import extract_model_schema
                    schema = extract_model_schema(latest_version)

                    if schema:
                        print(f"   参数数量: {len(schema)}")
                        print(f"   参数列表: {', '.join(list(schema.keys())[:5])}...")
                        results.append((model_name, True, len(schema)))
                    else:
                        print(f"   ⚠️ 未找到schema")
                        results.append((model_name, True, 0))
                else:
                    print(f"   ⚠️ 未找到版本信息")
                    results.append((model_name, False, 0))

            except Exception as e:
                print(f"\n❌ 失败: {e}")
                results.append((model_name, False, 0))

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    success_count = sum(1 for _, success, _ in results if success)
    print(f"\n✅ 通过: {success_count}/{len(results)}\n")

    for name, success, params in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if success and params > 0:
            print(f"   参数: {params}个")

    print("\n" + "=" * 80)
    print("ComfyUI节点配置")
    print("=" * 80)

    print("\n预设模型列表已添加到 ReplicateModelSelector 节点:")
    print("  1. google/nano-banana (默认)")
    print("  2. qwen/qwen-image-edit")
    print("  3. stability-ai/sdxl")
    print("  4. black-forest-labs/flux-schnell")
    print("  5. Custom (use search)")

    print("\n💡 使用方法:")
    print("  1. 在ComfyUI中添加 'Replicate Model Selector' 节点")
    print("  2. 从 'model_preset' 下拉菜单选择预设模型")
    print("  3. 选择 'Custom' 时可以使用 'search_query' 搜索其他模型")

    return success_count == len(results)

def main():
    success = asyncio.run(test_preset_models())

    if success:
        print("\n🎉 所有预设模型测试通过!")
    else:
        print("\n❌ 部分测试失败")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())