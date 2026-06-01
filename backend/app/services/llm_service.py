import requests
import json
import os
import traceback
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        pass

    def call_doubao_vision(self, api_key: str, prompt: str, image_url_or_base64: str,
                           model_name: str = "doubao-seed-2-0-pro-260215"):
        logger.info(f"\n========================================")
        logger.info(f"🚀 正在呼叫大模型，当前使用的模型版本是: {model_name}")
        logger.info(f"========================================\n")

        # 🌟 核心修复 1：将旧的 responses 接口改为标准 OpenAI 兼容接口
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

        # 强制去除首尾不可见空格
        clean_api_key = api_key.strip() if api_key else ""
        headers = {
            "Authorization": f"Bearer {clean_api_key}",
            "Content-Type": "application/json"
        }

        img_url = image_url_or_base64 if image_url_or_base64.startswith(
            "http") else f"data:image/jpeg;base64,{image_url_or_base64}"

        # 🌟 核心修复 2：将 input_image 格式改为标准的 image_url 格式
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": img_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        logger.info(f"📡 [LLM 请求] 正在向豆包发送单图视觉分析请求, 模型: {model_name}")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info("✅ [LLM 响应] 接口返回成功")
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            return str(result)
        else:
            logger.error(f"❌ [LLM 错误] 火山接口拒绝服务: {response.text}")
            raise Exception(f"【火山接口拒绝服务】状态码: {response.status_code}, 返回详情: {response.text}")

    # 🌟 【新增功能】支持同时传入多张图片进行跨端视觉 Visual Diff 分析
    def call_doubao_vision_multi(self, api_key: str, prompt: str, images_base64: list,
                                 model_name: str = "doubao-seed-2-0-pro-260215"):
        logger.info(f"\n========================================")
        logger.info(f"🚀 正在呼叫大模型 (多图跨端对比模式): {model_name}")
        logger.info(f"========================================\n")

        # 🌟 同上：统一修改为 chat/completions 端点
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

        clean_api_key = api_key.strip() if api_key else ""
        headers = {
            "Authorization": f"Bearer {clean_api_key}",
            "Content-Type": "application/json"
        }

        content_list = []
        for img_b64 in images_base64:
            img_url = img_b64 if img_b64.startswith("http") else f"data:image/jpeg;base64,{img_b64}"
            # 🌟 同上：修改为 image_url 格式
            content_list.append({"type": "image_url", "image_url": {"url": img_url}})

        content_list.append({"type": "text", "text": prompt})

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": content_list}]
        }

        logger.info(f"📡 [LLM 请求] 正在向豆包发送多图对比视觉请求, 模型: {model_name}")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info("✅ [LLM 响应] 多模态接口返回成功")
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            return str(result)
        else:
            logger.error(f"❌ [LLM 错误] 火山接口拒绝服务: {response.text}")
            raise Exception(f"【火山接口拒绝服务】状态码: {response.status_code}, 返回详情: {response.text}")

    def call_deepseek_text(self, api_key: str, prompt: str, system_prompt: str = ""):
        url = "https://api.deepseek.com/v1/chat/completions"
        clean_api_key = api_key.strip() if api_key else ""
        headers = {
            "Authorization": f"Bearer {clean_api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.1
        }

        logger.info(f"📡 [LLM 请求] 正在向 DeepSeek 发送文本推理请求...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            logger.info("✅ [LLM 响应] 文本推理接口返回成功")
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"❌ [LLM 错误] DeepSeek API 调用失败: {response.text}")
            raise Exception(f"【DeepSeek API 调用失败】: {response.text}")

    def generate_stream(self, system_prompt: str, user_content: list, api_key: str = None,
                        model_name: str = "deepseek-chat"):
        try:
            api_key = api_key or os.getenv("API_KEY", "")
            if not api_key:
                yield "❌ 抱歉，未检测到 API Key！请先在右侧【开发者参数底盘】中填写您的模型 API Key。"
                return

            if "doubao" in model_name.lower() or "ep-" in model_name.lower():
                url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            else:
                url = "https://api.deepseek.com/v1/chat/completions"

            clean_api_key = api_key.strip() if api_key else ""
            headers = {
                "Authorization": f"Bearer {clean_api_key}",
                "Content-Type": "application/json"
            }

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
                "stream": True
            }

            logger.info(f"📡 [LLM 请求] 开启流式对话输出, 模型: {model_name}")
            with requests.post(url, headers=headers, json=payload, stream=True) as response:
                if response.status_code != 200:
                    logger.error(f"❌ [LLM 错误] 流式请求失败: {response.text}")
                    yield f"❌ 模型服务拒绝访问 (状态码: {response.status_code}):\n{response.text}"
                    return

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]

                            if data_str.strip() == "[DONE]":
                                logger.info("✅ [LLM 响应] 流式对话生成结束")
                                break

                            try:
                                data_json = json.loads(data_str)
                                if "choices" in data_json and len(data_json["choices"]) > 0:
                                    delta = data_json["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"❌ [严重错误] 后端执行异常: {str(e)}", exc_info=True)
            error_msg = f"\n\n❌ **后端执行异常**: {str(e)}\n\n```python\n{traceback.format_exc()}\n```\n"
            yield error_msg


# 实例化全局服务
llm_service = LLMService()