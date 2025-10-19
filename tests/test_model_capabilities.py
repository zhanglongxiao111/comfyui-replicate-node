#!/usr/bin/env python3
"""
测试特定模型的能力
检查qwen-imgedit和nano-banana模型的输出和并发能力
"""

import asyncio
import json
import sys
from replicate_client import ReplicateClient
from utils import load_api_token, extract_model_schema, format_error_message

async def test_model_capabilities():
    """测试模型能力"""
    print("=" * 80)
    print("Replicate 模型能力测试")
    print("=" * 80)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    try:
        async with ReplicateClient(token) as client:
            # 要测试的模型
            models_to_test = [
                {
                    "name": "Qwen Image Edit",
                    "owner": "espressotechie",
                    "model": "qwen-imgedit-4bit"
                },
                {
                    "name": "Nano Banana (Gemini 2.5 Flash Image)",
                    "owner": "google",
                    "model": "nano-banana"
                }
            ]

            all_results = {}

            for model_info in models_to_test:
                print("\n" + "=" * 80)
                print(f"📋 测试模型: {model_info['name']} ({model_info['owner']}/{model_info['model']})")
                print("=" * 80)

                try:
                    # 获取模型详情
                    details = await client.get_model_details(model_info['owner'], model_info['model'])

                    print(f"\n✅ 模型信息:")
                    print(f"   描述: {details.get('description', 'N/A')[:200]}...")
                    print(f"   可见性: {details.get('visibility')}")
                    print(f"   运行次数: {details.get('run_count', 'N/A')}")

                    # 获取版本信息
                    latest_version = details.get('latest_version')
                    if not latest_version:
                        print("   ⚠️ 未找到版本信息")
                        continue

                    version_id = latest_version.get('id')
                    print(f"   版本ID: {version_id[:40]}...")

                    # 提取Schema
                    schema = extract_model_schema(latest_version)

                    model_result = {
                        "owner": model_info['owner'],
                        "model": model_info['model'],
                        "description": details.get('description', ''),
                        "version_id": version_id,
                        "parameters": {},
                        "output_info": {},
                        "concurrent_support": "未知"
                    }

                    if schema:
                        print(f"\n📝 输入参数 (共{len(schema)}个):")

                        for param_name, param_config in schema.items():
                            param_type = param_config.get('type', 'unknown')
                            required = param_config.get('required', False)
                            default = param_config.get('default', 'N/A')
                            description = param_config.get('description', '')
                            enum_values = param_config.get('enum')

                            status = "必填" if required else "可选"
                            print(f"\n   • {param_name} ({status})")
                            print(f"     类型: {param_type}")
                            print(f"     默认值: {default}")
                            if enum_values:
                                print(f"     可选值: {enum_values}")
                            if description:
                                print(f"     描述: {description[:150]}...")

                            # 特别关注num_outputs或类似参数
                            if 'num' in param_name.lower() and 'output' in param_name.lower():
                                print(f"     ⭐ 关键参数: 控制输出数量!")

                            model_result["parameters"][param_name] = {
                                "type": param_type,
                                "required": required,
                                "default": default,
                                "enum": enum_values,
                                "description": description
                            }
                    else:
                        print("\n   ⚠️ 该模型没有详细的schema信息")

                    # 检查OpenAPI schema中的输出信息
                    openapi_schema = latest_version.get('openapi_schema')
                    if openapi_schema:
                        print("\n🔍 OpenAPI Schema信息:")

                        # 检查输出定义
                        output_schema = openapi_schema.get('components', {}).get('schemas', {}).get('Output')
                        if output_schema:
                            output_type = output_schema.get('type')
                            output_items = output_schema.get('items')
                            output_format = output_schema.get('format')

                            print(f"   输出类型: {output_type}")
                            if output_items:
                                print(f"   输出项类型: {output_items}")
                            if output_format:
                                print(f"   输出格式: {output_format}")

                            # 判断是否支持多张图片
                            if output_type == 'array':
                                print("   ✅ 支持数组输出 - 可能支持多张图片")
                                model_result["output_info"]["supports_multiple"] = True
                                model_result["output_info"]["output_type"] = "array"
                            else:
                                print("   ⚠️ 单一输出 - 可能只支持一张图片")
                                model_result["output_info"]["supports_multiple"] = False
                                model_result["output_info"]["output_type"] = output_type

                            model_result["output_info"]["schema"] = output_schema

                        # 检查路径定义
                        paths = openapi_schema.get('paths', {})
                        if paths:
                            print(f"\n   API路径: {list(paths.keys())}")

                    # 检查版本的其他信息
                    cog_version = latest_version.get('cog_version')
                    if cog_version:
                        print(f"\n   Cog版本: {cog_version}")

                    # 保存结果
                    all_results[f"{model_info['owner']}/{model_info['model']}"] = model_result

                except Exception as e:
                    print(f"\n❌ 测试模型 {model_info['name']} 失败: {format_error_message(e)}")
                    continue

            # 输出总结
            print("\n" + "=" * 80)
            print("📊 测试总结")
            print("=" * 80)

            for model_key, result in all_results.items():
                print(f"\n🔹 {model_key}")

                # 输出能力
                output_info = result.get("output_info", {})
                if output_info:
                    if output_info.get("supports_multiple"):
                        print("   ✅ 支持多张图片输出 (array类型)")
                    else:
                        print("   ⚠️ 单张图片输出")
                    print(f"   输出类型: {output_info.get('output_type', '未知')}")

                # 检查num_outputs参数
                params = result.get("parameters", {})
                num_output_params = [k for k in params.keys() if 'num' in k.lower() and 'output' in k.lower()]
                if num_output_params:
                    print(f"   📝 输出数量参数: {num_output_params}")
                    for param in num_output_params:
                        param_info = params[param]
                        print(f"      - {param}: 默认={param_info.get('default')}, 类型={param_info.get('type')}")
                        if param_info.get('enum'):
                            print(f"        可选值: {param_info['enum']}")
                else:
                    print("   ℹ️ 未找到明确的输出数量参数")

                # 并发支持
                print("\n   🔄 并发支持:")
                print("      Replicate API天然支持并发请求")
                print("      - 可以同时创建多个预测")
                print("      - 每个预测独立执行")
                print("      - 受限于账户的并发限制")

            # 保存详细结果到JSON
            output_file = "model_capabilities_report.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)

            print(f"\n💾 详细结果已保存到: {output_file}")

            return True

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 测试失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行测试"""
    success = asyncio.run(test_model_capabilities())

    if success:
        print("\n" + "=" * 80)
        print("🎊 测试完成!")
        print("=" * 80)
        print("\n💡 关于并发:")
        print("   Replicate API本身支持并发请求,你可以:")
        print("   1. 同时创建多个prediction请求")
        print("   2. 使用异步方式并行处理")
        print("   3. 每个预测独立排队和执行")
        print("\n⚠️ 注意:")
        print("   - 并发数量受账户配额限制")
        print("   - 某些模型可能有GPU资源限制")
        print("   - 建议查看Replicate文档了解具体限制")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()