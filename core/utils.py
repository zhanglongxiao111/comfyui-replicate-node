"""
Utility functions for ComfyUI Replicate nodes
"""

import os
import json
import base64
import io
from typing import Dict, Any, Union, Optional, List
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _load_image_from_string(data: str) -> Optional[Image.Image]:
    """Decode image from URL or base64 string."""
    if not isinstance(data, str):
        return None

    try:
        if data.startswith(("http://", "https://")):
            import requests

            response = requests.get(data, timeout=30)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))

        if data.startswith("data:image"):
            header, _, b64_data = data.partition(",")
            if ";base64" not in header:
                return None
            decoded = base64.b64decode(b64_data)
            return Image.open(io.BytesIO(decoded))
    except Exception as exc:
        logger.warning("Failed to load image source: %s", exc)
        return None

    # Try raw base64 without prefix
    try:
        decoded = base64.b64decode(data)
        return Image.open(io.BytesIO(decoded))
    except Exception:
        return None


def convert_image_batch_to_base64_list(
    images: Any,
    limit: Optional[int] = None,
) -> List[str]:
    """Convert batched images to base64 data URI strings."""
    if images is None:
        return []

    encoded: List[str] = []

    try:
        import torch  # type: ignore
    except ImportError:
        torch = None  # type: ignore

    if torch is not None and isinstance(images, torch.Tensor):
        tensor = images.detach().cpu()
        if tensor.ndim == 3:
            tensor = tensor.unsqueeze(0)
        max_count = tensor.shape[0]
        if limit is not None:
            max_count = min(max_count, limit)
        for idx in range(max_count):
            encoded.append(convert_image_to_base64(tensor[idx : idx + 1]))
        return encoded

    if isinstance(images, list):
        items = images if limit is None else images[:limit]
        for item in items:
            encoded.append(convert_image_to_base64(item))
        return encoded

    encoded.append(convert_image_to_base64(images))
    return encoded


def parse_replicate_outputs(output: Any) -> tuple[List[np.ndarray], List[str]]:
    """Parse Replicate outputs into image arrays (float32 0-1) and text fragments."""
    image_arrays: List[np.ndarray] = []
    text_parts: List[str] = []

    entries = output if isinstance(output, list) else [output]

    for entry in entries:
        if isinstance(entry, str):
            image = _load_image_from_string(entry)
            if image:
                image = image.convert("RGB")
                arr = np.array(image).astype(np.float32) / 255.0
                image_arrays.append(arr)
            else:
                text_parts.append(entry)
        elif entry is not None:
            try:
                text_parts.append(json.dumps(entry, ensure_ascii=False))
            except TypeError:
                text_parts.append(str(entry))

    return image_arrays, text_parts


def stack_image_arrays(arrays: List[np.ndarray]):
    """Stack image arrays into a torch tensor."""
    if not arrays:
        return None

    try:
        import torch  # type: ignore
    except ImportError as exc:
        raise RuntimeError("torch is required to process images") from exc

    stacked = np.stack(arrays, axis=0).astype(np.float32)
    return torch.from_numpy(stacked)


def load_api_token() -> Optional[str]:
    """Load Replicate API token from environment variables or config file"""
    # Try environment variable first
    token = os.getenv('REPLICATE_API_TOKEN')
    if token:
        return token

    # Try config file (in plugin root directory, one level up from core/)
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('replicate_api_token')
        except Exception as e:
            logger.warning(f"Failed to load config file: {str(e)}")

    return None

def save_api_token(token: str):
    """Save API token to config file"""
    # Save to plugin root directory, one level up from core/
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    config = {'replicate_api_token': token}

    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("API token saved successfully")
    except Exception as e:
        logger.error(f"Failed to save API token: {str(e)}")

def convert_image_to_base64(image: Union[Image.Image, np.ndarray]) -> str:
    """Convert PIL Image or numpy array to base64 string"""
    # 延迟导入以避免 ComfyUI 启动阶段强依赖 torch
    try:
        import torch
    except ImportError:
        torch = None

    if torch is not None and isinstance(image, torch.Tensor):
        # ComfyUI format: [batch, height, width, channels] in range 0-1
        # Take first image from batch if batched
        if image.ndim == 4:
            image = image[0]
        image = image.detach().cpu().numpy()

    if isinstance(image, np.ndarray):
        # Convert numpy array to PIL Image
        # Handle both 0-1 float and 0-255 uint8 ranges
        if image.dtype == np.float32 or image.dtype == np.float64:
            # ComfyUI standard: float in range 0-1
            image = (np.clip(image, 0, 1) * 255).astype(np.uint8)
        elif image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)

        # Handle batch dimension (4D: [B, H, W, C])
        if image.ndim == 4:
            # Take first image from batch
            image = image[0]

        if len(image.shape) == 3 and image.shape[2] == 3:
            # RGB image
            pil_image = Image.fromarray(image, 'RGB')
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # RGBA image
            pil_image = Image.fromarray(image, 'RGBA')
        elif len(image.shape) == 2:
            # Grayscale image (2D: [H, W])
            pil_image = Image.fromarray(image, 'L')
        else:
            # Fallback: try to squeeze and convert to grayscale
            pil_image = Image.fromarray(image.squeeze(), 'L')
    else:
        pil_image = image

    # Convert to RGB if needed
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    # Resize if too large (Replicate limit is 10MB)
    max_size = 1024
    if max(pil_image.size) > max_size:
        pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Convert to base64
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"

def convert_tensor_to_image(tensor: np.ndarray) -> Image.Image:
    """Convert tensor to PIL Image"""
    if tensor.ndim == 3 and tensor.shape[0] == 3:
        # CHW format, convert to HWC
        tensor = tensor.transpose(1, 2, 0)

    if tensor.dtype != np.uint8:
        tensor = (tensor * 255).astype(np.uint8)

    return Image.fromarray(tensor)

def sanitize_inputs(inputs: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate inputs according to schema"""
    sanitized = {}

    for param_name, param_config in schema.items():
        if param_name not in inputs:
            if param_config.get('required', False):
                raise ValueError(f"Required parameter '{param_name}' is missing")
            continue

        value = inputs[param_name]
        param_type = param_config.get('type', 'string')

        try:
            if param_type == 'string':
                sanitized[param_name] = str(value)
            elif param_type == 'integer':
                sanitized[param_name] = int(value)
            elif param_type == 'number':
                sanitized[param_name] = float(value)
            elif param_type == 'boolean':
                sanitized[param_name] = bool(value)
            elif param_type == 'array':
                if isinstance(value, str):
                    # Try to parse JSON array from string
                    sanitized[param_name] = json.loads(value)
                else:
                    sanitized[param_name] = list(value)
            elif param_type == 'object':
                if isinstance(value, str):
                    sanitized[param_name] = json.loads(value)
                else:
                    sanitized[param_name] = dict(value)
            else:
                sanitized[param_name] = value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for parameter '{param_name}': {str(e)}")

    return sanitized

def format_model_display_name(owner: str, name: str, description: str = "") -> str:
    """Format model display name for UI"""
    if description:
        return f"{owner}/{name} - {description[:50]}..."
    return f"{owner}/{name}"

def extract_model_schema(version_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract input schema from model version information"""
    if 'openapi_schema' in version_info:
        return version_info['openapi_schema'].get('components', {}).get('schemas', {}).get('Input', {}).get('properties', {})
    elif 'schema' in version_info:
        return version_info['schema'].get('input', {}).get('properties', {})
    else:
        # Fallback to basic structure
        return {}

def get_parameter_type(param_config: Dict[str, Any]) -> str:
    """Determine ComfyUI parameter type from Replicate schema"""
    param_type = param_config.get('type', 'string')

    # Map Replicate types to ComfyUI types
    type_mapping = {
        'string': 'STRING',
        'integer': 'INT',
        'number': 'FLOAT',
        'boolean': 'BOOLEAN',
        'array': 'STRING',  # JSON array as string
        'object': 'STRING'  # JSON object as string
    }

    return type_mapping.get(param_type, 'STRING')

def get_parameter_options(param_config: Dict[str, Any]) -> Dict[str, Any]:
    """Get parameter options for ComfyUI"""
    options = {}

    # Add default value if available
    if 'default' in param_config:
        options['default'] = param_config['default']

    # Add min/max for numeric types
    if param_config.get('type') in ['integer', 'number']:
        if 'minimum' in param_config:
            options['min'] = param_config['minimum']
        if 'maximum' in param_config:
            options['max'] = param_config['maximum']

    # Add enum values if available
    if 'enum' in param_config:
        options['choices'] = param_config['enum']

    # Add multiline for text fields
    if param_config.get('type') == 'string' and param_config.get('format') == 'multiline':
        options['multiline'] = True

    return options

def is_image_parameter(param_config: Dict[str, Any]) -> bool:
    """Check if parameter expects an image input"""
    param_type = param_config.get('type', 'string')
    param_format = param_config.get('format', '')

    # Check for image-related formats
    image_formats = ['uri', 'image', 'file']
    image_keywords = ['image', 'picture', 'photo', 'img']

    if param_format.lower() in image_formats:
        return True

    # Check parameter name for image keywords
    param_name = param_config.get('title', '').lower()
    for keyword in image_keywords:
        if keyword in param_name:
            return True

    return False

def format_error_message(error: Union[str, Exception]) -> str:
    """Format error message for user display"""
    if isinstance(error, Exception):
        error_str = str(error)
    else:
        error_str = error

    # Remove sensitive information
    error_str = error_str.replace('Bearer', '[REDACTED]')

    # Provide user-friendly messages for common errors
    if 'Invalid API token' in error_str:
        return "Invalid Replicate API token. Please check your API key configuration."
    elif 'rate limit' in error_str.lower():
        return "API rate limit exceeded. Please wait and try again."
    elif 'network' in error_str.lower():
        return "Network error. Please check your internet connection."
    elif 'timeout' in error_str.lower():
        return "Request timed out. Please try again."
    else:
        return f"Error: {error_str}"
