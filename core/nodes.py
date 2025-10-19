"""
ComfyUI Replicate Nodes
Core node implementations for Replicate integration
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image

from .replicate_client import ReplicateClient, ModelInfo, PredictionStatus
from .utils import (
    load_api_token, save_api_token, convert_image_to_base64,
    format_model_display_name, extract_model_schema, get_parameter_type,
    get_parameter_options, is_image_parameter, sanitize_inputs,
    format_error_message
)

logger = logging.getLogger(__name__)

class ReplicateModelSelector:
    """Node for selecting Replicate models"""

    # 预设的推荐模型列表
    PRESET_MODELS = [
        "google/nano-banana",  # Gemini 2.5 Flash Image
        "qwen/qwen-image-edit",  # Qwen Image Edit
        "stability-ai/sdxl",  # Stable Diffusion XL
        "black-forest-labs/flux-schnell",  # FLUX Schnell
        "Custom (use search)"  # 自定义搜索选项
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_preset": (cls.PRESET_MODELS, {
                    "default": "google/nano-banana"
                }),
                "search_query": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "仅在选择'Custom'时使用搜索"
                }),
                "api_token": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Replicate API token (leave empty to use saved token)"
                }),
                "refresh": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "limit": ("INT", {"default": 50, "min": 1, "max": 100}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "DICT")  # model_id, model_name, model_version, model_info
    RETURN_NAMES = ("model_id", "model_name", "model_version", "model_info")
    FUNCTION = "select_model"
    CATEGORY = "Replicate"

    def select_model(self, model_preset: str, search_query: str, api_token: str, refresh: bool,
                    limit: int = 50) -> Tuple[str, str, str, Dict[str, Any]]:
        """Select a model from Replicate"""
        try:
            # Use provided token or load saved token
            token = api_token if api_token else load_api_token()
            if not token:
                raise ValueError("No API token provided. Please provide a token or save one first.")

            # Run async operation in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _get_models():
                async with ReplicateClient(token) as client:
                    if refresh:
                        client.clear_cache()

                    # 判断是使用预设模型还是搜索
                    if model_preset != "Custom (use search)":
                        # 使用预设模型
                        logger.info(f"使用预设模型: {model_preset}")
                        owner, name = model_preset.split('/')

                        # 直接获取模型详情
                        details = await client.get_model_details(owner, name)

                        # 构造模型信息(类似list_models返回的格式)
                        class PresetModel:
                            def __init__(self, owner, name, details):
                                self.owner = owner
                                self.name = name
                                self.description = details.get('description', '')
                                self.visibility = details.get('visibility', 'public')
                                self.url = details.get('url', '')
                                self.latest_version = details.get('latest_version')

                        selected_model = PresetModel(owner, name, details)

                    else:
                        # 使用搜索功能
                        logger.info(f"使用搜索: {search_query}")
                        models = await client.list_models(search=search_query if search_query else None,
                                                        limit=limit)

                        if not models:
                            return None, None, None, {}

                        # 选择第一个搜索结果
                        selected_model = models[0]

                    # Get model details
                    details = await client.get_model_details(selected_model.owner, selected_model.name)

                    # Get latest version
                    version_id = None
                    version_schema: Dict[str, Any] = {}
                    if selected_model.latest_version:
                        version_id = selected_model.latest_version.get('id')
                        version_schema = extract_model_schema(selected_model.latest_version)

                    model_info = {
                        'owner': selected_model.owner,
                        'name': selected_model.name,
                        'description': selected_model.description,
                        'visibility': selected_model.visibility,
                        'url': selected_model.url,
                        'details': details,
                        'version_id': version_id,
                        'schema': version_schema,
                        'schema_version_id': version_id
                    }

                    return f"{selected_model.owner}/{selected_model.name}", \
                           f"{selected_model.owner}/{selected_model.name}", \
                           version_id or "", model_info

            model_id, model_name, model_version, model_info = loop.run_until_complete(_get_models())
            loop.close()

            if not model_id:
                raise ValueError("No models found")

            return model_id, model_name, model_version, model_info

        except Exception as e:
            error_msg = format_error_message(e)
            raise RuntimeError(error_msg)

class ReplicateDynamicNode:
    """Dynamic node that creates inputs based on model schema"""

    # Class-level schema cache to avoid repeated API calls
    _schema_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_info": ("DICT", {}),
                "model_version": ("STRING", {"default": ""}),
                "api_token": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Replicate API token (leave empty to use saved token)"
                }),
                "prompt_text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入提示词"
                }),
            },
            "optional": {
                "primary_image": ("IMAGE",),  # ComfyUI IMAGE type (torch.Tensor [B,H,W,C] in 0-1 range)
                "secondary_image": ("IMAGE",),
                "tertiary_image": ("IMAGE",),
                "quaternary_image": ("IMAGE",),
                "param_overrides_json": ("STRING", {
                    "default": "{}",
                    "multiline": True,
                    "placeholder": "JSON 格式的额外参数，例如 {\"guidance_scale\": 7.5}"
                }),
                "param_overrides": ("DICT", {}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("DICT", "DICT")  # Prepared inputs, schema summary
    RETURN_NAMES = ("prepared_inputs", "schema_summary")
    FUNCTION = "prepare_inputs"
    CATEGORY = "Replicate"
    OUTPUT_NODE = False

    def prepare_inputs(self, model_info: Dict[str, Any], model_version: str,
                      api_token: str, prompt_text: str,
                      primary_image: Any = None, secondary_image: Any = None,
                      tertiary_image: Any = None, quaternary_image: Any = None,
                      param_overrides_json: str = "{}", param_overrides: Optional[Dict[str, Any]] = None,
                      prompt: Dict = None, extra_pnginfo: Dict = None,
                      unique_id: str = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Prepare inputs based on model schema"""
        try:
            if not model_info or not model_version:
                raise ValueError("No model selected or version available")

            # Use provided token or load saved token
            token = api_token if api_token else load_api_token()
            if not token:
                raise ValueError("No API token provided")

            owner = model_info.get('owner')
            name = model_info.get('name')
            version_id = model_version or model_info.get('version_id')

            if not owner or not name:
                raise ValueError("模型信息缺少 owner/name 字段")

            # 获取对应版本的 schema
            schema: Dict[str, Any] = {}
            resolved_version_id = version_id

            schema_from_model_info = model_info.get("schema")
            schema_version_id = model_info.get("schema_version_id") or model_info.get("version_id")

            # 尝试从类级缓存获取
            cache_key = f"{owner}/{name}@{version_id or 'latest'}"
            if cache_key in self._schema_cache:
                schema = self._schema_cache[cache_key]['schema']
                resolved_version_id = self._schema_cache[cache_key]['version_id']
            elif schema_from_model_info and (not version_id or schema_version_id == version_id):
                schema = schema_from_model_info
                resolved_version_id = schema_version_id or resolved_version_id
                # 缓存到类级缓存
                self._schema_cache[cache_key] = {'schema': schema, 'version_id': resolved_version_id}
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _fetch_schema():
                    async with ReplicateClient(token) as client:
                        version_payload: Dict[str, Any]
                        if version_id:
                            version_payload = await client.get_model_version(owner, name, version_id)
                        else:
                            details = await client.get_model_details(owner, name)
                            version_payload = details.get("latest_version", {})
                        return extract_model_schema(version_payload), version_payload.get("id", version_id)

                try:
                    schema, resolved_version_id = loop.run_until_complete(_fetch_schema())
                    # 缓存获取到的 schema
                    self._schema_cache[cache_key] = {'schema': schema, 'version_id': resolved_version_id}
                finally:
                    loop.close()

            if not model_version and resolved_version_id:
                model_version = resolved_version_id

            if not schema:
                logger.warning("模型 %s/%s 缺少输入 Schema，返回空输入", owner, name)
                empty_summary = self._build_schema_summary({}, model_version)
                return ({}, empty_summary)

            schema_summary = self._build_schema_summary(schema, model_version or resolved_version_id)

            # 解析 JSON overrides
            overrides_raw: Dict[str, Any] = {}
            if param_overrides_json and param_overrides_json.strip():
                try:
                    overrides_raw.update(json.loads(param_overrides_json))
                except (ValueError, TypeError) as json_error:
                    raise ValueError(f"参数 JSON 解析失败: {json_error}") from json_error

            if isinstance(param_overrides, dict):
                overrides_raw.update(param_overrides)

            # 来自节点 UI 的当前输入（例如 prompt_text）
            current_values = {}
            if prompt and unique_id and str(unique_id) in prompt:
                current_values = prompt[str(unique_id)].get('inputs', {})

            # 准备图片输入队列
            image_queue = []
            for idx, img in enumerate((primary_image, secondary_image, tertiary_image, quaternary_image), 1):
                if img is not None:
                    try:
                        processed_img = self._process_image_input(img, prompt)
                        image_queue.append(processed_img)
                    except Exception as img_error:
                        logger.error(f"处理第{idx}个图片输入时失败: {img_error}")
                        raise ValueError(f"图片输入{idx}处理失败: {format_error_message(img_error)}")

            # 处理 overrides：区分图片和常规参数
            manual_overrides: Dict[str, Any] = {}
            image_overrides: Dict[str, str] = {}

            for param_name, override_value in overrides_raw.items():
                if param_name not in schema:
                    logger.debug("忽略未知参数 %s 的 override", param_name)
                    continue

                param_config = schema[param_name]

                if is_image_parameter(param_config):
                    image_overrides[param_name] = self._process_image_input(override_value, prompt)
                else:
                    manual_overrides[param_name] = override_value

            # 对常规参数做类型安全转换
            if manual_overrides:
                sanitized = sanitize_inputs(manual_overrides,
                                            {name: schema[name] for name in manual_overrides})
            else:
                sanitized = {}

            prepared_inputs: Dict[str, Any] = {}

            for param_name, param_config in schema.items():
                # 1. override 优先
                if param_name in sanitized:
                    prepared_inputs[param_name] = sanitized[param_name]
                    continue
                if param_name in image_overrides:
                    prepared_inputs[param_name] = image_overrides[param_name]
                    continue

                # 2. 图片参数：按顺序取队列
                if is_image_parameter(param_config):
                    if image_queue:
                        prepared_inputs[param_name] = image_queue.pop(0)
                        continue
                    # 若 default 存在则使用
                    if 'default' in param_config:
                        prepared_inputs[param_name] = param_config['default']
                        continue
                    # 无图片且必填，直接报错
                    if param_config.get('required', False):
                        raise ValueError(f"模型参数 '{param_name}' 需要图片输入，请连接图片端口或在参数中提供。")
                    continue

                # 3. 提示词相关参数
                if self._is_prompt_parameter(param_name, param_config):
                    value = prompt_text or current_values.get(param_name)
                    if value:
                        prepared_inputs[param_name] = str(value)
                        continue

                # 4. 其他参数：尝试使用当前 UI 值或默认值
                if param_name in current_values:
                    value = current_values[param_name]
                    sanitized_current = sanitize_inputs({param_name: value}, {param_name: param_config})
                    prepared_inputs.update(sanitized_current)
                    continue

                if 'default' in param_config:
                    prepared_inputs[param_name] = param_config['default']
                    continue

                if param_config.get('required', False):
                    raise ValueError(f"缺少必填参数 '{param_name}'，请在 JSON 参数或端口中提供。")

            return (prepared_inputs, schema_summary)

        except Exception as e:
            error_msg = format_error_message(e)
            raise RuntimeError(error_msg)

    def _process_image_input(self, image_input: Any, prompt: Dict) -> str:
        """Process image input from node connections"""
        try:
            # 直接支持 torch.Tensor / numpy / PIL
            try:
                import torch
            except ImportError:
                torch = None

            if torch is not None and isinstance(image_input, torch.Tensor):
                image_input = image_input.detach().cpu().numpy()

            if isinstance(image_input, Image.Image):
                return convert_image_to_base64(image_input)

            if isinstance(image_input, np.ndarray):
                return convert_image_to_base64(image_input)

            if isinstance(image_input, list) and len(image_input) > 0:
                # Assume it's an image tensor from another node
                image_tensor = image_input[0]
                if torch is not None and isinstance(image_tensor, torch.Tensor):
                    image_tensor = image_tensor.detach().cpu().numpy()
                if isinstance(image_tensor, np.ndarray):
                    return convert_image_to_base64(image_tensor)
            elif isinstance(image_input, str):
                # Assume it's a file path or URL
                if image_input.startswith('data:image'):
                    return image_input
                if image_input.startswith(('http://', 'https://')):
                    return image_input
                else:
                    # Try to load local image
                    image = Image.open(image_input)
                    return convert_image_to_base64(image)

            # If we can't process it, return as-is
            return str(image_input)

        except Exception as e:
            logger.warning(f"Failed to process image input: {str(e)}")
            return str(image_input)

    def _is_prompt_parameter(self, param_name: str, param_config: Dict[str, Any]) -> bool:
        """Determine if parameter corresponds to prompt/text input"""
        if param_config.get('type', 'string') != 'string':
            return False

        keywords = ['prompt', 'text', 'caption', 'description', 'query']
        name_lower = param_name.lower()
        title_lower = param_config.get('title', '').lower()

        return any(keyword in name_lower or keyword in title_lower for keyword in keywords)

    def _build_schema_summary(self, schema: Dict[str, Any], version_id: Optional[str]) -> Dict[str, Any]:
        """Summarize schema information for UI 显示"""
        summary: Dict[str, Any] = {}

        for param_name, param_config in schema.items():
            summary[param_name] = {
                "type": param_config.get("type", "string"),
                "required": param_config.get("required", False),
                "default": param_config.get("default"),
                "enum": param_config.get("enum"),
                "description": param_config.get("description"),
                "title": param_config.get("title", param_name),
                "is_image": is_image_parameter(param_config),
                "is_prompt": self._is_prompt_parameter(param_name, param_config),
            }

        summary["_meta"] = {"version_id": version_id}
        return summary

    @classmethod
    def IS_CHANGED(cls, model_info: Dict[str, Any], model_version: str,
                   api_token: str, prompt_text: str = "",
                   primary_image: Any = None, secondary_image: Any = None,
                   tertiary_image: Any = None, quaternary_image: Any = None,
                   param_overrides_json: str = "{}", param_overrides: Optional[Dict[str, Any]] = None,
                   **kwargs):
        """Check if node inputs have changed"""
        return hash((
            str(model_info),
            model_version,
            api_token,
            prompt_text,
            param_overrides_json,
            str(param_overrides)
        ))

class ReplicatePrediction:
    """Node for executing Replicate predictions"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_version": ("STRING", {"default": ""}),
                "prepared_inputs": ("DICT", {}),
                "api_token": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Replicate API token (leave empty to use saved token)"
                }),
                "timeout": ("INT", {"default": 300, "min": 10, "max": 1800}),
                "poll_interval": ("INT", {"default": 2, "min": 1, "max": 10}),
            },
            "optional": {
                "webhook_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Optional webhook URL for notifications"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "DICT")  # prediction_id, status, results
    RETURN_NAMES = ("prediction_id", "status", "results")
    FUNCTION = "run_prediction"
    CATEGORY = "Replicate"
    OUTPUT_NODE = True

    def run_prediction(self, model_version: str, prepared_inputs: Dict[str, Any],
                      api_token: str, timeout: int = 300, poll_interval: int = 2,
                      webhook_url: str = "") -> Tuple[str, str, Dict[str, Any]]:
        """Run prediction on Replicate"""
        try:
            if not model_version:
                raise ValueError("No model version provided")
            if not prepared_inputs:
                raise ValueError("No inputs prepared")

            # Use provided token or load saved token
            token = api_token if api_token else load_api_token()
            if not token:
                raise ValueError("No API token provided")

            # Run async operation in thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _run_prediction():
                async with ReplicateClient(token) as client:
                    # Create prediction
                    prediction = await client.create_prediction(
                        version_id=model_version,
                        inputs=prepared_inputs,
                        webhook=webhook_url if webhook_url else None
                    )

                    logger.info(f"Created prediction: {prediction.id}")

                    # Wait for completion
                    try:
                        result = await client.wait_for_prediction(
                            prediction_id=prediction.id,
                            timeout=timeout,
                            poll_interval=poll_interval
                        )

                        if result.status == 'succeeded':
                            logger.info(f"Prediction {prediction.id} completed successfully")
                            return prediction.id, result.status, {
                                'output': result.output,
                                'logs': result.logs,
                                'created_at': result.created_at,
                                'completed_at': result.completed_at
                            }
                        elif result.status == 'failed':
                            error_msg = result.error or "Prediction failed"
                            raise RuntimeError(f"Prediction failed: {error_msg}")
                        elif result.status == 'canceled':
                            raise RuntimeError("Prediction was canceled")
                        else:
                            raise RuntimeError(f"Unexpected prediction status: {result.status}")

                    except TimeoutError:
                        # Cancel the prediction
                        await client.cancel_prediction(prediction.id)
                        raise RuntimeError(f"Prediction timed out after {timeout} seconds")

            prediction_id, status, results = loop.run_until_complete(_run_prediction())
            loop.close()

            return prediction_id, status, results

        except Exception as e:
            error_msg = format_error_message(e)
            raise RuntimeError(error_msg)

class ReplicateConfig:
    """Node for configuring Replicate API token"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_token": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "password": True,
                    "placeholder": "Enter your Replicate API token"
                }),
                "save_token": ("BOOLEAN", {"default": True}),
                "test_connection": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "BOOLEAN")  # status, success
    RETURN_NAMES = ("status", "success")
    FUNCTION = "configure_token"
    CATEGORY = "Replicate"
    OUTPUT_NODE = True

    def configure_token(self, api_token: str, save_token: bool, test_connection: bool) -> Tuple[str, bool]:
        """Configure and optionally test Replicate API token"""
        try:
            if not api_token:
                return ("No token provided", False)

            # Test connection if requested
            if test_connection:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def _test_connection():
                    async with ReplicateClient(api_token) as client:
                        # Try to list models to test connection
                        await client.list_models(limit=1)
                        return True

                try:
                    success = loop.run_until_complete(_test_connection())
                    loop.close()
                    if not success:
                        return ("Connection test failed", False)
                except Exception as e:
                    loop.close()
                    return (f"Connection test failed: {format_error_message(e)}", False)

            # Save token if requested
            if save_token:
                save_api_token(api_token)

            return ("API token configured successfully", True)

        except Exception as e:
            error_msg = format_error_message(e)
            return (error_msg, False)

class ReplicateOutputProcessor:
    """Node for processing Replicate prediction outputs"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "results": ("DICT", {}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")  # image, text, raw_output
    RETURN_NAMES = ("image", "text", "raw_output")
    FUNCTION = "process_output"
    CATEGORY = "Replicate"
    OUTPUT_NODE = False

    def process_output(self, results: Dict[str, Any]) -> Tuple[Any, str, str]:
        """Process Replicate prediction output"""
        try:
            import torch
            import requests
            from io import BytesIO
        except ImportError as e:
            raise RuntimeError(f"缺少必要的依赖: {e}")

        output = results.get('output')
        if not output:
            return (None, "", json.dumps(results, indent=2))

        # 处理不同类型的输出
        image_tensor = None
        text_output = ""

        # 如果输出是列表
        if isinstance(output, list):
            # 尝试处理图像URL
            for item in output:
                if isinstance(item, str) and item.startswith(('http://', 'https://')):
                    try:
                        response = requests.get(item, timeout=30)
                        response.raise_for_status()
                        img = Image.open(BytesIO(response.content))

                        # 转换为ComfyUI格式: [B,H,W,C] in 0-1 range
                        img_array = np.array(img.convert('RGB')).astype(np.float32) / 255.0
                        image_tensor = torch.from_numpy(img_array).unsqueeze(0)  # Add batch dimension
                        break
                    except Exception as e:
                        logger.warning(f"下载图像失败 {item}: {e}")
                        continue
                elif isinstance(item, str):
                    text_output += item + "\n"

        # 如果输出是单个URL
        elif isinstance(output, str):
            if output.startswith(('http://', 'https://')):
                try:
                    response = requests.get(output, timeout=30)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))

                    img_array = np.array(img.convert('RGB')).astype(np.float32) / 255.0
                    image_tensor = torch.from_numpy(img_array).unsqueeze(0)
                except Exception as e:
                    logger.warning(f"下载图像失败: {e}")
                    text_output = output
            else:
                text_output = output

        raw_output = json.dumps(output, indent=2, ensure_ascii=False)

        return (image_tensor, text_output.strip(), raw_output)

# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "ReplicateModelSelector": ReplicateModelSelector,
    "ReplicateDynamicNode": ReplicateDynamicNode,
    "ReplicatePrediction": ReplicatePrediction,
    "ReplicateConfig": ReplicateConfig,
    "ReplicateOutputProcessor": ReplicateOutputProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ReplicateModelSelector": "Replicate Model Selector",
    "ReplicateDynamicNode": "Replicate Dynamic Node",
    "ReplicatePrediction": "Replicate Prediction",
    "ReplicateConfig": "Replicate Config",
    "ReplicateOutputProcessor": "Replicate Output Processor",
}
