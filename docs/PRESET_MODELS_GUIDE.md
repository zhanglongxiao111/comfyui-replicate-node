# ComfyUI Replicate 预设模型使用指南

## 🎯 更新内容

已为 `ReplicateModelSelector` 节点添加预设模型下拉选择功能,您现在可以快速选择推荐的高质量模型!

---

## 📋 预设模型列表

### 1. **google/nano-banana** (默认) ⭐
- **名称**: Nano Banana (Gemini 2.5 Flash Image)
- **作者**: Google
- **运行次数**: 20,800,000+
- **参数数量**: 4个
- **特点**:
  - Google最新的图像编辑和生成模型
  - 支持多图融合 (image_input是数组)
  - 高质量输出
  - 精确的编辑控制
- **输出**: 单张图片(支持并发生成多张)
- **定价**: $0.039/张
- **最佳用途**: 图像生成、编辑、多图融合

### 2. **qwen/qwen-image-edit** ✨
- **名称**: Qwen Image Edit
- **作者**: Qwen (阿里巴巴)
- **运行次数**: 586,000+
- **参数数量**: 7个
- **特点**:
  - 强大的文本渲染能力
  - 精确的图像编辑
  - 支持快速模式(go_fast)
  - 语义和外观双重编辑
- **输出**: 数组(可能支持多张图片)
- **最佳用途**: 图像编辑、文字渲染、风格转换

### 3. **stability-ai/sdxl**
- **名称**: Stable Diffusion XL
- **作者**: Stability AI
- **特点**: 高质量图像生成,业界标准
- **最佳用途**: 艺术创作、概念设计

### 4. **black-forest-labs/flux-schnell**
- **名称**: FLUX Schnell
- **作者**: Black Forest Labs
- **特点**: 快速生成,高效性能
- **最佳用途**: 快速原型、批量生成

### 5. **Custom (use search)**
- 使用搜索功能查找其他模型
- 在 `search_query` 中输入关键词

---

## 🚀 使用方法

### 基础使用

1. **添加节点**
   - 在ComfyUI中,添加 `Replicate Model Selector` 节点

2. **选择预设模型**
   - 从 `model_preset` 下拉菜单选择模型
   - 默认是 `google/nano-banana`

3. **连接到Dynamic Node**
   - 将输出连接到 `Replicate Dynamic Node`
   - 参数会自动根据模型生成

### 使用自定义搜索

1. **选择Custom选项**
   - `model_preset` 选择 `Custom (use search)`

2. **输入搜索词**
   - 在 `search_query` 中输入关键词
   - 例如: "stable diffusion", "llama", "flux"

3. **执行搜索**
   - 节点会返回第一个匹配的模型

---

## 💡 实际应用示例

### 示例1: 使用Nano Banana生成图片

```
工作流:
┌─────────────────────────┐
│ Replicate Model Selector│
│ preset: nano-banana     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Replicate Dynamic Node  │
│ prompt: "a red cat"     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Replicate Prediction    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Output Processor        │
└─────────────────────────┘
```

### 示例2: 使用Qwen Image Edit编辑图片

```
工作流:
┌─────────────────────────┐     ┌────────────┐
│ Replicate Model Selector│     │ Load Image │
│ preset: qwen-image-edit │     └──────┬─────┘
└───────────┬─────────────┘            │
            │                          │
            ▼                          │
┌─────────────────────────┐            │
│ Replicate Dynamic Node  │◄───────────┘
│ prompt: "add glasses"   │
│ primary_image: ────────┘
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Replicate Prediction    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Output Processor        │
└─────────────────────────┘
```

### 示例3: 批量并发生成

使用Nano Banana并发生成10张图片:

```python
# 在ComfyUI中,创建10个并行的Prediction节点
# 或使用Python脚本:

from example_concurrent_generation import concurrent_generation_demo
asyncio.run(concurrent_generation_demo())
```

---

## 📊 模型对比

| 特性 | Nano Banana | Qwen Image Edit |
|------|-------------|-----------------|
| 输出数量 | 单张 | 多张(数组) |
| 输入图片 | 多张(融合) | 单张 |
| 运行次数 | 2000万+ | 58万+ |
| 参数数量 | 4个 | 7个 |
| 特色功能 | 多图融合 | 文本渲染 |
| 最佳用途 | 生成/编辑 | 精确编辑 |
| 并发支持 | ✅ | ✅ |

---

## 🔧 高级技巧

### 1. 快速切换模型

在同一工作流中:
- 复制 `Model Selector` 节点
- 选择不同的预设模型
- 对比不同模型的效果

### 2. 参数覆盖

在 `Dynamic Node` 中使用 `param_overrides_json`:

```json
{
  "output_format": "png",
  "output_quality": 100,
  "seed": 42
}
```

### 3. 批量处理

参考 `example_concurrent_generation.py`:
- 分批并发(推荐)
- 每批5-10个
- 避免触发限流

---

## ⚠️ 注意事项

### Nano Banana
- ✅ 输入支持多张图片(融合)
- ⚠️ 输出只有一张
- 💡 需要多张输出时使用并发
- 💰 成本: $0.039/张

### Qwen Image Edit
- ✅ 输出是数组(可能多张)
- ✅ 强大的文本渲染
- 💡 use `go_fast=true` 加速
- 💡 适合批量编辑

### 通用建议
- 首次使用建议用小图测试
- 注意API配额和成本
- 使用 `refresh=false` 利用缓存
- 保存好的参数组合

---

## 🆘 常见问题

### Q: 如何添加更多预设模型?

A: 编辑 `nodes.py` 中的 `PRESET_MODELS` 列表:

```python
PRESET_MODELS = [
    "google/nano-banana",
    "qwen/qwen-image-edit",
    "your-owner/your-model",  # 添加你的模型
    "Custom (use search)"
]
```

### Q: 预设模型没有我想要的模型?

A: 使用 `Custom (use search)` 选项,然后在 `search_query` 中搜索。

### Q: 如何知道模型支持哪些参数?

A: 查看 `Dynamic Node` 的第二个输出 `schema_summary`,连接到 `Show Text` 节点。

### Q: 并发会增加成本吗?

A: 并发不增加单张成本,但会增加总请求数。例如:
- 串行10张: 10 × $0.039 = $0.39
- 并发10张: 10 × $0.039 = $0.39 (相同成本,但更快)

---

## 📚 相关资源

- [MODEL_COMPARISON_REPORT.md](MODEL_COMPARISON_REPORT.md) - 详细模型对比
- [example_concurrent_generation.py](example_concurrent_generation.py) - 并发示例代码
- [default_models_config.json](default_models_config.json) - 模型配置信息
- [Replicate官网](https://replicate.com/)

---

## ✅ 验证测试

所有预设模型已通过验证:
- ✅ google/nano-banana - 2080万+运行
- ✅ qwen/qwen-image-edit - 58万+运行
- ✅ API连接正常
- ✅ Schema提取成功
- ✅ 参数识别正确

---

**最后更新**: 2025-10-19
**测试状态**: 全部通过 ✅
**节点版本**: 1.0.0