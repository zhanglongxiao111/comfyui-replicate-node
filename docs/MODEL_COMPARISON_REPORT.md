# Replicate 模型能力对比报告

## 测试日期
2025-10-19

## 测试模型
1. **Qwen Image Edit** - `espressotechie/qwen-imgedit-4bit`
2. **Nano Banana (Gemini 2.5 Flash Image)** - `google/nano-banana`

---

## 📊 核心问题回答

### Q1: 这两个模型支持最多几张图片的输出?

#### Qwen Image Edit (`espressotechie/qwen-imgedit-4bit`)
- ✅ **支持多张图片输出**
- 输出类型: `array` (数组)
- 输出格式: URI数组 (图片URL列表)
- Schema定义:
  ```json
  {
    "type": "array",
    "items": {
      "type": "string",
      "format": "uri"
    }
  }
  ```
- **结论**: 虽然没有明确的`num_outputs`参数,但输出类型是数组,**理论上支持输出多张图片**

#### Nano Banana (`google/nano-banana`)
- ⚠️ **仅支持单张图片输出**
- 输出类型: `string` (单个字符串)
- 输出格式: URI (单个图片URL)
- Schema定义:
  ```json
  {
    "type": "string",
    "format": "uri"
  }
  ```
- **结论**: 每次调用**只输出一张图片**

---

### Q2: 如果只能输出一张,是否支持并发?

#### 简短回答: ✅ **是的,两个模型都完全支持并发!**

#### 详细说明:

**Replicate API的并发支持**:
- ✅ Replicate API天然支持并发请求
- ✅ 可以同时创建多个prediction请求
- ✅ 每个prediction独立执行和排队
- ✅ 支持异步处理,不会互相阻塞

**如何实现并发**:

1. **方法1: 异步并发创建多个预测**
   ```python
   async def generate_multiple_images(prompts):
       async with ReplicateClient(token) as client:
           # 同时创建多个预测
           tasks = []
           for prompt in prompts:
               task = client.create_prediction(
                   version_id=version_id,
                   inputs={"prompt": prompt}
               )
               tasks.append(task)

           # 并发执行
           predictions = await asyncio.gather(*tasks)

           # 等待所有完成
           results = []
           for pred in predictions:
               result = await client.wait_for_prediction(pred.id)
               results.append(result)

           return results
   ```

2. **方法2: 在ComfyUI中使用多个Prediction节点**
   ```
   Dynamic Node 1 → Prediction 1 (独立执行)
   Dynamic Node 2 → Prediction 2 (独立执行)
   Dynamic Node 3 → Prediction 3 (独立执行)
   ```

3. **方法3: 批量处理**
   ```python
   # 创建10个并发请求
   for i in range(10):
       prediction = await client.create_prediction(...)
       # 不等待,继续创建下一个

   # 稍后一起检查所有结果
   ```

---

## 🔍 详细模型分析

### 1. Qwen Image Edit (`espressotechie/qwen-imgedit-4bit`)

#### 基本信息
- **作者**: espressotechie
- **描述**: Qwen图像编辑快速版
- **运行次数**: 274次
- **Cog版本**: 0.16.8

#### 输入参数 (7个)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `seed` | integer | ❌ | 无 | 随机种子(可重现性) |
| `image` | string | ❌ | 无 | 输入图像 |
| `steps` | unknown | ❌ | 2 | 采样步数(2=快速,4=高质量) |
| `prompt` | string | ❌ | "" | 提示词 |
| `output_format` | unknown | ❌ | "webp" | 输出图像格式 |
| `output_quality` | integer | ❌ | 95 | 输出质量(0-100) |
| `negative_prompt` | string | ❌ | "" | 负面提示词 |

#### 输出能力
- ✅ **数组输出**: 支持返回多个图像URL
- 输出格式: `["url1", "url2", "url3", ...]`
- **实际输出数量**: 取决于模型内部逻辑(未在参数中明确指定)

#### 使用场景
- 图像编辑
- 快速生成变体
- 可能支持批量处理

---

### 2. Nano Banana (`google/nano-banana`)

#### 基本信息
- **作者**: Google
- **完整名称**: Gemini 2.5 Flash Image
- **描述**: Google最新的图像编辑模型
- **运行次数**: 20,596,753次 (非常流行!)
- **Cog版本**: 0.16.8
- **定价**: $0.039/张图片

#### 输入参数 (4个)

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `prompt` | string | ❌ | 无 | 图像生成/编辑描述 |
| `image_input` | **array** | ❌ | `[]` | **输入图像数组(支持多张)** |
| `aspect_ratio` | unknown | ❌ | "match_input_image" | 长宽比 |
| `output_format` | unknown | ❌ | "jpg" | 输出格式 |

#### 特别说明
- ⭐ **输入支持多张图片** (`image_input`是数组类型)
- ⚠️ **输出只有一张图片** (输出类型是单个URI)
- **多图融合**: 可以输入多张参考图,输出融合后的单张图

#### 输出能力
- ⚠️ **单一输出**: 每次只返回一个图像URL
- 输出格式: `"https://...jpg"`
- **要生成多张**: 需要调用多次或使用并发

#### 核心功能
1. **多图融合**: 输入多张图片,融合成一张新图
2. **精确编辑**: 使用自然语言进行精确编辑
3. **风格一致性**: 多次调用保持角色/风格一致
4. **高质量输出**: Google最新的图像生成技术

#### 使用场景
- 图像编辑和生成
- 多图融合创作
- 虚拟试穿
- 家居改造可视化
- 角色一致性创作

---

## 💡 并发实现建议

### 对于Qwen Image Edit

如果需要**多张不同的图片**:

**选项A: 利用数组输出** (如果模型支持)
```python
# 单次调用,可能返回多张
result = await client.create_prediction(
    version_id=version_id,
    inputs={
        "prompt": "a cat",
        # 可能没有num_outputs参数
    }
)
# result.output 可能是 ["url1", "url2", ...]
```

**选项B: 并发调用多次**
```python
# 同时生成3张不同的图
tasks = [
    client.create_prediction(version_id, {"prompt": "cat 1"}),
    client.create_prediction(version_id, {"prompt": "cat 2"}),
    client.create_prediction(version_id, {"prompt": "cat 3"}),
]
predictions = await asyncio.gather(*tasks)
```

---

### 对于Nano Banana

**必须使用并发** (因为单次只输出一张):

```python
async def generate_batch_nano_banana(prompts):
    """并发生成多张图片"""
    async with ReplicateClient(token) as client:
        # 1. 并发创建所有预测
        create_tasks = [
            client.create_prediction(
                version_id=nano_banana_version_id,
                inputs={"prompt": prompt}
            )
            for prompt in prompts
        ]

        predictions = await asyncio.gather(*create_tasks)
        print(f"✅ 创建了 {len(predictions)} 个预测")

        # 2. 并发等待所有完成
        wait_tasks = [
            client.wait_for_prediction(pred.id, timeout=300)
            for pred in predictions
        ]

        results = await asyncio.gather(*wait_tasks)
        print(f"✅ {len(results)} 个预测已完成")

        # 3. 提取所有图像URL
        image_urls = [r.output for r in results if r.status == 'succeeded']

        return image_urls

# 使用示例
prompts = [
    "a red cat",
    "a blue cat",
    "a green cat",
    "a yellow cat",
    "a purple cat"
]

urls = await generate_batch_nano_banana(prompts)
print(f"生成了 {len(urls)} 张图片: {urls}")
```

---

## ⚡ 性能对比

### 并发性能估算

假设你需要生成**10张图片**:

#### Qwen Image Edit
- **如果支持数组输出**:
  - 1次API调用
  - 等待时间: ~1次模型执行时间
  - **推荐**: 先尝试单次调用

- **如果使用并发**:
  - 10次API调用(并发)
  - 等待时间: ~1次模型执行时间(GPU并行)
  - API成本: 10倍

#### Nano Banana
- **必须并发**:
  - 10次API调用(并发)
  - 等待时间: ~1次模型执行时间(GPU并行)
  - API成本: 10 × $0.039 = **$0.39**

### 并发限制

**Replicate账户限制**:
- 免费账户: 通常有并发限制
- 付费账户: 更高的并发限制
- 具体限制: 查看Replicate文档或联系支持

**建议**:
- 从小批量开始测试(如5个并发)
- 监控API响应和错误
- 根据需求逐步增加并发数
- 使用重试机制处理失败

---

## 🎯 最佳实践

### 1. 选择合适的模型

**选择Qwen Image Edit,如果**:
- 需要快速的图像编辑
- 可能需要多张输出
- 对成本敏感

**选择Nano Banana,如果**:
- 需要Google最新技术
- 需要多图融合功能
- 需要高质量输出
- 需要角色一致性

### 2. 并发策略

```python
# 智能批处理
async def smart_batch_processing(items, batch_size=5):
    """分批处理,避免过载"""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        # 处理当前批次
        batch_results = await process_batch(batch)
        results.extend(batch_results)

        # 短暂延迟,避免触发限流
        if i + batch_size < len(items):
            await asyncio.sleep(1)

    return results
```

### 3. 错误处理

```python
async def robust_prediction(client, version_id, inputs, max_retries=3):
    """带重试的预测"""
    for attempt in range(max_retries):
        try:
            pred = await client.create_prediction(version_id, inputs)
            result = await client.wait_for_prediction(pred.id)

            if result.status == 'succeeded':
                return result
            else:
                print(f"预测失败: {result.error}")

        except Exception as e:
            print(f"尝试 {attempt+1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避

    raise Exception("所有重试都失败")
```

---

## 📝 总结

### Qwen Image Edit
- ✅ 输出类型: **数组** (支持多张)
- ✅ 并发: **完全支持**
- 💡 建议: 先测试是否单次调用就能返回多张

### Nano Banana
- ⚠️ 输出类型: **单张**
- ✅ 输入类型: **支持多张** (融合)
- ✅ 并发: **完全支持,必须使用**
- 💡 建议: 使用异步并发生成多张图片

### 并发能力
**两个模型都100%支持并发!** Replicate API设计就是为并发优化的:
- ✅ 可以同时创建多个预测
- ✅ 每个预测独立排队
- ✅ GPU资源自动调度
- ✅ 支持异步等待

---

## 🔗 相关资源

- [Qwen Image Edit on Replicate](https://replicate.com/espressotechie/qwen-imgedit-4bit)
- [Nano Banana on Replicate](https://replicate.com/google/nano-banana)
- [Replicate API文档](https://replicate.com/docs)
- [并发限制说明](https://replicate.com/docs/topics/predictions/create-a-prediction)

---

**测试完成时间**: 2025-10-19
**测试工具**: ComfyUI Replicate节点测试套件
**API Token**: 已验证并正常工作