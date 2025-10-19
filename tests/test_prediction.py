#!/usr/bin/env python3
"""
真实预测测试
使用一个简单的模型进行实际预测测试
"""

import asyncio
import json
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, extract_model_schema, format_error_message

async def test_prediction():
    """测试真实的预测执行"""
    print("=" * 60)
    print("Replicate 预测执行测试")
    print("=" * 60)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    try:
        async with ReplicateClient(token) as client:
            # 使用一个简单快速的模型进行测试
            # 这个模型是hello-world示例,非常快
            owner = "replicate"
            name = "hello-world"

            print(f"\n🎯 测试模型: {owner}/{name}")
            print("   这是一个简单的测试模型,会快速返回结果")

            # 获取模型详情
            print("\n📋 获取模型信息...")
            details = await client.get_model_details(owner, name)

            latest_version = details.get('latest_version')
            if not latest_version:
                print("❌ 未找到模型版本")
                return False

            version_id = latest_version.get('id')
            print(f"✅ 版本ID: {version_id}")

            # 提取schema
            schema = extract_model_schema(latest_version)
            if schema:
                print(f"\n📝 模型参数:")
                for param_name, param_config in schema.items():
                    print(f"   - {param_name}: {param_config.get('type', 'unknown')}")
            else:
                print("\n⚠️ 该模型没有详细的schema")

            # 准备输入 - hello-world模型接受一个text参数
            inputs = {
                "text": "ComfyUI Replicate节点测试"
            }

            print(f"\n💬 输入参数:")
            print(json.dumps(inputs, indent=2, ensure_ascii=False))

            # 创建预测
            print("\n🚀 创建预测...")
            prediction = await client.create_prediction(
                version_id=version_id,
                inputs=inputs
            )

            print(f"✅ 预测已创建: {prediction.id}")
            print(f"   状态: {prediction.status}")

            # 等待完成
            print("\n⏳ 等待预测完成...")
            result = await client.wait_for_prediction(
                prediction_id=prediction.id,
                timeout=60,
                poll_interval=1
            )

            print(f"\n✅ 预测完成!")
            print(f"   最终状态: {result.status}")

            if result.status == 'succeeded':
                print(f"\n🎉 输出结果:")
                print(json.dumps(result.output, indent=2, ensure_ascii=False))

                if result.logs:
                    print(f"\n📜 执行日志:")
                    print(result.logs)

                print(f"\n⏱️ 耗时:")
                print(f"   创建时间: {result.created_at}")
                print(f"   完成时间: {result.completed_at}")

                return True
            else:
                print(f"\n❌ 预测失败")
                if result.error:
                    print(f"   错误: {result.error}")
                return False

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 测试失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行测试"""
    print("\n⚠️ 注意: 这个测试将使用你的Replicate API配额")
    print("   hello-world模型是免费的,不会产生费用\n")

    success = asyncio.run(test_prediction())

    if success:
        print("\n" + "=" * 60)
        print("🎊 完整预测流程测试通过!")
        print("=" * 60)
        print("\n✨ 验证的功能:")
        print("  ✅ 模型信息获取")
        print("  ✅ Schema提取")
        print("  ✅ 预测创建")
        print("  ✅ 异步状态轮询")
        print("  ✅ 结果获取")
        print("\n🚀 ComfyUI Replicate节点已准备就绪!")
    else:
        print("\n❌ 测试失败,请检查错误信息")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()