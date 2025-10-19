#!/usr/bin/env python3
"""
测试预设模型功能
"""

import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入模块内容
import importlib.util

def load_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 加载模块
nodes_module = load_module_from_file('nodes', os.path.join(current_dir, 'nodes.py'))
ReplicateModelSelector = nodes_module.ReplicateModelSelector

def test_preset_models():
    """测试预设模型选择功能"""
    print("=" * 80)
    print("测试预设模型功能")
    print("=" * 80)

    # API token (已配置)
    api_token = ""  # 使用保存的token

    # 创建节点实例
    selector = ReplicateModelSelector()

    # 测试列表
    test_cases = [
        {
            "name": "Nano Banana (预设)",
            "model_preset": "google/nano-banana",
            "search_query": "",
            "should_succeed": True
        },
        {
            "name": "Qwen Image Edit (预设)",
            "model_preset": "qwen/qwen-image-edit",
            "search_query": "",
            "should_succeed": True
        },
        {
            "name": "Custom Search (hello-world)",
            "model_preset": "Custom (use search)",
            "search_query": "hello-world",
            "should_succeed": True
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 80}")

        try:
            # 调用select_model
            model_id, model_name, model_version, model_info = selector.select_model(
                model_preset=test_case['model_preset'],
                search_query=test_case['search_query'],
                api_token=api_token,
                refresh=False,
                limit=50
            )

            print(f"\n✅ 成功!")
            print(f"   模型ID: {model_id}")
            print(f"   模型名称: {model_name}")
            print(f"   版本ID: {model_version[:40]}..." if model_version else "   版本ID: N/A")
            print(f"   描述: {model_info.get('description', 'N/A')[:100]}...")

            # 检查schema
            schema = model_info.get('schema', {})
            if schema:
                print(f"   参数数量: {len(schema)}")
                print(f"   参数: {', '.join(list(schema.keys())[:5])}...")
            else:
                print(f"   ⚠️ 未找到schema")

            results.append({
                "test": test_case['name'],
                "success": True,
                "model": f"{model_id}",
                "params": len(schema)
            })

        except Exception as e:
            print(f"\n❌ 失败: {e}")
            results.append({
                "test": test_case['name'],
                "success": False,
                "error": str(e)
            })

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ 通过: {success_count}/{len(results)}")

    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        print(f"\n{i}. {status} {result['test']}")
        if result['success']:
            print(f"   模型: {result['model']}")
            print(f"   参数: {result.get('params', 0)}个")
        else:
            print(f"   错误: {result.get('error', 'Unknown')}")

    print("\n" + "=" * 80)
    print("预设模型列表:")
    print("=" * 80)
    for model in ReplicateModelSelector.PRESET_MODELS:
        print(f"  • {model}")

    return success_count == len(results)

if __name__ == "__main__":
    success = test_preset_models()
    sys.exit(0 if success else 1)