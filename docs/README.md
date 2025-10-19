# ComfyUI Replicate Nodes

Integration with Replicate API for AI model inference in ComfyUI.

## Features

- **Model Selection**: Browse and search Replicate models directly in ComfyUI
- **Dynamic Parameters**: Automatically generate input parameters based on model schema
- **Smart Input Handling**:
  - Text prompts with automatic detection
  - Up to 4 image inputs with automatic conversion
  - JSON parameter overrides for advanced control
  - DICT parameter overrides from other nodes
- **Async Processing**: Non-blocking prediction execution with status monitoring
- **Image Support**:
  - Full ComfyUI IMAGE type support (torch.Tensor [B,H,W,C] in 0-1 range)
  - Automatic format conversion (torch.Tensor, numpy, PIL, URLs)
  - Batch dimension handling
- **Output Processing**: Automatic download and conversion of Replicate outputs
- **Error Handling**: User-friendly error messages and detailed logging
- **Multi-level Caching**:
  - Class-level schema cache
  - Model info cache
  - API response cache with TTL

## Installation

1. Navigate to your ComfyUI `custom_nodes` directory
2. Clone or copy this repository:
   ```bash
   git clone https://github.com/your-username/comfyui-replicate-nodes.git
   # or manually copy the node folder
   ```
3. Install dependencies:
   ```bash
   cd comfyui-replicate-nodes
   pip install -r requirements.txt
   ```
4. Restart ComfyUI

## Configuration

### Getting Your Replicate API Token

1. Sign up at [Replicate](https://replicate.com)
2. Go to your account settings
3. Copy your API token

### Setting Up the Token

There are two ways to configure your API token:

#### Method 1: Using the Replicate Config Node
1. Add the "Replicate Config" node to your workflow
2. Enter your API token
3. Enable "save_token" to store it locally
4. Enable "test_connection" to verify the token works

#### Method 2: Environment Variable
Set the `REPLICATE_API_TOKEN` environment variable:
```bash
export REPLICATE_API_TOKEN=your_token_here
```

## Usage

### Basic Workflow

1. **Replicate Config**: Configure your API token (one-time setup)
2. **Replicate Model Selector**: Search and select a model
3. **Replicate Dynamic Node**: Prepare inputs based on model schema
   - Enter text prompt in `prompt_text`
   - Connect images to image input ports (primary, secondary, etc.)
   - Use `param_overrides_json` for additional parameters
4. **Replicate Prediction**: Execute the prediction
5. **Replicate Output Processor**: Process and convert outputs to ComfyUI format

### Example Workflow

1. Add a **Replicate Config** node and enter your API token
2. Add a **Replicate Model Selector** node:
   - Enter a search query like "stable diffusion" or "image generation"
   - Execute to select a model
3. Add a **Replicate Dynamic Node**:
   - Connect the model info from the selector
   - 在节点中设置 `prompt_text`、连接图片端口（`primary_image` 等）
   - 如需覆盖其他参数，填写 `param_overrides_json` 或连接 `param_overrides` 端口
   - 节点会自动输出 `schema_summary`，方便查看模型需要哪些参数
4. Add a **Replicate Prediction** node:
   - Connect the prepared inputs from the dynamic node
   - Execute to run the prediction

### Working with Images

The nodes automatically handle image conversion:
- Input images can be from other ComfyUI nodes or local files
- Images are automatically converted to the format required by Replicate
- Output images are returned in ComfyUI's tensor format

### 参数配置与覆盖

- `prompt_text`：用于输入/接收提示词，可直接在 UI 中填写或连接上游文本节点  
- `primary_image` ~ `quaternary_image`：最多支持四张图片输入，会自动匹配模型中声明的图片参数  
- `param_overrides_json`：以 JSON 形式覆盖模型其余参数，例如 `{"guidance_scale": 7.5}`  
- `param_overrides`：从其他节点传入参数字典，实现完全动态的管线配置  
- `schema_summary`：节点输出的第二个端口，描述模型期望的全部参数（类型、默认值、是否必填等），便于调试与构建自定义 UI

> JSON 覆盖与端口同时存在时，后者会覆盖前者；对于图片参数，也可以在 JSON/端口中直接传入 base64、URL 或本地路径。

### Supported Model Types

The nodes work with any Replicate model, including:
- Image generation (Stable Diffusion, DALL-E, etc.)
- Text generation (LLaMA, GPT, etc.)
- Image processing (upscaling, style transfer, etc.)
- Audio processing
- Video processing
- And more!

## Node Descriptions

### Replicate Config
- **Purpose**: Configure and test your Replicate API token
- **Inputs**: API token, save option, test connection option
- **Outputs**: Status message and success flag

### Replicate Model Selector
- **Purpose**: Search and select Replicate models
- **Inputs**: Search query, API token (optional), refresh option, limit
- **Outputs**: Model ID, name, version, and detailed information

### Replicate Dynamic Node
- **Purpose**: Generate request payloads based on Replicate model schema
- **Inputs**: Model info、model version、API token、prompt_text、最多 4 个图片端口、JSON/DICT 覆盖
- **Outputs**: `prepared_inputs`（直接传给预测节点）、`schema_summary`（供调试/自定义 UI 使用）
- **Note**: 会自动填充 schema 默认值，并允许手动或通过端口覆盖参数

### Replicate Prediction
- **Purpose**: Execute predictions on Replicate
- **Inputs**: Model version, prepared inputs, API token (optional), timeout settings
- **Outputs**: Prediction ID, status, and results (raw DICT format)

### Replicate Output Processor
- **Purpose**: Convert Replicate outputs to ComfyUI-compatible formats
- **Inputs**: Results dictionary from Prediction node
- **Outputs**:
  - `image`: Processed image as ComfyUI IMAGE type (torch.Tensor [B,H,W,C] in 0-1 range)
  - `text`: Extracted text output
  - `raw_output`: Original JSON output for debugging
- **Features**:
  - Automatically downloads images from URLs
  - Converts to ComfyUI standard format
  - Handles both single outputs and arrays
  - Extracts text from string outputs

## Troubleshooting

### Common Issues

1. **"Invalid API token" error**
   - Check that your token is correct and has no extra spaces
   - Ensure your token has the necessary permissions

2. **"Network error" or timeout**
   - Check your internet connection
   - Try increasing the timeout value in the prediction node
   - Some models may take longer to process

3. **"No models found"**
   - Try different search terms
   - Check that the model is public and available

4. **Image processing errors**
   - Ensure images are in supported formats (PNG, JPEG, etc.)
   - Check that image files are not too large (<10MB)

### Logs

Check the ComfyUI console for detailed error messages and debug information.

## Performance Tips

1. **Model Caching**: The nodes cache model information to reduce API calls
2. **Batch Processing**: Process multiple inputs in a single prediction when possible
3. **Timeout Settings**: Adjust timeout values based on model complexity
4. **API Limits**: Be mindful of Replicate's rate limits

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License.

## Support

For issues specific to these nodes, please use the GitHub issues.
For issues with Replicate API, please refer to [Replicate's documentation](https://replicate.com/docs).
