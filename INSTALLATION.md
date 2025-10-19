# ComfyUI Replicate Nodes - 安装指南

## 📋 安装前准备

### 系统要求

- **Python**: 3.8 或更高版本
- **ComfyUI**: 已安装并可以正常运行
- **网络**: 需要能够访问 Replicate API (https://replicate.com)

### 获取 Replicate API Token

1. 访问 [Replicate](https://replicate.com) 并注册账号
2. 登录后进入账号设置 (Account Settings)
3. 找到 API Tokens 部分
4. 复制你的 API token (格式类似: `r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx`)

---

## 🚀 安装方法

### 方法一: 使用 Git Clone (推荐)

这是最简单的方法,并且便于后续更新。

```bash
# 1. 进入 ComfyUI 的 custom_nodes 目录
cd /path/to/ComfyUI/custom_nodes

# 2. 克隆本仓库
git clone https://github.com/your-username/comfyui-replicate-nodes.git

# 3. 进入插件目录
cd comfyui-replicate-nodes

# 4. 运行安装脚本
python install.py
```

### 方法二: 手动下载安装

如果无法使用 Git,可以手动下载:

```bash
# 1. 下载并解压到 custom_nodes 目录
# 确保解压后的文件夹名为 comfyui-replicate-nodes

# 2. 进入插件目录
cd /path/to/ComfyUI/custom_nodes/comfyui-replicate-nodes

# 3. 安装依赖
pip install -r requirements.txt

# 或使用 Python 安装脚本
python install.py
```

### 方法三: 使用 ComfyUI Manager (如果支持)

如果你安装了 ComfyUI Manager 插件:

1. 打开 ComfyUI Manager
2. 搜索 "Replicate Nodes"
3. 点击 Install
4. 重启 ComfyUI

---

## ✅ 验证安装

### 检查文件结构

安装完成后,你的目录应该如下所示:

```
ComfyUI/
└── custom_nodes/
    └── comfyui-replicate-nodes/     # 或你重命名的目录名
        ├── __init__.py              ✓ 必需
        ├── requirements.txt         ✓ 必需
        ├── config.json              ✓ 配置文件
        ├── install.py
        ├── pyproject.toml
        ├── core/                    ✓ 核心代码
        │   ├── __init__.py
        │   ├── nodes.py
        │   ├── replicate_client.py
        │   └── utils.py
        ├── tests/                   (可选)
        ├── docs/                    (可选)
        └── examples/                (可选)
```

### 测试导入

在 ComfyUI 目录运行:

```bash
python -c "import custom_nodes.comfyui_replicate_nodes as rn; print('节点数量:', len(rn.NODE_CLASS_MAPPINGS))"
```

应该输出: `节点数量: 5`

### 启动 ComfyUI

```bash
# 启动 ComfyUI
python main.py

# 或
python -m comfyui.main
```

检查控制台输出,应该看到类似:

```
Import times for custom nodes:
   ...
   0.2 seconds: comfyui-replicate-nodes
```

没有错误信息即表示加载成功。

---

## ⚙️ 配置 API Token

安装完成后需要配置 Replicate API Token。有三种方法:

### 方法一: 使用节点配置 (推荐,适合新手)

1. 启动 ComfyUI
2. 在节点面板中找到 **Replicate** 分类
3. 添加 **Replicate Config** 节点到画布
4. 在节点中输入你的 API Token
5. 勾选 `save_token` (保存到本地)
6. 勾选 `test_connection` (测试连接)
7. 执行节点,看到 "API token configured successfully" 即成功

### 方法二: 环境变量 (推荐,适合高级用户)

**Windows:**
```cmd
# 临时设置(当前命令行窗口)
set REPLICATE_API_TOKEN=r8_your_token_here

# 永久设置(系统环境变量)
setx REPLICATE_API_TOKEN "r8_your_token_here"
```

**Linux/Mac:**
```bash
# 临时设置
export REPLICATE_API_TOKEN=r8_your_token_here

# 永久设置 (添加到 ~/.bashrc 或 ~/.zshrc)
echo 'export REPLICATE_API_TOKEN=r8_your_token_here' >> ~/.bashrc
source ~/.bashrc
```

### 方法三: 手动编辑配置文件

编辑 `config.json` 文件:

```json
{
  "replicate_api_token": "r8_your_token_here",
  "_comment": "Enter your Replicate API token here"
}
```

---

## 🎯 快速测试

### 基础工作流测试

1. 在 ComfyUI 中创建新工作流
2. 添加以下节点并连接:

```
[Replicate Config]
    → 配置 Token

[Replicate Model Selector]
    → model_preset: "google/nano-banana"
    → 执行获取模型信息

[Replicate Dynamic Node]
    → 连接 model_info 和 model_version
    → prompt_text: "A beautiful sunset"
    → 执行准备输入

[Replicate Prediction]
    → 连接 prepared_inputs 和 model_version
    → 执行预测

[Replicate Output Processor]
    → 连接 results
    → 查看输出的图像和文本
```

3. 依次执行节点,如果一切正常,你应该能看到生成的结果

---

## 🔧 故障排查

### 问题 1: ComfyUI 启动时报 ImportError

**症状**:
```
ImportError: cannot import name 'NODE_CLASS_MAPPINGS' from 'comfyui_replicate_nodes'
```

**解决方法**:
1. 检查 `__init__.py` 是否存在
2. 检查 `core/` 目录及其文件是否完整
3. 重新运行 `python install.py`

### 问题 2: 找不到节点

**症状**: ComfyUI 界面中找不到 Replicate 分类的节点

**解决方法**:
1. 检查控制台是否有加载错误
2. 确认依赖已安装: `pip list | grep -E "aiohttp|requests"`
3. 重启 ComfyUI

### 问题 3: API Token 无效

**症状**:
```
Invalid Replicate API token
```

**解决方法**:
1. 检查 Token 是否正确复制(无多余空格)
2. 检查 Token 是否过期
3. 在 Replicate 网站重新生成 Token
4. 使用 Replicate Config 节点测试连接

### 问题 4: 网络连接失败

**症状**:
```
Network error / Connection timeout
```

**解决方法**:
1. 检查网络连接
2. 检查防火墙设置
3. 如在中国大陆,可能需要配置代理
4. 增加 Prediction 节点的 timeout 值

### 问题 5: 依赖安装失败

**症状**: `pip install -r requirements.txt` 报错

**解决方法**:
```bash
# 升级 pip
python -m pip install --upgrade pip

# 分别安装依赖
pip install aiohttp
pip install requests
pip install pillow
pip install numpy

# 如果使用虚拟环境,确保激活了正确的环境
```

---

## 📚 后续步骤

安装配置完成后:

1. 📖 阅读 [docs/QUICK_START.md](docs/QUICK_START.md) - 快速入门教程
2. 📖 阅读 [docs/README.md](docs/README.md) - 详细使用文档
3. 💡 查看 [examples/](examples/) - 示例工作流
4. 🧪 运行 [tests/](tests/) - 测试脚本验证功能

---

## 💡 提示

- 首次使用建议先用预设模型(如 `google/nano-banana`)测试
- Replicate 的免费额度有限,注意监控使用量
- 不同模型的执行时间差异很大,调整 timeout 参数
- 查看 ComfyUI 控制台日志可获取详细的错误信息

---

## 🆘 获取帮助

- GitHub Issues: [提交问题](https://github.com/your-username/comfyui-replicate-nodes/issues)
- Replicate 文档: https://replicate.com/docs
- ComfyUI 文档: https://github.com/comfyanonymous/ComfyUI

祝使用愉快! 🎉
