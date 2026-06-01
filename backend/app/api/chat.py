# backend/app/api/chat.py
import base64
import requests
import asyncio
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.core.prompts import SYSTEM_PROMPTS, DEFAULT_PROMPT
from app.services.file_parser import FileParserService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

router = APIRouter()
llm_service = LLMService()
rag_service = RAGService()


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
        files: Optional[List[UploadFile]] = File(default=[])
):
    system_prompt = SYSTEM_PROMPTS.get(module_type, DEFAULT_PROMPT)
    user_text = user_message.strip() if user_message else "请分析。"
    user_content = []

    images = images or []
    files = files or []

    # 1. 批量处理图片
    for img in images:
        if img.size > 0:
            content = await img.read()
            b64_str = base64.b64encode(content).decode('utf-8')
            mime_type = img.content_type or "image/jpeg"
            user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_str}"}})

    # 2. 批量处理文件与 PDF
    has_table = False
    for doc in files:
        if doc.size > 0:
            content = await doc.read()
            if doc.filename.lower().endswith('.pdf'):
                ingest_msg = rag_service.ingest_pdf(content, doc.filename)
                user_text += f"\n\n{ingest_msg}"
            else:
                has_table = True
                summary = FileParserService.parse_tabular_data(content, doc.filename)
                user_text += summary

    if has_table:
        user_text += "\n要求：请结合上述数据写出详细报告，并严格按要求在末尾输出代码以生成图表！"

    # 3. 🌟🌟🌟 核心穿透修复：解决 FastAPI 单线程同步请求导致的死锁问题
    print(f"\n[AI 智能中枢] 收到前端参数 -> Token: {feishu_token}, AppID: {feishu_app_id}")

    if feishu_token and feishu_app_id and feishu_app_secret:
        try:
            print("[AI 智能中枢] 正在通过异步线程穿透拉取飞书数据...")
            payload = {
                "feishu_app_id": feishu_app_id,
                "feishu_app_secret": feishu_app_secret,
                "app_token": feishu_token
            }
            table_context = ""

            # 🌟 修复关键点：使用 asyncio.to_thread 放入独立线程，防止阻塞事件循环
            res_workspace = await asyncio.to_thread(
                requests.post,
                "http://127.0.0.1:8000/api/homework/get_workspace_data",
                json=payload,
                timeout=10
            )

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

            res_stats = await asyncio.to_thread(
                requests.post,
                "http://127.0.0.1:8000/api/homework/get_dashboard_stats",
                json=payload,
                timeout=10
            )

            if res_stats.status_code == 200:
                data_s = res_stats.json()
                if data_s.get("status") == "success":
                    raw_records = data_s.get("stats", {}).get("raw_records", [])
                    if raw_records:
                        table_context += "\n【当前多维表格-学生逐题答题流水明细如下】:\n"
                        for record in raw_records[:35]:  # 截取前35条，防止超出大模型单次上下文限制
                            table_context += f"- 学生: {record.get('student_name')}, 题号: {record.get('question_number')}, 知识点: {record.get('knowledge_point')}, 判题状态: {record.get('is_correct')}, 错因诊断: {record.get('error_cause')}\n"

            if table_context:
                print("[AI 智能中枢] 飞书数据拉取成功！已注入大模型 Prompt 上下文。")
                user_text = (
                    f"你是一个深度连接了学校飞书多维表格系统的 AI 助教专家。以下是系统自动为你从当前老师选定的飞书云端表格中实时拉取出来的真实班级成绩数据。语境完全真实，请严格根据这些确凿的数据回答老师的问题，禁止伪造任何学生姓名、分数或错题！\n\n"
                    f"{table_context}\n\n"
                    f"老师现在向你提问：{user_text}"
                )
            else:
                print("[AI 智能中枢] 虽然请求成功，但表格内暂无有效成绩数据。")

        except Exception as e:
            import traceback
            print(f"[飞书多维表格实时数据穿透失败]: {str(e)}")
            traceback.print_exc()
    else:
        print("[AI 智能中枢] ⚠️ 拦截条件未满足！未检测到完整的飞书三件套 (Token/AppID/Secret)。")

    if module_type == "rag_qa":
        retrieved_context = rag_service.retrieve_context(user_message)
        if retrieved_context:
            user_text = f"你是一个校本专家。请结合以下【本地资料检索结果】来回答用户的问题。\n\n{retrieved_context}\n\n用户的问题是：{user_text}"

    user_content.append({"type": "text", "text": user_text})

    return StreamingResponse(
        llm_service.generate_stream(
            system_prompt,
            user_content,
            api_key=api_key,
            model_name=model_name or "deepseek-chat"
        ),
        media_type="text/plain"
    )