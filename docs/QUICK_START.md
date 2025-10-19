# ComfyUI Replicate 节点快速入门指南

## 🚀 5分钟上手

### 步骤1: 安装

```bash
# 1. 进入ComfyUI的custom_nodes目录
cd /path/to/ComfyUI/custom_nodes

# 2. 复制节点文件夹
cp -r /path/to/this/folder ./comfyui-replicate-nodes

# 3. 安装依赖
cd comfyui-replicate-nodes
pip install -r requirements.txt

# 或者运行安装脚本
python install.py
```

### 步骤2: 获取API密钥

1. 访问 [Replicate](https://replicate.com)
2. 注册/登录账户
3. 进入 **Account Settings** → **API Tokens**
4. 复制你的API token

### 步骤3: 配置API密钥

**方法1: 使用节点配置**
1. 重启ComfyUI
2. 在节点菜单中找到 `Replicate` 分类
3. 添加 `Replicate Config` 节点
4. 粘贴你的API token
5. 勾选 `save_token` 和 `test_connection`
6. 执行节点

**方法2: 使用环境变量**
```bash
export REPLICATE_API_TOKEN="your_token_here"
```

**方法3: 直接编辑配置文件**
编辑 `config.json`:
```json
{
  "replicate_api_token": "your_token_here"
}
```

### 步骤4: 测试连接

```bash
python test_connection.py
```

应该看到:
```
✅ Connection successful! Found XX models
```

---

## 📖 基础工作流示例

### 示例1: 文本生成

```
┌─────────────────────┐
│ Replicate Config    │ (一次性设置)
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Model Selector      │
│ search: "llama"     │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Dynamic Node        │
│ prompt_text: "..."  │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Prediction          │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Output Processor    │
└─────────────────────┘
```

### 示例2: 图像生成

```
┌─────────────────────┐
│ Model Selector      │
│ search: "stable-    │
│         diffusion"  │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌────────────┐
│ Dynamic Node        │ ◄───│ Load Image │
│ prompt_text:        │     └────────────┘
│  "a cat"            │
│ primary_image: ─────┘
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Prediction          │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Output Processor    │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│ Preview Image       │
└─────────────────────┘
```

---

## 🎯 常用模型推荐

### 图像生成
- `stability-ai/sdxl` - Stable Diffusion XL
- `black-forest-labs/flux-schnell` - 快速图像生成
- `playground-ai/playground-v2.5` - 高质量图像

### 图像处理
- `nightmareai/real-esrgan` - 图像超分辨率
- `tencentarc/gfpgan` - 人脸修复
- `pollinations/modnet` - 背景移除

### 文本生成
- `meta/llama-2-70b-chat` - LLaMA 2对话模型
- `anthropic/claude-2` - Claude 2

### 视频生成
- `stability-ai/stable-video-diffusion` - 视频生成

---

## 💡 使用技巧

### 技巧1: 使用JSON覆盖参数

如果模型有很多参数,可以用JSON一次性设置:

```json
{
  "num_inference_steps": 50,
  "guidance_scale": 7.5,
  "negative_prompt": "blurry, bad quality",
  "width": 1024,
  "height": 1024
}
```

### 技巧2: 参数优先级

记住参数优先级(从高到低):
1. `param_overrides` (DICT)
2. `param_overrides_json` (JSON字符串)
3. 图像端口
4. `prompt_text`
5. Schema默认值

### 技巧3: 查看Schema摘要

`Dynamic Node` 的第二个输出 `schema_summary` 包含所有参数信息,连接到 `Show Text` 节点可以查看:

```json
{
  "prompt": {
    "type": "string",
    "required": false,
    "default": "",
    "is_prompt": true
  },
  "image": {
    "type": "string",
    "is_image": true
  }
}
```

### 技巧4: 处理多个图像

如果模型需要多张图像,使用多个图像端口:

```
primary_image   → image (第一个图像参数)
secondary_image → reference_image (第二个图像参数)
tertiary_image  → control_image (第三个图像参数)
```

或者使用JSON精确指定:

```json
{
  "init_image": "https://...",
  "mask_image": "https://..."
}
```

---

## ⚠️ 常见问题

### Q1: "Invalid API token" 错误?
**解决**:
- 检查token是否正确复制(没有多余空格)
- 确认token在Replicate账户中是激活的
- 重新生成token

### Q2: 模型搜索没有结果?
**解决**:
- 尝试更通用的搜索词
- 留空搜索框查看所有模型
- 勾选 `refresh` 清除缓存

### Q3: 预测超时?
**解决**:
- 增加 `timeout` 值(默认300秒)
- 某些复杂模型需要更长时间
- 检查Replicate服务状态

### Q4: 图像无法加载?
**解决**:
- 确保图像是ComfyUI的IMAGE类型
- 检查图像URL是否可访问
- 尝试使用 `Output Processor` 节点处理输出

### Q5: "No schema found" 警告?
**解决**:
- 这是正常的,某些模型不提供详细schema
- 可以手动使用JSON设置参数
- 查看模型文档了解参数

---

## 🔧 高级用法

### 自定义参数验证

```python
# 在param_overrides_json中使用
{
  "prompt": "a cat",
  "seed": 42,
  "num_outputs": 1,
  "scheduler": "K_EULER"
}
```

### 使用Webhook

在 `Prediction` 节点中设置webhook URL,预测完成时会收到通知:

```
webhook_url: https://your-server.com/webhook
```

### 批量处理

连接多个 `Prediction` 节点处理不同输入:

```
Dynamic Node 1 → Prediction 1
Dynamic Node 2 → Prediction 2
Dynamic Node 3 → Prediction 3
```

---

## 📊 性能优化

### 缓存策略
- 模型列表缓存: 1小时
- Schema缓存: 永久(类级缓存)
- API响应缓存: 1小时

### 减少API调用
1. 使用 `refresh=False` (默认)
2. 重复使用相同的 `model_info`
3. 批量处理时共享 `Dynamic Node`

### 加快预测速度
1. 选择"-turbo"或"fast"版本的模型
2. 减少 `num_inference_steps`
3. 使用较小的图像尺寸
4. 设置合理的 `poll_interval` (默认2秒)

---

## 📚 更多资源

- [Replicate文档](https://replicate.com/docs)
- [Replicate模型库](https://replicate.com/explore)
- [ComfyUI文档](https://docs.comfy.org/)
- [项目GitHub](https://github.com/your-repo)

---

## 🆘 获取帮助

1. 查看 [CODE_REVIEW.md](CODE_REVIEW.md) - 详细技术说明
2. 查看 [TEST_REPORT.md](TEST_REPORT.md) - 测试验证结果
3. 查看 [README.md](README.md) - 完整文档
4. 提交GitHub Issue
5. 查看ComfyUI社区讨论

---

## ✨ 开始使用!

现在你已经准备好了! 🎉

1. ✅ 安装完成
2. ✅ API配置完成
3. ✅ 了解基本工作流
4. ✅ 知道常见问题解决方法

**下一步**:
- 打开ComfyUI
- 添加 `Replicate Model Selector` 节点
- 搜索你喜欢的模型
- 开始创作!

祝你使用愉快! 🚀