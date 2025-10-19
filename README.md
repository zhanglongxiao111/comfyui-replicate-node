# ComfyUI Replicate Nodes

将 Replicate API 的强大 AI 模型集成到 ComfyUI 中,支持图像生成、图像编辑、文本生成等多种功能。

## ✨ 特性

- 🔍 **模型搜索**: 直接在 ComfyUI 中浏览和搜索 Replicate 模型
- 🎯 **预设模型**: 内置推荐模型,开箱即用
- 🔄 **动态参数**: 根据模型 Schema 自动生成输入参数
- 🖼️ **智能图像处理**: 支持最多 4 个图像输入,自动格式转换
- 📝 **文本提示**: 智能识别并处理提示词参数
- ⚡ **异步执行**: 非阻塞预测执行,实时状态监控
- 🎨 **输出处理**: 自动下载并转换为 ComfyUI 格式

## 📦 快速安装

### 方法 1: 自动安装 (推荐)

```bash
# 进入 ComfyUI 的 custom_nodes 目录
cd /path/to/ComfyUI/custom_nodes

# 克隆或下载本插件
git clone https://github.com/your-username/comfyui-replicate-nodes.git

# 进入插件目录
cd comfyui-replicate-nodes

# 运行安装脚本
python install.py
```

### 方法 2: 手动安装

```bash
cd /path/to/ComfyUI/custom_nodes/comfyui-replicate-nodes
pip install -r requirements.txt
```

详细安装说明请查看 [INSTALLATION.md](INSTALLATION.md)

## ⚙️ 配置

### 获取 API Token

1. 注册 [Replicate](https://replicate.com) 账号
2. 获取你的 [API Token](https://replicate.com/account/api-tokens)

### 配置 Token (三选一)

**方法 1: 使用节点** (最简单)
- 在 ComfyUI 中添加 `Replicate Config` 节点
- 输入 Token,勾选 `save_token` 和 `test_connection`

**方法 2: 环境变量**
```bash
export REPLICATE_API_TOKEN=r8_your_token_here
```

**方法 3: 配置文件**
编辑 `config.json`:
```json
{
  "replicate_api_token": "r8_your_token_here"
}
```

## 🚀 使用方法

### 基础工作流

```
1. Replicate Model Selector
   ├─ model_preset: "google/nano-banana" (或搜索其他模型)
   └─ 输出: model_info, model_version

2. Replicate Dynamic Node
   ├─ 连接: model_info, model_version
   ├─ prompt_text: "你的提示词"
   ├─ primary_image: (可选) 连接图像
   └─ 输出: prepared_inputs, schema_summary

3. Replicate Prediction
   ├─ 连接: prepared_inputs, model_version
   └─ 输出: prediction_id, status, results

4. Replicate Output Processor
   ├─ 连接: results
   └─ 输出: image, text, raw_output
```

### 预设模型

插件内置了以下推荐模型:

- **google/nano-banana** - Gemini 2.5 Flash (视觉理解)
- **qwen/qwen-image-edit** - Qwen 图像编辑
- **stability-ai/sdxl** - Stable Diffusion XL
- **black-forest-labs/flux-schnell** - FLUX 快速生成

也可以选择 `Custom (use search)` 搜索其他模型。

## 📖 文档

- 📘 [INSTALLATION.md](INSTALLATION.md) - 详细安装指南
- 📗 [docs/QUICK_START.md](docs/QUICK_START.md) - 快速入门教程
- 📙 [docs/PRESET_MODELS_GUIDE.md](docs/PRESET_MODELS_GUIDE.md) - 预设模型指南
- 📕 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - 项目结构说明

## 🔧 节点说明

| 节点 | 功能 | 主要输入 | 主要输出 |
|------|------|----------|----------|
| **Replicate Config** | 配置 API Token | api_token | status, success |
| **Replicate Model Selector** | 选择模型 | model_preset, search_query | model_info, model_version |
| **Replicate Dynamic Node** | 准备输入参数 | model_info, prompt_text, images | prepared_inputs, schema_summary |
| **Replicate Prediction** | 执行预测 | prepared_inputs, model_version | prediction_id, results |
| **Replicate Output Processor** | 处理输出 | results | image, text, raw_output |

## 📁 项目结构

```
comfyui-replicate-nodes/
├── __init__.py              # 插件入口
├── requirements.txt         # 依赖列表
├── config.json              # 配置文件
├── install.py               # 安装脚本
├── core/                    # 核心代码
│   ├── nodes.py            # 节点实现
│   ├── replicate_client.py # API 客户端
│   └── utils.py            # 工具函数
├── tests/                   # 测试脚本
├── docs/                    # 文档
└── examples/                # 示例
```

详见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🐛 故障排查

### 常见问题

**导入错误**: 检查 `core/` 目录是否完整,重新运行 `python install.py`

**找不到节点**: 检查 ComfyUI 控制台错误,确认依赖已安装

**Token 无效**: 检查 Token 格式,重新从 Replicate 获取

**网络错误**: 检查网络连接,增加 timeout 值

更多详情请查看 [INSTALLATION.md](INSTALLATION.md) 的故障排查部分。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [Replicate](https://replicate.com)

---

⭐ 如果这个项目对你有帮助,请给个 Star!
