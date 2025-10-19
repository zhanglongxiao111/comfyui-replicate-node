"""
Replicate API Client
Handles communication with Replicate API
"""

import aiohttp
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Replicate model information"""
    owner: str
    name: str
    url: str
    description: str = ""
    visibility: str = "public"
    latest_version: Optional[Dict] = None

@dataclass
class PredictionStatus:
    """Prediction status information"""
    id: str
    status: str
    input: Dict[str, Any]
    output: Optional[Any] = None
    error: Optional[str] = None
    logs: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    urls: Optional[Dict[str, str]] = None

class ReplicateClient:
    """Asynchronous Replicate API client"""

    def __init__(self, api_token: str, base_url: str = "https://api.replicate.com/v1"):
        self.api_token = api_token
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache = {
            'models': {},
            'model_details': {},
            'cache_time': {},
            'ttl': 3600  # 1 hour cache TTL
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=300)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Replicate API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' statement.")

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status in [200, 201]:  # 200 OK, 201 Created
                    return await response.json()
                elif response.status == 401:
                    raise Exception("Invalid API token")
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    await asyncio.sleep(retry_after)
                    return await self._request(method, endpoint, **kwargs)
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache['cache_time']:
            return False
        return time.time() - self._cache['cache_time'][cache_key] < self._cache['ttl']

    async def list_models(self, search: Optional[str] = None, limit: int = 100) -> List[ModelInfo]:
        """List available models with optional search"""
        cache_key = f"models_{search}_{limit}"

        if self._is_cache_valid(cache_key):
            return self._cache['models'].get(cache_key, [])

        params = {}
        if search:
            params['search'] = search

        try:
            response = await self._request('GET', '/models', params=params)
            models = []

            for model_data in response.get('results', []):
                model = ModelInfo(
                    owner=model_data['owner'],
                    name=model_data['name'],
                    url=model_data['url'],
                    description=model_data.get('description', ''),
                    visibility=model_data.get('visibility', 'public'),
                    latest_version=model_data.get('latest_version')
                )
                models.append(model)

            # Cache results
            self._cache['models'][cache_key] = models
            self._cache['cache_time'][cache_key] = time.time()

            return models

        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            raise

    async def get_model_details(self, owner: str, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        cache_key = f"model_details_{owner}_{name}"

        if self._is_cache_valid(cache_key):
            return self._cache['model_details'].get(cache_key, {})

        try:
            response = await self._request('GET', f'/models/{owner}/{name}')

            # Cache results
            self._cache['model_details'][cache_key] = response
            self._cache['cache_time'][cache_key] = time.time()

            return response

        except Exception as e:
            logger.error(f"Failed to get model details for {owner}/{name}: {str(e)}")
            raise

    async def get_model_version(self, owner: str, name: str, version_id: str) -> Dict[str, Any]:
        """Get specific version information for a model"""
        try:
            response = await self._request('GET', f'/models/{owner}/{name}/versions/{version_id}')
            return response
        except Exception as e:
            logger.error(f"Failed to get model version {owner}/{name}@{version_id}: {str(e)}")
            raise

    async def create_prediction(self, version_id: str, inputs: Dict[str, Any],
                              webhook: Optional[str] = None) -> PredictionStatus:
        """Create a new prediction"""
        data = {
            "version": version_id,
            "input": inputs
        }

        if webhook:
            data["webhook"] = webhook

        try:
            response = await self._request('POST', '/predictions', json=data)
            return PredictionStatus(
                id=response['id'],
                status=response['status'],
                input=response['input'],
                output=response.get('output'),
                error=response.get('error'),
                logs=response.get('logs'),
                created_at=response.get('created_at'),
                completed_at=response.get('completed_at'),
                urls=response.get('urls')
            )
        except Exception as e:
            logger.error(f"Failed to create prediction: {str(e)}")
            raise

    async def get_prediction(self, prediction_id: str) -> PredictionStatus:
        """Get prediction status and results"""
        try:
            response = await self._request('GET', f'/predictions/{prediction_id}')
            return PredictionStatus(
                id=response['id'],
                status=response['status'],
                input=response['input'],
                output=response.get('output'),
                error=response.get('error'),
                logs=response.get('logs'),
                created_at=response.get('created_at'),
                completed_at=response.get('completed_at'),
                urls=response.get('urls')
            )
        except Exception as e:
            logger.error(f"Failed to get prediction {prediction_id}: {str(e)}")
            raise

    async def cancel_prediction(self, prediction_id: str) -> PredictionStatus:
        """Cancel a running prediction"""
        try:
            response = await self._request('POST', f'/predictions/{prediction_id}/cancel')
            return PredictionStatus(
                id=response['id'],
                status=response['status'],
                input=response['input'],
                output=response.get('output'),
                error=response.get('error'),
                logs=response.get('logs'),
                created_at=response.get('created_at'),
                completed_at=response.get('completed_at'),
                urls=response.get('urls')
            )
        except Exception as e:
            logger.error(f"Failed to cancel prediction {prediction_id}: {str(e)}")
            raise

    async def wait_for_prediction(self, prediction_id: str,
                                 timeout: int = 300, poll_interval: int = 2) -> PredictionStatus:
        """Wait for prediction to complete with polling"""
        start_time = time.time()

        while True:
            prediction = await self.get_prediction(prediction_id)

            if prediction.status in ['succeeded', 'failed', 'canceled']:
                return prediction

            if time.time() - start_time > timeout:
                raise TimeoutError(f"Prediction {prediction_id} timed out after {timeout} seconds")

            await asyncio.sleep(poll_interval)

    def clear_cache(self):
        """Clear all cached data"""
        self._cache = {
            'models': {},
            'model_details': {},
            'cache_time': {},
            'ttl': self._cache['ttl']
        }