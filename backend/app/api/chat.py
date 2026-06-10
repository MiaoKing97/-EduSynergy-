"""
Chat API: AI conversation with streaming, file upload, PDF ingestion, Feishu data context.
All routes are async with httpx for Feishu data fetching.
"""
import asyncio
import base64
import json
from typing import Optional, List

import httpx
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from ..core.prompts import SYSTEM_PROMPTS, DEFAULT_PROMPT
from ..services.file_parser import FileParserService
from ..services.llm_service import llm_service, LLMService
from ..services.rag_service import RAGService

router = APIRouter()
llm_svc: LLMService = llm_service
rag_service = RAGService()

_HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def _fetch_feishu_data(app_id: str, app_secret: str, app_token: str) -> str:
    """Fetch workspace data + dashboard stats from Feishu (shared helper)."""
    payload = {
        "feishu_app_id": app_id,
        "feishu_app_secret": app_secret,
        "app_token": app_token,
    }

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        try:
            res_workspace = await client.post(
                "http://127.0.0.1:8000/api/homework/get_workspace_data",
                json=payload, timeout=10,
            )
            res_stats = await client.post(
                "http://127.0.0.1:8000/api/homework/get_dashboard_stats",
                json=payload, timeout=10,
            )
        except Exception as e:
            print(f"[飞书多维表格实时数据拉取失败]: {str(e)}")
            return ""

    table_context = ""

    # Workspace data
    if res_workspace.status_code == 200:
        data_w = res_workspace.json()
        if data_w.get("status") == "success":
            graded_list = data_w.get("data", {}).get("graded", []) or data_w.get("graded_list", [])
            if graded_list:
                table_context += "【当前多维表格-全班学生成绩大盘档案如下】:\n"
                for student in graded_list:
                    name = student.get("student_name", "未知")
                    score = student.get("score", "未评分")
                    feedback = student.get("feedback", "无总体评语")
                    table_context += f"- 学生姓名: {name}, 综合得分: {score}分, AI评语: {feedback}\n"

    # Dashboard stats
    if res_stats.status_code == 200:
        data_s = res_stats.json()
        if data_s.get("status") == "success":
            raw_records = data_s.get("stats", {}).get("raw_records", [])
            if raw_records:
                table_context += "\n【当前多维表格-学生逐题答题流水明细如下】:\n"
                for record in raw_records[:35]:
                    table_context += f"- 学生: {record.get('student_name')}, 题号: {record.get('question_number')}, 知识点: {record.get('knowledge_point')}, 判题状态: {record.get('is_correct')}, 错因诊断: {record.get('error_cause')}\n"

    if table_context:
        print("[AI 智能中枢] 飞书数据拉取成功！已注入大模型 Prompt 上下文。")
        return (
            "你是一个深度连接了学校飞书多维表格系统的 AI 助教专家。以下是系统自动为你从当前老师选定的飞书云端表格中实时拉取出来的真实班级成绩数据。语境完全真实，请严格根据这些确凿的数据回答老师的问题，禁止伪造任何学生姓名、分数或错题！\n\n"
            f"{table_context}\n\n老师现在向你提问：{{user_message}}"
        )
    else:
        print("[AI 智能中枢] 虽然请求成功，但表格内暂无有效成绩数据。")
        return ""


@router.post("/chat")
async def chat_with_ai(
        user_message: str = Form(...),
        module_type: str = Form(...),
        api_key: str = Form(default=""),
        model_name: str = Form(default=""),
        feishu_token: str = Form(default=""),
        feishu_app_id: str = Form(default=""),
        feishu_app_secret: str = Form(default=""),
        images: Optional[List[UploadFile]] = File(default=[]),
        files: Optional[List[UploadFile]] = File(default=[]),
):
    """AI chat endpoint: handles text, images, PDFs, and tabular data uploads."""
    system_prompt = SYSTEM_PROMPTS.get(module_type, DEFAULT_PROMPT)
    user_text = user_message.strip() if user_message else "请分析。"
    user_content: list = []

    # 1. Batch image upload
    images = images or []
    for img in images:
        if img.size > 0:
            content = await img.read()
            b64_str = base64.b64encode(content).decode('utf-8')
            mime_type = img.content_type or "image/jpeg"
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_str}"},
            })

    # 2. File upload: PDF → ChromaDB ingestion, tabular → parser
    has_table = False
    files = files or []
    for doc in files:
        if doc.size > 0:
            content = await doc.read()
            if doc.filename.lower().endswith('.pdf'):
                ingest_msg = await rag_service.ingest_pdf(content, doc.filename)
                user_text += f"\n\n{ingest_msg}"
            else:
                has_table = True
                summary = await FileParserService.parse_tabular_data_async(content, doc.filename)
                user_text += summary

    if has_table:
        user_text += "\n要求：请结合上述数据写出详细报告，并严格按要求在末尾输出代码以生成图表！"

    # 3. Feishu data context injection (async)
    if feishu_token and feishu_app_id and feishu_app_secret:
        print(f"\n[AI 智能中枢] 收到前端参数 -> Token: {feishu_token}, AppID: {feishu_app_id}")
        formatted_prompt = await _fetch_feishu_data(feishu_app_id, feishu_app_secret, feishu_token)
        if formatted_prompt:
            user_text = formatted_prompt.replace("{user_message}", user_text)
        else:
            print("[AI 智能中枢] ⚠️ 未获取到有效飞书数据，跳过数据注入。")
    else:
        print("[AI 智能中枢] ⚠️ 拦截条件未满足！未检测到完整的飞书三件套 (Token/AppID/Secret)。")

    # 4. RAG retrieval
    if module_type == "rag_qa":
        retrieved_context = rag_service.retrieve_context(user_message)
        if retrieved_context:
            user_text = (
                f"你是一个校本专家。请结合以下【本地资料检索结果】来回答用户的问题。\n\n"
                f"{retrieved_context}\n\n用户问题是：{user_text}"
            )

    user_content.append({"type": "text", "text": user_text})

    return StreamingResponse(
        llm_svc.generate_stream(
            system_prompt,
            user_content,
            api_key=api_key,
            model_name=model_name or "deepseek-chat",
        ),
        media_type="text/plain",
    )
