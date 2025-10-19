#!/usr/bin/env python3
"""
并发图片生成示例
演示如何使用Replicate API并发生成多张图片
"""

import asyncio
import sys
import time
from replicate_client import ReplicateClient
from utils import load_api_token, format_error_message

async def concurrent_generation_demo():
    """并发生成图片示例"""
    print("=" * 80)
    print("Replicate 并发图片生成示例")
    print("=" * 80)

    token = load_api_token()
    if not token:
        print("❌ 未找到API token")
        return False

    # 使用hello-world模型进行快速演示(免费)
    model_owner = "replicate"
    model_name = "hello-world"
    version_id = "9dcd6d78e7c6560c340d916fe32e9f24aabfa331e5cce95fe31f77fb03121426"

    # 要生成的提示词列表
    prompts = [
        "ComfyUI 测试 1",
        "ComfyUI 测试 2",
        "ComfyUI 测试 3",
        "ComfyUI 测试 4",
        "ComfyUI 测试 5"
    ]

    print(f"\n🎯 测试模型: {model_owner}/{model_name}")
    print(f"📝 将并发生成 {len(prompts)} 个结果\n")

    try:
        async with ReplicateClient(token) as client:
            # ============================================================
            # 方法1: 串行执行 (对比用)
            # ============================================================
            print("=" * 80)
            print("📊 方法1: 串行执行 (Sequential)")
            print("=" * 80)

            sequential_start = time.time()
            sequential_results = []

            for i, prompt in enumerate(prompts, 1):
                print(f"\n[{i}/{len(prompts)}] 处理: {prompt}")

                # 创建预测
                pred = await client.create_prediction(
                    version_id=version_id,
                    inputs={"text": prompt}
                )
                print(f"   ✅ 预测已创建: {pred.id}")

                # 等待完成
                result = await client.wait_for_prediction(pred.id, timeout=60)
                print(f"   ✅ 完成: {result.output}")

                sequential_results.append(result)

            sequential_time = time.time() - sequential_start
            print(f"\n⏱️ 串行执行总耗时: {sequential_time:.2f}秒")
            print(f"📊 平均每个: {sequential_time/len(prompts):.2f}秒")

            # ============================================================
            # 方法2: 并发执行 (推荐)
            # ============================================================
            print("\n" + "=" * 80)
            print("📊 方法2: 并发执行 (Concurrent)")
            print("=" * 80)

            concurrent_start = time.time()

            # 步骤1: 并发创建所有预测
            print(f"\n🚀 步骤1: 并发创建 {len(prompts)} 个预测...")

            create_tasks = [
                client.create_prediction(
                    version_id=version_id,
                    inputs={"text": prompt}
                )
                for prompt in prompts
            ]

            predictions = await asyncio.gather(*create_tasks)
            print(f"   ✅ {len(predictions)} 个预测已创建")

            for i, pred in enumerate(predictions, 1):
                print(f"   [{i}] {pred.id} - 状态: {pred.status}")

            # 步骤2: 并发等待所有完成
            print(f"\n⏳ 步骤2: 并发等待所有预测完成...")

            wait_tasks = [
                client.wait_for_prediction(pred.id, timeout=60)
                for pred in predictions
            ]

            concurrent_results = await asyncio.gather(*wait_tasks)
            print(f"   ✅ {len(concurrent_results)} 个预测已完成")

            concurrent_time = time.time() - concurrent_start
            print(f"\n⏱️ 并发执行总耗时: {concurrent_time:.2f}秒")
            print(f"📊 平均每个: {concurrent_time/len(prompts):.2f}秒")

            # ============================================================
            # 性能对比
            # ============================================================
            print("\n" + "=" * 80)
            print("📊 性能对比")
            print("=" * 80)

            speedup = sequential_time / concurrent_time
            time_saved = sequential_time - concurrent_time

            print(f"\n串行执行: {sequential_time:.2f}秒")
            print(f"并发执行: {concurrent_time:.2f}秒")
            print(f"\n⚡ 加速比: {speedup:.2f}x")
            print(f"💾 节省时间: {time_saved:.2f}秒 ({time_saved/sequential_time*100:.1f}%)")

            # ============================================================
            # 输出结果
            # ============================================================
            print("\n" + "=" * 80)
            print("📋 输出结果")
            print("=" * 80)

            print("\n并发执行结果:")
            for i, (prompt, result) in enumerate(zip(prompts, concurrent_results), 1):
                print(f"   [{i}] {prompt}")
                print(f"       输入: {result.input}")
                print(f"       输出: {result.output}")
                print(f"       状态: {result.status}")
                print()

            # ============================================================
            # 方法3: 分批并发 (推荐用于大量任务)
            # ============================================================
            print("\n" + "=" * 80)
            print("📊 方法3: 分批并发 (Batch Concurrent) - 推荐!")
            print("=" * 80)

            # 大量提示词
            large_prompts = [f"测试 {i}" for i in range(1, 21)]  # 20个
            batch_size = 5  # 每批5个

            print(f"\n处理 {len(large_prompts)} 个任务,每批 {batch_size} 个")

            batch_start = time.time()
            batch_results = []

            for i in range(0, len(large_prompts), batch_size):
                batch = large_prompts[i:i+batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(large_prompts) + batch_size - 1) // batch_size

                print(f"\n🔄 批次 {batch_num}/{total_batches} (共{len(batch)}个任务)")

                # 创建当前批次的预测
                create_tasks = [
                    client.create_prediction(version_id, {"text": prompt})
                    for prompt in batch
                ]
                predictions = await asyncio.gather(*create_tasks)

                # 等待当前批次完成
                wait_tasks = [
                    client.wait_for_prediction(pred.id, timeout=60)
                    for pred in predictions
                ]
                results = await asyncio.gather(*wait_tasks)

                batch_results.extend(results)
                print(f"   ✅ 批次 {batch_num} 完成")

                # 批次间短暂延迟(避免触发限流)
                if i + batch_size < len(large_prompts):
                    await asyncio.sleep(0.5)

            batch_time = time.time() - batch_start
            print(f"\n⏱️ 分批并发总耗时: {batch_time:.2f}秒")
            print(f"📊 平均每个: {batch_time/len(large_prompts):.2f}秒")
            print(f"✅ 成功: {sum(1 for r in batch_results if r.status == 'succeeded')}/{len(batch_results)}")

            return True

    except Exception as e:
        error_msg = format_error_message(e)
        print(f"\n❌ 测试失败: {error_msg}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行示例"""
    print("\n💡 本示例将演示三种执行方式:")
    print("   1. 串行执行 - 一个接一个")
    print("   2. 并发执行 - 同时处理所有")
    print("   3. 分批并发 - 推荐的实际使用方式")
    print("\n⚠️ 注意: 使用hello-world模型进行演示(免费)\n")

    success = asyncio.run(concurrent_generation_demo())

    if success:
        print("\n" + "=" * 80)
        print("🎊 并发示例完成!")
        print("=" * 80)
        print("\n💡 关键要点:")
        print("   1. 并发执行可以大幅提升性能(通常2-5倍)")
        print("   2. 使用asyncio.gather()实现并发")
        print("   3. 对于大量任务,使用分批处理避免过载")
        print("   4. 添加适当的延迟避免触发限流")
        print("\n🚀 可以将此模式应用到实际的图像生成任务!")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()