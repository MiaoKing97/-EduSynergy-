"""
Async LLM service using httpx.
Wraps Volcengine Doubao (multi-modal vision) and DeepSeek APIs.
"""
import io
import logging
from typing import AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)

# Timeout: 300s for streaming/vision (LLM can be slow), 60s for non-streaming
STREAM_TIMEOUT = 300
NON_STREAM_TIMEOUT = 60

# Endpoint configs
VOLCENGINE_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def _get_endpoint(model_name: str) -> str:
    if model_name.lower().startswith("doubao") or "ep-" in model_name:
        return VOLCENGINE_URL
    return DEEPSEEK_URL


def _make_headers(api_key: str) -> dict:
    clean = api_key.strip() if api_key else ""
    return {"Authorization": f"Bearer {clean}", "Content-Type": "application/json"}


class LLMService:
    """Async-compatible LLM calls with connection pooling."""

    def __init__(self):
        # Shared httpx client for connection reuse
        # Vision calls (multi-image) can be slow — use STREAM_TIMEOUT
        self._client = httpx.AsyncClient(timeout=STREAM_TIMEOUT)
        self._stream_client = httpx.AsyncClient(timeout=STREAM_TIMEOUT)

    async def call_doubao_vision(self, api_key: str, prompt: str, image_url_or_base64: str,
                                 model_name: str = "doubao-seed-2-0-pro-260215") -> dict:
        """Call Doubao vision API. Returns {"content": ..., "usage": {...}}."""
        img_url = image_url_or_base64 if image_url_or_base64.startswith("http") else f"data:image/jpeg;base64,{image_url_or_base64}"

        payload = {
            "model": model_name,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": img_url}},
                    {"type": "text", "text": prompt}
                ]
            }]
        }

        logger.info(f"LLM request: single-image vision, model={model_name}")
        resp = await self._client.post(VOLCENGINE_URL, headers=_make_headers(api_key), json=payload)

        if resp.status_code != 200:
            logger.error(f"LLM error: {resp.text}")
            raise Exception(f"Volcengine API error {resp.status_code}: {resp.text}")

        data = resp.json()
        usage = data.get("usage", {})
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "usage": usage}

    async def call_doubao_vision_multi(self, api_key: str, prompt: str, images_base64: list,
                                       model_name: str = "doubao-seed-2-0-pro-260215") -> dict:
        """Call Doubao vision API with multiple images."""
        content_list = []
        for img_b64 in images_base64:
            img_url = img_b64 if img_b64.startswith("http") else f"data:image/jpeg;base64,{img_b64}"
            content_list.append({"type": "image_url", "image_url": {"url": img_url}})
        content_list.append({"type": "text", "text": prompt})

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": content_list}]
        }

        logger.info(f"LLM request: multi-image, model={model_name}, images={len(images_base64)}")
        resp = await self._client.post(VOLCENGINE_URL, headers=_make_headers(api_key), json=payload)

        if resp.status_code != 200:
            logger.error(f"LLM error: {resp.text}")
            raise Exception(f"Volcengine API error {resp.status_code}: {resp.text}")

        data = resp.json()
        usage = data.get("usage", {})
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"content": content, "usage": usage}

    async def generate_stream(self, system_prompt: str, user_content: list, api_key: str = None,
                              model_name: str = "deepseek-chat") -> AsyncIterator[str]:
        """Streaming LLM response. Yields text chunks + a final metadata dict with usage."""
        try:
            api_key = api_key or ""
            if not api_key:
                yield "❌ 抱歉，未检测到 API Key！请先在右侧【开发者参数底盘】中填写您的模型 API Key。"
                return

            endpoint = _get_endpoint(model_name)
            text_prompt = ""
            for item in user_content:
                if item.get("type") == "text":
                    text_prompt += item.get("text", "") + "\n"

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": text_prompt.strip()})

            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.5,
                "stream": True,
            }

            logger.info(f"LLM streaming request: model={model_name}")

            async with httpx.AsyncClient(timeout=STREAM_TIMEOUT) as stream_client:
                async with stream_client.stream("POST", endpoint, headers=_make_headers(api_key), json=payload) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        logger.error(f"LLM streaming error: {error_text}")
                        yield f"❌ 模型服务拒绝访问 (状态码: {resp.status_code}):\n{error_text.decode()}"
                        return

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            import json
                            data_json = json.loads(data_str)
                            if "choices" in data_json and len(data_json["choices"]) > 0:
                                delta = data_json["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"LLM streaming exception: {e}", exc_info=True)
            import traceback
            yield f"\n\n❌ **后端执行异常**: {str(e)}\n\n```python\n{traceback.format_exc()}\n```\n"

    async def close(self):
        """Cleanup httpx clients."""
        await self._client.aclose()
        await self._stream_client.aclose()


# Global singleton
llm_service = LLMService()
