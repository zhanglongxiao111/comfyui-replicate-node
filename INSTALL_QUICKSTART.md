# 🚀 ComfyUI Replicate Nodes - 快速安装

> 3 分钟完成安装,立即开始使用!

## 第一步: 安装插件 (选择一种方法)

### 方法 A: Git Clone (推荐)
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/your-username/comfyui-replicate-nodes.git
cd comfyui-replicate-nodes
python install.py
```

### 方法 B: 手动下载
1. 下载插件压缩包
2. 解压到 `ComfyUI/custom_nodes/`
3. 进入目录运行 `python install.py`

---

## 第二步: 获取 API Token

1. 打开 https://replicate.com
2. 注册/登录账号
3. 访问 https://replicate.com/account/api-tokens
4. 复制你的 Token (格式: `r8_xxxxx...`)

---

## 第三步: 配置 Token (选择一种方法)

### 方法 A: 在 ComfyUI 中配置 (推荐新手)
1. 启动 ComfyUI
2. 添加 `Replicate Config` 节点
3. 粘贴 Token
4. 勾选 `save_token` 和 `test_connection`
5. 点击执行

### 方法 B: 环境变量 (推荐高级用户)

**Windows (CMD):**
```cmd
setx REPLICATE_API_TOKEN "r8_your_token_here"
```

**Windows (PowerShell):**
```powershell
[System.Environment]::SetEnvironmentVariable('REPLICATE_API_TOKEN', 'r8_your_token_here', 'User')
```

**Linux/Mac:**
```bash
echo 'export REPLICATE_API_TOKEN=r8_your_token_here' >> ~/.bashrc
source ~/.bashrc
```

---

## 第四步: 重启 ComfyUI

```bash
# 如果 ComfyUI 正在运行,重启它
# Windows: 关闭命令行窗口并重新启动
# Linux/Mac: Ctrl+C 然后重新运行
python main.py
```

---

## 第五步: 验证安装

### 检查节点是否加载

在 ComfyUI 界面中,右键 → Add Node → Replicate

你应该看到 5 个节点:
- ✅ Replicate Config
- ✅ Replicate Model Selector
- ✅ Replicate Dynamic Node
- ✅ Replicate Prediction
- ✅ Replicate Output Processor

### 快速测试工作流

1. 添加 `Replicate Model Selector` 节点
   - model_preset: `google/nano-banana`
   - 执行节点

2. 添加 `Replicate Dynamic Node` 节点
   - 连接 model_info 和 model_version
   - prompt_text: `"Describe this image: A beautiful sunset"`
   - 执行节点

3. 添加 `Replicate Prediction` 节点
   - 连接 prepared_inputs 和 model_version
   - 执行节点

4. 添加 `Replicate Output Processor` 节点
   - 连接 results
   - 查看输出

如果所有节点都成功执行,恭喜你,安装完成! 🎉

---

## 🆘 遇到问题?

### 问题 1: 找不到节点
- **解决**: 检查 ComfyUI 控制台是否有错误信息
- **原因**: 可能是依赖未安装或文件缺失
- **操作**: 重新运行 `python install.py`

### 问题 2: Import Error
```
ImportError: cannot import name 'NODE_CLASS_MAPPINGS'
```
- **解决**: 检查 `core/` 目录是否存在且文件完整
- **操作**: 重新下载/克隆插件

### 问题 3: Invalid API Token
```
Invalid Replicate API token
```
- **解决**: 检查 Token 是否正确复制(无空格)
- **操作**: 重新从 Replicate 获取 Token

### 问题 4: 网络超时
```
Request timed out
```
- **解决**: 增加 Prediction 节点的 `timeout` 值(默认 300 秒)
- **原因**: 某些模型生成时间较长

---

## 📚 下一步

- 📖 阅读 [完整文档](docs/README.md)
- 💡 查看 [示例工作流](examples/)
- 🔧 探索 [预设模型指南](docs/PRESET_MODELS_GUIDE.md)

---

需要更多帮助?
- 📘 [详细安装指南](INSTALLATION.md)
- 🐛 [提交 Issue](https://github.com/your-username/comfyui-replicate-nodes/issues)
