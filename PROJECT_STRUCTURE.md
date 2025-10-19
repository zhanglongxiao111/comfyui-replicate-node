# 项目目录结构

本插件遵循模块化的目录结构,方便维护和扩展。

## 目录说明

```
node/                           # ComfyUI 插件根目录
├── __init__.py                 # 插件入口文件 (ComfyUI 必需)
├── requirements.txt            # Python 依赖声明
├── pyproject.toml             # 项目配置
├── install.py                 # 安装脚本
├── config.json                # 用户配置文件 (API Token 等)
├── default_models_config.json # 默认模型配置
│
├── core/                      # 核心代码模块
│   ├── __init__.py
│   ├── nodes.py               # ComfyUI 节点实现
│   ├── replicate_client.py    # Replicate API 客户端
│   └── utils.py               # 工具函数
│
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── test_connection.py
│   ├── test_full_workflow.py
│   ├── test_model_capabilities.py
│   ├── test_prediction.py
│   ├── test_preset_models.py
│   ├── test_presets_simple.py
│   ├── search_nano_banana.py
│   └── verify_default_models.py
│
├── docs/                      # 文档
│   ├── README.md              # 主要说明文档
│   ├── QUICK_START.md         # 快速入门指南
│   ├── PRESET_MODELS_GUIDE.md # 预设模型指南
│   ├── CODE_REVIEW.md         # 代码审查
│   ├── TEST_REPORT.md         # 测试报告
│   ├── MODEL_COMPARISON_REPORT.md
│   └── model_capabilities_report.json
│
└── examples/                  # 示例文件
    ├── example_workflow.json
    └── example_concurrent_generation.py
```

## 文件说明

### 根目录必需文件 (ComfyUI 规范)

- **`__init__.py`**: ComfyUI 插件入口,导出 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS`
- **`requirements.txt`**: 声明插件依赖的 Python 包
- **`config.json`**: 保存用户的 API Token 等配置信息

### core/ - 核心功能模块

所有核心业务逻辑代码都放在此目录:

- **`nodes.py`**: 定义所有 ComfyUI 节点类
- **`replicate_client.py`**: 封装 Replicate API 调用
- **`utils.py`**: 通用工具函数(图像处理、配置管理等)

### tests/ - 测试模块

包含所有测试脚本,用于验证功能正确性:

- `test_*.py`: 各种功能测试
- `verify_*.py`: 验证脚本
- `search_*.py`: 搜索功能测试

### docs/ - 文档模块

所有 Markdown 文档和报告文件:

- **`README.md`**: 插件主要说明文档
- **`QUICK_START.md`**: 快速入门指南
- 其他技术文档和报告

### examples/ - 示例模块

示例代码和工作流配置:

- **`example_workflow.json`**: ComfyUI 工作流示例
- **`example_*.py`**: Python 脚本示例

## 导入路径说明

整理后的模块导入关系:

```python
# 根目录 __init__.py
from .core.nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# core/nodes.py
from .replicate_client import ReplicateClient, ModelInfo, PredictionStatus
from .utils import (load_api_token, save_api_token, ...)

# core/utils.py
# 配置文件路径指向根目录: os.path.dirname(os.path.dirname(__file__))
```

## 优势

1. **结构清晰**: 核心代码、测试、文档、示例分离
2. **易于维护**: 模块化设计便于定位和修改代码
3. **符合规范**: 遵循 ComfyUI 插件开发标准
4. **扩展友好**: 新增功能只需在对应目录添加文件
