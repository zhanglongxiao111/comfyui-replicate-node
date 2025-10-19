"""
ComfyUI Replicate Nodes
Model-specific nodes for Replicate integration
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from .replicate_client import ReplicateClient
from .utils import (
    convert_image_batch_to_base64_list,
    format_error_message,
    load_api_token,
    parse_replicate_outputs,
    save_api_token,
    stack_image_arrays,
)

logger = logging.getLogger(__name__)

try:
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    logger.warning(
        "未检测到 nest_asyncio，某些环境下可能出现事件循环冲突。"
        "若遇到 'event loop is already running'，请安装 nest_asyncio。"
    )


class ReplicateModelNodeBase:
    """Base implementation for model-specific Replicate nodes."""

    MODEL_OWNER: str = ""
    MODEL_NAME: str = ""
    SUPPORTS_NATIVE_BATCH: bool = False
    REQUIRE_IMAGE: bool = False
    MAX_REFERENCE_IMAGES: Optional[int] = None
    MAX_IMAGES: int = 5
    REQUEST_TIMEOUT: int = 300
    POLL_INTERVAL: int = 2

    _version_cache: Dict[str, str] = {}

    @classmethod
    def _model_key(cls) -> str:
        return f"{cls.MODEL_OWNER}/{cls.MODEL_NAME}"

    @classmethod
    async def _get_latest_version_id(cls, client: ReplicateClient) -> str:
        cache_key = cls._model_key()
        if cache_key in cls._version_cache:
            return cls._version_cache[cache_key]

        details = await client.get_model_details(cls.MODEL_OWNER, cls.MODEL_NAME)
        version_info = details.get("latest_version", {}) if details else {}
        version_id = version_info.get("id")
        if not version_id:
            raise RuntimeError(f"无法获取 {cache_key} 的最新版本 ID")

        cls._version_cache[cache_key] = version_id
        return version_id

    @staticmethod
    def _resolve_string(manual_value: str, port_value: Optional[str]) -> str:
        if isinstance(port_value, str) and port_value.strip():
            return port_value
        return manual_value

    def _resolve_token(self, manual_token: str, port_token: Optional[str]) -> str:
        token = self._resolve_string(manual_token, port_token)
        if not token:
            token = load_api_token()
        if not token:
            raise RuntimeError("未找到可用的 Replicate API 密钥")
        return token

    def _resolve_count(self, manual_count: int, port_count: Optional[int]) -> int:
        if isinstance(port_count, int) and port_count > 0:
            candidate = port_count
        else:
            candidate = manual_count
        candidate = max(1, candidate)
        candidate = min(candidate, self.MAX_IMAGES)
        return candidate

    def _prepare_images(self, image_batch: Any) -> List[str]:
        images = convert_image_batch_to_base64_list(image_batch, self.MAX_REFERENCE_IMAGES)
        if self.REQUIRE_IMAGE and not images:
            raise ValueError("请提供至少一张输入图片")
        return images

    async def _create_and_wait(
        self,
        client: ReplicateClient,
        version_id: str,
        inputs: Dict[str, Any],
    ):
        prediction = await client.create_prediction(
            version_id=version_id,
            inputs=inputs,
        )
        result = await client.wait_for_prediction(
            prediction_id=prediction.id,
            timeout=self.REQUEST_TIMEOUT,
            poll_interval=self.POLL_INTERVAL,
        )
        if result.status != "succeeded":
            error_message = result.error or f"预测状态: {result.status}"
            raise RuntimeError(error_message)
        return prediction, result

    async def _run_prediction_batch(
        self,
        client: ReplicateClient,
        payload: Dict[str, Any],
        desired_count: int,
    ):
        version_id = await self._get_latest_version_id(client)

        images: List[Any] = []
        text_parts: List[str] = []
        raw_records: List[Dict[str, Any]] = []
        iteration = 0

        while len(images) < desired_count:
            iteration += 1

            remaining = desired_count - len(images)
            if self.SUPPORTS_NATIVE_BATCH:
                if iteration == 1:
                    request_count = desired_count
                else:
                    request_count = remaining
            else:
                request_count = 1

            request_inputs = self._prepare_request_payload(payload, request_count, iteration)

            prediction, result = await self._create_and_wait(
                client,
                version_id,
                request_inputs,
            )

            raw_records.append(
                {
                    "prediction_id": prediction.id,
                    "inputs": request_inputs,
                    "output": result.output,
                    "logs": result.logs,
                    "status": result.status,
                }
            )

            image_arrays, texts = parse_replicate_outputs(result.output)
            if image_arrays:
                images.extend(image_arrays)
            if texts:
                text_parts.extend(texts)
            if result.logs:
                text_parts.append(result.logs)

            if self.SUPPORTS_NATIVE_BATCH:
                if len(images) >= desired_count:
                    break
                if iteration >= desired_count:
                    raise RuntimeError("模型未返回足够的图像，请尝试减少生成数量或检查输入。")
                continue

            if iteration >= desired_count:
                break

            if not image_arrays:
                raise RuntimeError("模型未返回图像输出，请检查输入参数")

        if not images:
            raise RuntimeError("模型未返回可用图像")

        return images[:desired_count], text_parts, raw_records

    def _prepare_request_payload(
        self,
        payload: Dict[str, Any],
        requested_count: int,
        iteration: int,
    ) -> Dict[str, Any]:
        return dict(payload)

    async def _async_predict(
        self,
        token: str,
        payload: Dict[str, Any],
        desired_count: int,
    ):
        async with ReplicateClient(token) as client:
            return await self._run_prediction_batch(client, payload, desired_count)

    def _execute_predictions(
        self,
        token: str,
        payload: Dict[str, Any],
        desired_count: int,
    ):
        created_loop = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            created_loop = True

        try:
            return loop.run_until_complete(
                self._async_predict(token, payload, desired_count)
            )
        finally:
            if created_loop:
                loop.close()

    def _build_payload(
        self,
        prompt: str,
        image_inputs: List[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def predict(self, **kwargs):
        try:
            prompt = self._resolve_string(
                kwargs.get("提示词", ""),
                kwargs.get("提示词输入"),
            )
            if not prompt or not prompt.strip():
                raise ValueError("提示词不能为空")

            token = self._resolve_token(
                kwargs.get("API密钥", ""),
                kwargs.get("API密钥输入"),
            )
            desired_count = self._resolve_count(
                kwargs.get("生成数量", 1),
                kwargs.get("数量输入"),
            )

            image_inputs = self._prepare_images(kwargs.get("输入图片"))
            payload = self._build_payload(prompt, image_inputs, kwargs)

            image_arrays, text_parts, raw_records = self._execute_predictions(
                token,
                payload,
                desired_count,
            )

            image_tensor = stack_image_arrays(image_arrays)
            text_output = "\n".join(part for part in text_parts if part).strip()
            raw_output = json.dumps(raw_records, ensure_ascii=False, indent=2)

            return (image_tensor, text_output, raw_output)

        except Exception as exc:
            formatted = format_error_message(exc)
            lower_msg = formatted.lower()
            if "flagged as sensitive" in lower_msg or "e005" in lower_msg:
                fallback = json.dumps(
                    {"error": formatted, "model": self._model_key()}, ensure_ascii=False, indent=2
                )
                return (None, formatted, fallback)

            raise RuntimeError(formatted)


class ReplicateQwenImageEditPlus(ReplicateModelNodeBase):
    MODEL_OWNER = "qwen"
    MODEL_NAME = "qwen-image-edit-plus"
    REQUIRE_IMAGE = True
    MAX_REFERENCE_IMAGES = 4
    DESCRIPTION = "图像编辑：根据中文提示修改输入图片，支持多图批量生成。"
    CATEGORY = "Replicate/图像"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "API密钥": ("STRING", {
                    "default": "",
                    "password": True,
                    "placeholder": "留空使用已保存的密钥",
                    "tooltip": "用于访问 Replicate 服务的 API 密钥，可通过端口输入或自动读取配置。"
                }),
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入编辑提示",
                    "tooltip": "描述对输入图片进行修改的中文指令，可使用端口覆盖。"
                }),
                "输入图片": ("IMAGE", {
                    "tooltip": "待编辑的参考图片，支持批量图像。"
                }),
                "生成数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "tooltip": "本轮生成目标图像的数量。"
                }),
            },
            "optional": {
                "提示词输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的提示词，优先级高于面板输入。"
                }),
                "API密钥输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的 API 密钥，优先级高于面板输入。"
                }),
                "数量输入": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "tooltip": "通过连线设置的生成数量，大于 0 时覆盖面板数值。"
                }),
                "极速模式": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "开启后使用官方加速配置，生成更快但可能影响细节。"
                }),
                "输出比例": ([
                    "match_input_image",
                    "1:1",
                    "16:9",
                    "9:16",
                    "4:3",
                    "3:4"
                ], {
                    "default": "match_input_image",
                    "tooltip": "生成图片的宽高比，默认跟随输入图片。"
                }),
                "输出格式": (["png", "webp", "jpg"], {
                    "default": "png",
                    "tooltip": "生成文件格式，选择 PNG 可保留更多细节。"
                }),
                "输出质量": ("INT", {
                    "default": 95,
                    "min": 0,
                    "max": 100,
                    "tooltip": "导出 JPEG/WebP 时的质量值，PNG 格式可忽略。"
                }),
                "禁用安全检查": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "关闭官方安全审核，可能输出敏感内容。"
                }),
                "随机种子": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 4294967295,
                    "tooltip": "固定随机种子复现实验结果，-1 表示随机。"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("生成图像", "文本输出", "原始结果")
    FUNCTION = "predict"
    CATEGORY = "Replicate/模型"

    def _build_payload(
        self,
        prompt: str,
        image_inputs: List[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        quality = int(params.get("输出质量", 95))
        quality = max(0, min(100, quality))

        payload = {
            "prompt": prompt,
            "image": image_inputs,
            "go_fast": bool(params.get("极速模式", True)),
            "aspect_ratio": params.get("输出比例", "match_input_image"),
            "output_format": params.get("输出格式", "png"),
            "output_quality": quality,
            "disable_safety_checker": bool(params.get("禁用安全检查", False)),
        }

        seed = params.get("随机种子", -1)
        if isinstance(seed, int) and seed >= 0:
            payload["seed"] = seed

        return payload


class ReplicateSeedream4(ReplicateModelNodeBase):
    MODEL_OWNER = "bytedance"
    MODEL_NAME = "seedream-4"
    MAX_REFERENCE_IMAGES = 10
    SUPPORTS_NATIVE_BATCH = True
    DESCRIPTION = "Seedream 4：文本或参考图生成多张高清图像。"
    CATEGORY = "Replicate/图像"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "API密钥": ("STRING", {
                    "default": "",
                    "password": True,
                    "placeholder": "留空使用已保存的密钥",
                    "tooltip": "用于访问 Replicate 服务的 API 密钥，可通过端口输入或自动读取配置。"
                }),
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入生成提示",
                    "tooltip": "描述目标场景与风格的中文指令，可通过端口覆盖。"
                }),
                "生成数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "tooltip": "本轮生成目标图片数量，支持最多 5 张。"
                }),
            },
            "optional": {
                "提示词输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的提示词，优先级高于面板输入。"
                }),
                "API密钥输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的 API 密钥，优先级高于面板输入。"
                }),
                "数量输入": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "tooltip": "通过连线设置的生成数量，大于 0 时覆盖面板数值。"
                }),
                "输入图片": ("IMAGE", {
                    "tooltip": "可选的参考图片，用于图生图或多图混合生成。"
                }),
                "分辨率": (["1K", "2K", "4K", "custom"], {
                    "default": "2K",
                    "tooltip": "输出分辨率预设，选择 custom 时需指定宽高。"
                }),
                "长宽比": ([
                    "match_input_image",
                    "1:1",
                    "4:3",
                    "3:4",
                    "16:9",
                    "9:16",
                    "3:2",
                    "2:3",
                    "21:9"
                ], {
                    "default": "match_input_image",
                    "tooltip": "输出图像的宽高比，默认与输入图片匹配。"
                }),
                "自定义宽度": ("INT", {
                    "default": 2048,
                    "min": 1024,
                    "max": 4096,
                    "tooltip": "当分辨率选择 custom 时的输出宽度。"
                }),
                "自定义高度": ("INT", {
                    "default": 2048,
                    "min": 1024,
                    "max": 4096,
                    "tooltip": "当分辨率选择 custom 时的输出高度。"
                }),
                "顺序生成": (["disabled", "auto"], {
                    "default": "disabled",
                    "tooltip": "自动生成同主题多图时选择 auto，单图生成保持 disabled。"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("生成图像", "文本输出", "原始结果")
    FUNCTION = "predict"
    CATEGORY = "Replicate/模型"

    def _build_payload(
        self,
        prompt: str,
        image_inputs: List[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        size = params.get("分辨率", "2K")
        aspect_ratio = params.get("长宽比", "match_input_image")
        mode = params.get("顺序生成", "disabled")

        payload: Dict[str, Any] = {
            "prompt": prompt,
            "image_input": image_inputs,
            "size": size,
            "aspect_ratio": aspect_ratio,
            "sequential_image_generation": mode,
        }

        if size == "custom":
            width = int(params.get("自定义宽度", 2048))
            height = int(params.get("自定义高度", 2048))
            width = max(1024, min(4096, width))
            height = max(1024, min(4096, height))
            payload["width"] = width
            payload["height"] = height

        return payload

    def _prepare_request_payload(
        self,
        payload: Dict[str, Any],
        requested_count: int,
        iteration: int,
    ) -> Dict[str, Any]:
        data = dict(payload)

        if requested_count > 1:
            data["sequential_image_generation"] = "auto"
            data["max_images"] = min(15, requested_count)
        else:
            data["sequential_image_generation"] = data.get(
                "sequential_image_generation",
                "disabled",
            )
            data.pop("max_images", None)

        return data


class ReplicateNanoBanana(ReplicateModelNodeBase):
    MODEL_OWNER = "google"
    MODEL_NAME = "nano-banana"
    MAX_REFERENCE_IMAGES = 4
    DESCRIPTION = "Nano Banana：轻量快速的多模态图像生成。"
    CATEGORY = "Replicate/图像"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "API密钥": ("STRING", {
                    "default": "",
                    "password": True,
                    "placeholder": "留空使用已保存的密钥",
                    "tooltip": "用于访问 Replicate 服务的 API 密钥，可通过端口输入或自动读取配置。"
                }),
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入生成提示",
                    "tooltip": "描述目标画面的中文指令，可通过端口覆盖。"
                }),
                "生成数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "tooltip": "本轮生成目标图片数量，支持最多 5 张。"
                }),
            },
            "optional": {
                "提示词输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的提示词，优先级高于面板输入。"
                }),
                "API密钥输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的 API 密钥，优先级高于面板输入。"
                }),
                "数量输入": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "tooltip": "通过连线设置的生成数量，大于 0 时覆盖面板数值。"
                }),
                "输入图片": ("IMAGE", {
                    "tooltip": "可选的参考图片列表，帮助模型保持角色与风格一致。"
                }),
                "长宽比": ([
                    "match_input_image",
                    "1:1",
                    "2:3",
                    "3:2",
                    "3:4",
                    "4:3",
                    "4:5",
                    "5:4",
                    "9:16",
                    "16:9",
                    "21:9"
                ], {
                    "default": "match_input_image",
                    "tooltip": "输出图像的宽高比，默认与输入图片匹配。"
                }),
                "输出格式": (["jpg", "png"], {
                    "default": "jpg",
                    "tooltip": "生成文件格式，PNG 可提供无损质量。"
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("生成图像", "文本输出", "原始结果")
    FUNCTION = "predict"
    CATEGORY = "Replicate/模型"

    def _build_payload(
        self,
        prompt: str,
        image_inputs: List[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "prompt": prompt,
            "image_input": image_inputs,
            "aspect_ratio": params.get("长宽比", "match_input_image"),
            "output_format": params.get("输出格式", "jpg"),
        }


class ReplicateAPIKeyLink:
    """提供或持久化 Replicate API 密钥的节点。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "API密钥": ("STRING", {
                    "default": "",
                    "password": True,
                    "placeholder": "手动输入或留空",
                    "tooltip": "面板输入的 API 密钥，若留空可使用端口数据或已保存配置。"
                }),
                "保存到配置": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "选中后将密钥写入插件 config.json，下次自动读取。"
                }),
                "允许配置回退": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "当未提供密钥时，允许读取已保存或环境变量中的密钥。"
                }),
            },
            "optional": {
                "API密钥输入": ("STRING", {
                    "default": "",
                    "tooltip": "通过连线传入的密钥，优先级高于面板输入。"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("API密钥", "状态")
    FUNCTION = "link"
    DESCRIPTION = "读取、复用或保存 Replicate API 密钥，便于在多个节点之间共享。"
    CATEGORY = "Replicate/配置"

    def link(self, **kwargs):
        try:
            manual = kwargs.get("API密钥", "")
            incoming = kwargs.get("API密钥输入")
            allow_fallback = bool(kwargs.get("允许配置回退", True))

            token = manual
            if isinstance(incoming, str) and incoming.strip():
                token = incoming

            if not token and allow_fallback:
                token = load_api_token()

            if not token:
                raise ValueError("未提供 API 密钥，且未启用配置回退")

            if kwargs.get("保存到配置", False):
                save_api_token(token)
                status = "已保存 API 密钥"
            elif token == manual or (isinstance(incoming, str) and incoming.strip()):
                status = "使用输入的 API 密钥"
            else:
                status = "使用已保存的 API 密钥"

            return (token, status)

        except Exception as exc:
            raise RuntimeError(format_error_message(exc))


NODE_CLASS_MAPPINGS = {
    "ReplicateQwenImageEditPlus": ReplicateQwenImageEditPlus,
    "ReplicateSeedream4": ReplicateSeedream4,
    "ReplicateNanoBanana": ReplicateNanoBanana,
    "ReplicateAPIKeyLink": ReplicateAPIKeyLink,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ReplicateQwenImageEditPlus": "qwen/qwen-image-edit-plus",
    "ReplicateSeedream4": "bytedance/seedream-4",
    "ReplicateNanoBanana": "google/nano-banana",
    "ReplicateAPIKeyLink": "Replicate API 密钥",
}
