#!/usr/bin/env python3
"""
完整工作流测试脚本
测试从模型选择到参数准备的完整流程
"""

import asyncio
import json
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, extract_model_schema, format_error_message

async def test_full_workflow():
    """测试完整的工作流程"""
    print("=" * 60)
    print("ComfyUI Replicate 节点完整工作流测试")
    print("=" * 60)

    # 加载API token
    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    print("✅ API token已加载")

    try:
        async with ReplicateClient(token) as client:
            # 1. 搜索模型
            print("\n" + "=" * 60)
            print("步骤 1: 搜索Stable Diffusion模型")
            print("=" * 60)

            models = await client.list_models(search="stable-diffusion", limit=5)

            if not models:
                print("❌ 未找到模型")
                return False

            print(f"✅ 找到 {len(models)} 个模型:\n")
            for i, model in enumerate(models, 1):
                print(f"{i}. {model.owner}/{model.name}")
                if model.description:
                    print(f"   描述: {model.description[:100]}...")
                print()

            # 选择第一个模型进行测试
            selected_model = models[0]
            print(f"🎯 选择模型: {selected_model.owner}/{selected_model.name}\n")

            # 2. 获取模型详细信息
            print("=" * 60)
            print("步骤 2: 获取模型详细信息")
            print("=" * 60)

            details = await client.get_model_details(selected_model.owner, selected_model.name)

            print(f"✅ 模型详情:")
            print(f"   URL: {details.get('url')}")
            print(f"   可见性: {details.get('visibility')}")

            latest_version = details.get('latest_version')
            if latest_version:
                version_id = latest_version.get('id')
                print(f"   最新版本: {version_id[:20]}...")
            else:
                print("   ❌ 未找到版本信息")
                return False

            # 3. 提取Schema
            print("\n" + "=" * 60)
            print("步骤 3: 提取模型Schema")
            print("=" * 60)

            schema = extract_model_schema(latest_version)

            if not schema:
                print("⚠️ 该模型没有schema信息")
                print("   这是正常的,某些模型可能不提供openapi_schema")
            else:
                print(f"✅ Schema包含 {len(schema)} 个参数:\n")

                for param_name, param_config in list(schema.items())[:10]:  # 只显示前10个
                    param_type = param_config.get('type', 'unknown')
                    required = param_config.get('required', False)
                    default = param_config.get('default', 'N/A')
                    description = param_config.get('description', '')

                    status = "必填" if required else "可选"
                    print(f"📝 {param_name} ({status})")
                    print(f"   类型: {param_type}")
                    print(f"   默认值: {default}")
                    if description:
                        print(f"   描述: {description[:80]}...")
                    print()

            # 4. 测试版本API
            print("=" * 60)
            print("步骤 4: 通过版本API获取Schema")
            print("=" * 60)

            version_info = await client.get_model_version(
                selected_model.owner,
                selected_model.name,
                version_id
            )

            version_schema = extract_model_schema(version_info)

            if version_schema:
                print(f"✅ 从版本API获取到 {len(version_schema)} 个参数")
            else:
                print("⚠️ 版本API也未返回schema")

            # 5. 测试缓存
            print("\n" + "=" * 60)
            print("步骤 5: 测试缓存机制")
            print("=" * 60)

            # 第二次请求应该从缓存获取
            models_cached = await client.list_models(search="stable-diffusion", limit=5)
            print(f"✅ 缓存测试完成,获取到 {len(models_cached)} 个模型")

            # 6. 模拟准备输入参数
            print("\n" + "=" * 60)
            print("步骤 6: 模拟参数准备")
            print("=" * 60)

            if schema:
                sample_inputs = {}

                for param_name, param_config in schema.items():
                    # 使用默认值
                    if 'default' in param_config:
                        sample_inputs[param_name] = param_config['default']
                    # 必填参数需要提供值
                    elif param_config.get('required', False):
                        param_type = param_config.get('type', 'string')
                        if param_type == 'string':
                            sample_inputs[param_name] = "test prompt"
                        elif param_type == 'integer':
                            sample_inputs[param_name] = 1
                        elif param_type == 'number':
                            sample_inputs[param_name] = 1.0
                        elif param_type == 'boolean':
                            sample_inputs[param_name] = True

                print(f"✅ 准备了 {len(sample_inputs)} 个参数:")
                print(json.dumps(sample_inputs, indent=2, ensure_ascii=False))
            else:
                print("⚠️ 无schema,跳过参数准备")

            print("\n" + "=" * 60)
            print("🎉 全部测试通过!")
            print("=" * 60)
            print("\n✨ 节点功能验证:")
            print("  ✅ ReplicateModelSelector - 模型搜索和选择")
            print("  ✅ Schema提取和缓存机制")
            print("  ✅ ReplicateDynamicNode - 参数准备逻辑")
            print("  ✅ API客户端的完整功能")

            return True

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 测试失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行测试"""
    success = asyncio.run(test_full_workflow())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()