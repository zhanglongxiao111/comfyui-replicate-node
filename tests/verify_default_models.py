#!/usr/bin/env python3
"""
验证默认模型列表
"""

import asyncio
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, extract_model_schema, format_error_message

async def verify_models():
    """验证默认模型"""
    print("=" * 80)
    print("验证默认模型列表")
    print("=" * 80)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    # 要验证的模型列表
    default_models = [
        {
            "name": "Nano Banana (Gemini 2.5 Flash Image)",
            "owner": "google",
            "model": "nano-banana",
            "description": "Google最新的图像编辑和生成模型"
        },
        {
            "name": "Qwen Image Edit",
            "owner": "qwen",
            "model": "qwen-image-edit",
            "description": "Qwen官方图像编辑模型"
        }
    ]

    verified_models = []

    try:
        async with ReplicateClient(token) as client:
            for model_info in default_models:
                print(f"\n{'=' * 80}")
                print(f"验证模型: {model_info['name']}")
                print(f"路径: {model_info['owner']}/{model_info['model']}")
                print(f"{'=' * 80}")

                try:
                    # 获取模型详情
                    details = await client.get_model_details(
                        model_info['owner'],
                        model_info['model']
                    )

                    print(f"\n✅ 模型存在!")
                    print(f"   URL: {details.get('url')}")
                    print(f"   描述: {details.get('description', 'N/A')[:150]}...")
                    print(f"   运行次数: {details.get('run_count', 'N/A'):,}")
                    print(f"   可见性: {details.get('visibility')}")

                    # 获取版本信息
                    latest_version = details.get('latest_version')
                    if latest_version:
                        version_id = latest_version.get('id')
                        print(f"   版本ID: {version_id[:40]}...")

                        # 提取Schema
                        schema = extract_model_schema(latest_version)
                        if schema:
                            print(f"   参数数量: {len(schema)}")
                            print(f"   参数列表: {', '.join(list(schema.keys())[:5])}...")

                        # 保存验证通过的模型
                        verified_models.append({
                            **model_info,
                            "version_id": version_id,
                            "url": details.get('url'),
                            "run_count": details.get('run_count', 0),
                            "full_description": details.get('description', ''),
                            "schema_params": list(schema.keys()) if schema else []
                        })
                    else:
                        print(f"   ⚠️ 未找到版本信息")

                except Exception as e:
                    print(f"\n❌ 验证失败: {format_error_message(e)}")
                    print(f"   可能的原因:")
                    print(f"   1. 模型路径不正确")
                    print(f"   2. 模型已被删除或私有")
                    print(f"   3. API权限问题")

            # 输出总结
            print("\n" + "=" * 80)
            print("验证总结")
            print("=" * 80)

            print(f"\n✅ 验证通过: {len(verified_models)}/{len(default_models)}")

            if verified_models:
                print("\n通过验证的模型:")
                for i, model in enumerate(verified_models, 1):
                    print(f"\n{i}. {model['name']}")
                    print(f"   路径: {model['owner']}/{model['model']}")
                    print(f"   URL: {model['url']}")
                    print(f"   运行次数: {model['run_count']:,}")

                # 生成配置文件
                import json
                config = {
                    "default_models": verified_models,
                    "verified_at": "2025-10-19"
                }

                config_file = "default_models_config.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                print(f"\n💾 配置已保存到: {config_file}")

            return len(verified_models) > 0

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 验证失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行验证"""
    success = asyncio.run(verify_models())

    if success:
        print("\n" + "=" * 80)
        print("🎉 验证完成!")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 更新ComfyUI节点以使用这些默认模型")
        print("  2. 在模型选择器中添加预设选项")
        print("  3. 提供快速选择界面")
    else:
        print("\n❌ 验证失败,请检查模型路径")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()