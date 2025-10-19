# ComfyUI Replicate 节点集

将 Replicate 上的远程模型平滑接入 ComfyUI。本仓库提供三个高频模型的专用节点，以及一个 API 密钥共享节点，直接输出 ComfyUI 可识别的图像张量与文本结果，便于在工作流中继续处理或展示。

## ✨ 功能亮点

- **专用节点**：内置 `qwen/qwen-image-edit-plus`、`bytedance/seedream-4`、`google/nano-banana` 三个模型的定制节点，中文界面，参数易懂。
- **端口/面板双输入**：提示词、生成数量、API 密钥均可通过节点面板或上游端口传入，方便自动化流程。
- **多图处理**：自动识别模型是否支持批量生成。若不支持，则并发调用补足，最多输出 5 张图像。
- **输出即用**：返回的图像直接是 ComfyUI 期待的 `IMAGE` 张量，可接驳预览、保存或后处理节点。
- **API 密钥共享**：通过独立节点统一保管或分发 Replicate API key，减少重复输入。

## 📦 安装方式

### 方式一：使用插件管理器（推荐）

在 ComfyUI 内置的插件管理器中搜索 `comfyui-replicate-node` 并安装，随后点击“更新/刷新”即可。

### 方式二：手动克隆

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/zhanglongxiao111/comfyui-replicate-node.git
cd comfyui-replicate-node
python install.py  # 可选：校验依赖与配置
```

若只想手动安装依赖，可执行：

```bash
pip install -r requirements.txt
```

## 🔑 配置 Replicate API Token

1. 访问 [Replicate 账号页面](https://replicate.com/account/api-tokens) 获取 `r8_xxx` 形式的 token。
2. 在 ComfyUI 中有两种方式：  
   - **使用节点**：拖入 `Replicate API 密钥` 节点，输入 token，勾选“保存到配置”后，可供其他节点复用。  
   - **环境变量 / 配置文件**：在系统中设置 `REPLICATE_API_TOKEN`，或编辑仓库根目录的 `config.json`：
     ```json
     {
       "replicate_api_token": "r8_your_token_here"
     }
     ```

## 🧩 节点总览

| 节点名称 | 说明 | 关键输入 | 输出 |
| --- | --- | --- | --- |
| **Replicate API 密钥** | 读取/保存 API token，输出给其他节点使用 | API密钥、保存到配置、允许配置回退 | API密钥、状态 |
| **qwen/qwen-image-edit-plus** | 基于中文指令编辑输入图片，支持多图生成 | API密钥、提示词、输入图片、生成数量、输出参数 | 生成图像、文本输出、原始结果 |
| **bytedance/seedream-4** | 文生图/图生图混合模型，可原生批量生成 | API密钥、提示词、生成数量、参考图等 | 生成图像、文本输出、原始结果 |
| **google/nano-banana** | 轻量级多模态生成模型，支持参考图 | API密钥、提示词、生成数量、参考图等 | 生成图像、文本输出、原始结果 |

所有节点的面板与端口文案均为中文，常用参数带有 tooltip 提示，方便快速上手。

## 🚀 快速上手示例

1. 在画布中放置 `Replicate API 密钥` 节点，填写 token 并连接到下游节点的密钥端口。
2. 拖入例如 `qwen/qwen-image-edit-plus` 节点：  
   - 连接提示词、输入图片、生成数量等端口；  
   - 节点会根据模型能力自动决定批量或并发生成，最多输出 5 张图。
3. 将节点输出接到 `Preview Image` 或 `Save Image` 等默认节点即可查看结果。
4. 若需要生成多张不同画面，可通过 `数量输入` 端口动态传值，配合工作流控制。

## 🧪 开发与测试

- 验证 Replicate API 可用：`python tests/test_prediction.py`（需要有效 token）。
- 额外示例工作流位于 `examples/`，可作为画布模板。

## 🤝 贡献

欢迎提交 Issue 与 Pull Request。若有更多模型需求或功能建议，直接在仓库讨论区反馈即可。

## 📄 许可证

本项目采用 MIT License，详情见仓库根目录的 `LICENSE`（如需自定义许可，可按需调整）。

---
如果该插件对你有帮助，欢迎在 GitHub 上点个 ⭐ 支持作者！
