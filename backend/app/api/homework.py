"""
Homework API: Feishu table management, homework upload, auto-grading, dashboard stats.
All routes are async with httpx-based Feishu client.
"""
import asyncio
import base64
import io
import json
import logging
import re
import time
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from ..auth.middleware import get_current_user
from ..services.feishu_service import FeishuService
from ..services.llm_service import llm_service
from ..services.screenshot_service import capture_responsive_screenshots
from ..core.prompts import WEB_DESIGN_PROMPT

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── HTTP client for generic HTTP calls (e.g. list tables) ───
_HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


# ─── Request models ───

class CreateTableRequest(BaseModel):
    table_name: str
    feishu_app_id: str
    feishu_app_secret: str


class ExtractTemplateRequest(BaseModel):
    image_base64: str
    ai_model: str
    api_key: str


class SaveRulesRequest(BaseModel):
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str
    rules: list


class UploadHomeworkRequest(BaseModel):
    student_name: str
    image_base64: str
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str
    table_id: str = ""


class UploadWebDesignRequest(BaseModel):
    student_name: str
    live_url: str
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str


class GetWorkspaceRequest(BaseModel):
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str


class GradeHomeworkRequest(BaseModel):
    record_id: str
    ai_model: str
    api_key: str
    system_prompt: str
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str


class DashboardStatsRequest(BaseModel):
    feishu_app_id: str
    feishu_app_secret: str
    app_token: str


class ChatBIRequest(BaseModel):
    user_message: str
    data_context: str
    ai_model: str
    api_key: str


# ─── Shared helpers ───

async def _get_tables_list(client: FeishuService, app_token: str) -> list:
    """List all tables in a bitable app (cached briefly via httpx client reuse)."""
    token = await client._get_tenant_access_token()
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as http_client:
        resp = await http_client.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
    return (resp.json().get("data") or {}).get("items") or []


async def _get_or_create_submit_table(feishu_client: FeishuService, app_token: str) -> str:
    """Async helper: find or auto-create the '作业提交看板' table."""
    try:
        token = await feishu_client._get_tenant_access_token()
    except Exception:
        token = feishu_client._token  # fallback if token fetch fails
    list_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as http_client:
            tables_resp = await http_client.get(list_url, headers={"Authorization": f"Bearer {token}"})
            tables_resp.raise_for_status()
            tables = (tables_resp.json().get("data") or {}).get("items") or []
            for t in tables:
                if t.get("name") == "作业提交看板":
                    return t.get("table_id")
    except Exception as e:
        logger.warning(f"⚠️ 实时查询飞书子表列表失败: {e}")

    logger.warning("🚨 侦测到'作业提交看板'缺失，正在启动自愈程序重新创建...")
    new_table_id = await feishu_client.create_table(app_token, "作业提交看板")
    await feishu_client.add_field(app_token, new_table_id, "学生姓名", 1)
    await feishu_client.add_field(app_token, new_table_id, "作业图片", 17)
    await feishu_client.add_field(app_token, new_table_id, "网页链接", 1)
    await feishu_client.add_field(app_token, new_table_id, "网页源码", 1)
    await feishu_client.add_field(app_token, new_table_id, "提交时间", 1)
    await feishu_client.add_field(app_token, new_table_id, "状态", 3, property_dict={
        "options": [{"name": "待批改"}, {"name": "已批改"}]
    })
    return new_table_id


def _get_graded_table_id(tables: list) -> Optional[str]:
    """Extract graded table ID from a table list."""
    return next((t.get("table_id") for t in tables if t.get("name") == "批改结果表"), None)


def _image_to_base64(raw_bytes: bytes) -> str:
    """Compress image to JPEG 75% and return base64."""
    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.thumbnail((1200, 10000), Image.Resampling.LANCZOS)
    compressed_io = io.BytesIO()
    img.save(compressed_io, format='JPEG', quality=75)
    return base64.b64encode(compressed_io.getvalue()).decode('utf-8')


# ─── Routes ───

@router.post("/create_table")
async def create_feishu_table(req: CreateTableRequest):
    try:
        logger.info(f"📝 [表格操作] 正在为 {req.table_name} 创建全新的多维表格应用...")
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        generated_app_token = await feishu_client.create_bitable_app(req.table_name)

        table_id = await feishu_client.create_table(generated_app_token, "作业提交看板")
        await feishu_client.add_field(generated_app_token, table_id, "学生姓名", 1)
        await feishu_client.add_field(generated_app_token, table_id, "作业图片", 17)
        await feishu_client.add_field(generated_app_token, table_id, "网页链接", 1)
        await feishu_client.add_field(generated_app_token, table_id, "网页源码", 1)
        await feishu_client.add_field(generated_app_token, table_id, "提交时间", 1)
        await feishu_client.add_field(generated_app_token, table_id, "状态", 3, property_dict={
            "options": [{"name": "待批改"}, {"name": "已批改"}]
        })

        graded_table_id = await feishu_client.create_table(generated_app_token, "批改结果表")
        await feishu_client.add_field(generated_app_token, graded_table_id, "学生姓名", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "题号", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "题目", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "知识点", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "学生答案", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "是否正确", 1)
        await feishu_client.add_field(generated_app_token, graded_table_id, "错因", 1)

        try:
            await feishu_client.share_with_tenant(generated_app_token)
        except Exception as e:
            logger.warning(f"Share with tenant skipped: {e}")

        real_user_url = f"https://www.feishu.cn/base/{generated_app_token}?table={table_id}"
        logger.info(f"✅ [表格操作] 成功生成多维表格，Token: {generated_app_token}")
        return {
            "status": "success",
            "app_token": generated_app_token,
            "table_id": table_id,
            "url": real_user_url,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [严重错误] 创建表格失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_template")
async def extract_template(req: ExtractTemplateRequest):
    try:
        logger.info(f"🧠 [模版提取] 正在分析上传的标准试卷图片...")
        system_prompt = r"""你是一个专业的教务AI助理。请分析用户上传的试卷/标准答案图片，完整提取所有题目的结构信息。
请务必只输出一个纯粹的 JSON 数组格式，不要包含任何额外的解释文字或 markdown 标记。
【⚠️极其重要：数学公式处理规范】
1. 绝不允许使用带单反斜杠的 LaTeX 语法（如 \pi, \triangle, \frac）！
2. 请一律替换为普通文本或 Unicode 符号（如 π, △, ∠, 根号, 分数）。

JSON 数组中每个对象必须严格包含以下六个字段：
- "number": 题号 (字符串，如 "1", "2")
- "type": 题型 (字符串，如 "选择题", "填空题", "解答题")
- "score": 分值 (整数，根据常规预估，如 3 或 5)
- "answer": 标准答案 (字符串，如 "A", "B")
- "question": 题目内容 (字符串，请从图片中精准OCR识别出该题的完整题目文本与选项)
- "analysis": 题目解析 (字符串，请你作为资深老师，为这道题生成详细的解题思路、步骤和考点分析)"""

        result = await llm_service.call_doubao_vision(
            api_key=req.api_key,
            prompt=system_prompt,
            image_url_or_base64=req.image_base64,
            model_name=req.ai_model,
        )
        ai_result = result["content"]

        clean_json_str = ""
        match_array = re.search(r'\[.*\]', ai_result, re.DOTALL)
        if match_array:
            clean_json_str = match_array.group(0)
        else:
            match_obj = re.search(r'\{.*\}', ai_result, re.DOTALL)
            if match_obj:
                clean_json_str = f"[{match_obj.group(0)}]"
            else:
                raise Exception("AI 未能输出结构化对象")

        clean_json_str = clean_json_str.replace('\\', '\\\\').replace('\\\\n', '\\n').replace('\\\\"', '\\"')
        parsed_rules = json.loads(clean_json_str)
        if not isinstance(parsed_rules, list):
            parsed_rules = [parsed_rules]

        logger.info(f"✅ [模版提取] 成功提取到 {len(parsed_rules)} 个题目结构")
        return {"status": "success", "data": parsed_rules}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [模版提取失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save_template_rules")
async def save_template_rules(req: SaveRulesRequest):
    try:
        logger.info(f"💾 [同步数据] 正在保存 {len(req.rules)} 条标准模板进飞书多维表格...")
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        sub_table_id = await feishu_client.create_table(req.app_token, "标准答案题库")

        await feishu_client.add_field(req.app_token, sub_table_id, "题号", 1)
        await feishu_client.add_field(req.app_token, sub_table_id, "题目内容", 1)
        await feishu_client.add_field(req.app_token, sub_table_id, "ai答案", 1)
        await feishu_client.add_field(req.app_token, sub_table_id, "分值", 2)
        await feishu_client.add_field(req.app_token, sub_table_id, "ai题目解析", 1)

        feishu_records = [{
            "fields": {
                "题号": str(item.get("number", "")),
                "题目内容": str(item.get("question", "暂无内容")),
                "ai答案": str(item.get("answer", "")),
                "分值": int(item.get("score", 5)),
                "ai题目解析": str(item.get("analysis", "暂无解析")),
            }
        } for item in req.rules]

        await feishu_client.batch_create_records(req.app_token, sub_table_id, feishu_records)
        logger.info(f"✅ [同步数据] 模板成功保存入库")
        return {"status": "success", "message": "录入成功！"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [同步数据失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_student_work")
async def upload_student_work(req: UploadHomeworkRequest):
    try:
        logger.info(f"📤 [图片上传] 学生 {req.student_name} 正在提交作业图片...")
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)

        image_bytes = base64.b64decode(req.image_base64)
        file_name = f"{req.student_name}_作业.jpg"
        file_token = await feishu_client.upload_bitable_image(req.app_token, image_bytes, file_name)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = {
            "学生姓名": req.student_name,
            "作业图片": [{"file_token": file_token}],
            "提交时间": current_time,
            "状态": "待批改",
        }
        await feishu_client.create_record(req.app_token, active_table_id, fields)
        logger.info(f"✅ [图片上传] {req.student_name} 作业已成功存入飞书")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [图片上传失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_web_screenshot")
async def upload_web_screenshot(req: UploadHomeworkRequest):
    try:
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)

        try:
            await feishu_client.add_field(req.app_token, active_table_id, "网页链接", 1)
        except Exception:
            pass  # column might already exist

        image_bytes = base64.b64decode(req.image_base64)
        file_name = f"{req.student_name}_截图快照.jpg"
        file_token = await feishu_client.upload_bitable_image(req.app_token, image_bytes, file_name)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = {
            "学生姓名": req.student_name,
            "作业图片": [{"file_token": file_token}],
            "网页链接": "[手动上传的高清截图]",
            "提交时间": current_time,
            "状态": "待批改",
        }
        await feishu_client.create_record(req.app_token, active_table_id, fields)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [截图上传失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_web_file")
async def upload_web_file(
        student_name: str = Form(...),
        feishu_app_id: str = Form(...),
        feishu_app_secret: str = Form(...),
        app_token: str = Form(...),
        file: UploadFile = File(...),
):
    try:
        logger.info(f"📂 [文件批阅] 学生 {student_name} 正在提交本地独立网页文件: {file.filename}")
        feishu_client = FeishuService(feishu_app_id, feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, app_token)

        try:
            await feishu_client.add_field(app_token, active_table_id, "网页链接", 1)
        except Exception:
            pass
        try:
            await feishu_client.add_field(app_token, active_table_id, "网页源码", 1)
        except Exception:
            pass

        file_bytes = await file.read()
        source_code = file_bytes.decode("utf-8", errors="ignore")

        logger.info("[文件批阅] 正在调配 Playwright 对上传的独立源码执行可视化重绘截屏...")
        capture_result = await asyncio.to_thread(capture_responsive_screenshots, html_content=source_code)

        images_base64 = [capture_result["pc_snapshot"], capture_result["mobile_snapshot"]]
        image_tokens = []
        device_names = ["PC端", "移动端"]
        for idx, b64_str in enumerate(images_base64):
            img_bytes = base64.b64decode(b64_str)
            img_name = f"{student_name}_本地上传_{device_names[idx]}快照.jpg"
            file_token = await feishu_client.upload_bitable_image(app_token, img_bytes, img_name)
            image_tokens.append({"file_token": file_token})

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = {
            "学生姓名": student_name,
            "网页链接": f"本地文件: {file.filename}",
            "网页源码": source_code[:30000],
            "作业图片": image_tokens,
            "提交时间": current_time,
            "状态": "待批改",
        }
        await feishu_client.create_record(app_token, active_table_id, fields)
        logger.info(f"✅ [文件批阅] {student_name} 的独立源文件快照及代码已成功沉淀至飞书！")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [文件批阅失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_web_design")
async def upload_web_design(req: UploadWebDesignRequest):
    try:
        logger.info(f"🔗 [网页提交] 学生 {req.student_name} 正在提交 Live URL: {req.live_url}")
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)

        try:
            await feishu_client.add_field(req.app_token, active_table_id, "网页链接", 1)
        except Exception:
            pass
        try:
            await feishu_client.add_field(req.app_token, active_table_id, "网页源码", 1)
        except Exception:
            pass

        logger.info(f"[网页提交] 正在为 {req.live_url} 生成跨端快照与源码提取...")
        capture_result = await asyncio.to_thread(capture_responsive_screenshots, url=req.live_url)

        images_base64 = [capture_result["pc_snapshot"], capture_result["mobile_snapshot"]]
        source_code = capture_result.get("source_code", "")

        image_tokens = []
        device_names = ["PC端", "移动端"]
        for idx, b64_str in enumerate(images_base64):
            img_bytes = base64.b64decode(b64_str)
            file_name = f"{req.student_name}_{device_names[idx]}快照.jpg"
            file_token = await feishu_client.upload_bitable_image(req.app_token, img_bytes, file_name)
            image_tokens.append({"file_token": file_token})

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fields = {
            "学生姓名": req.student_name,
            "网页链接": req.live_url,
            "网页源码": source_code[:30000],
            "作业图片": image_tokens,
            "提交时间": current_time,
            "状态": "待批改",
        }
        await feishu_client.create_record(req.app_token, active_table_id, fields)
        logger.info(f"✅ [网页提交] {req.student_name} 的网页快照及源码已入库完成！")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [网页提交失败]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_workspace_data")
async def get_workspace_data(req: GetWorkspaceRequest):
    try:
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)

        records_resp = await feishu_client.get_table_records(req.app_token, active_table_id)
        records = (records_resp.get("data") or {}).get("items") or []

        # ── Single shared HTTP call instead of duplicating per-route ──
        token = await feishu_client._get_tenant_access_token()
        tables = await _get_tables_list(feishu_client, req.app_token)
        graded_table_id = _get_graded_table_id(tables)

        details_map = {}
        if graded_table_id:
            g_records_resp = await feishu_client.get_table_records(req.app_token, graded_table_id)
            g_records = (g_records_resp.get("data") or {}).get("items") or []

            for r in g_records:
                f = r.get("fields", {})
                s_name = f.get("学生姓名") or "未知学生"
                q_num = f.get("题号") or ""
                kp = f.get("知识点") or "-"
                is_c = f.get("是否正确") or "错误"
                err = f.get("错因") or "无"

                if s_name not in details_map:
                    details_map[s_name] = {"correct_count": 0, "total_count": 0, "lines": []}
                details_map[s_name]["total_count"] += 1
                if is_c == "正确":
                    details_map[s_name]["correct_count"] += 1

                # 截断超长文本防止 f-string 拼接异常
                q_num_s = str(q_num)[:30]
                kp_s = str(kp)[:50]
                is_c_s = str(is_c)[:20]
                err_s = str(err)[:20000]

                if q_num_s == "综合评测" or kp_s == "UI/UX设计":
                    line_text = f"🖥️ {q_num_s} (考点: {kp_s}) ➡️ 状态: {is_c_s}"
                    if err_s != "无":
                        line_text += f"\n   💡 诊断详报: {err_s}"
                else:
                    line_text = f"📝 {q_num_s} (考点: {kp_s}) ➡️ {is_c_s}"
                    if is_c_s in ["错误", "待优化"] and err_s != "无":
                        line_text += f"\n   🚨 错因: {err_s}"

                details_map[s_name]["lines"].append(line_text)

        pending_list = []
        graded_list = []

        for r in records:
            fields = r.get("fields", {})
            s_name = fields.get("学生姓名", "未知学生")

            if fields.get("状态") == "已批改":
                item_details = details_map.get(s_name, {"correct_count": 0, "total_count": 0, "lines": []})
                calc_score = int((item_details["correct_count"] / item_details["total_count"]) * 100) if item_details["total_count"] > 0 else 0
                graded_list.append({
                    "record_id": r.get("record_id"),
                    "student_name": s_name,
                    "score": calc_score,
                    "feedback": "\n\n".join(item_details["lines"]),
                })
            else:
                pending_list.append({
                    "record_id": r.get("record_id"),
                    "student_name": s_name,
                })

        return {"status": "success", "pending_list": pending_list, "graded_list": graded_list}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grade_homework")
async def grade_homework(req: GradeHomeworkRequest):
    try:
        total_start = time.time()
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)

        records_resp = await feishu_client.get_table_records(req.app_token, active_table_id)
        records = (records_resp.get("data") or {}).get("items") or []
        current_record = next((r for r in records if r.get("record_id") == req.record_id), None)

        if not current_record:
            raise Exception("未能定位到作业记录")

        old_fields = current_record.get("fields", {})
        student_name = old_fields.get("学生姓名", "未知学生")
        live_url = old_fields.get("网页链接", "")
        source_code = old_fields.get("网页源码", "")
        logger.info(f"🤖 [任务启动] 正在批阅学生: {student_name}")

        grade_records = []

        # ── Web design pipeline ──
        if live_url or source_code:
            image_attachments = old_fields.get("作业图片", [])
            images_base64 = []
            raw_images_bytes = []

            if live_url == "[手动上传的高清截图]":
                logger.info("📸 [静态评测] 拦截到静态截图，直接提取喂给大模型...")
                for att in image_attachments:
                    raw_images_bytes.append(await feishu_client.download_image(att["file_token"]))

            elif len(image_attachments) >= 2:
                logger.info(f"📸 [数据调取] 快照资源就绪，直接命中复用链路...")
                for att in image_attachments[:2]:
                    raw_images_bytes.append(await feishu_client.download_image(att["file_token"]))

            else:
                logger.info(f"📸 [补缺重绘] 飞书缺失快照缓存，正在动态调度 Playwright 重构全图...")
                if live_url and live_url.startswith("http"):
                    capture_result = await asyncio.to_thread(capture_responsive_screenshots, url=live_url)
                elif source_code:
                    capture_result = await asyncio.to_thread(capture_responsive_screenshots, html_content=source_code)
                else:
                    raise Exception("该记录既非静态截图，也没有有效网址和源码，无法生成快照！")

                b64_list = [capture_result["pc_snapshot"], capture_result["mobile_snapshot"]]
                if not source_code:
                    source_code = capture_result.get("source_code", "")
                for b64 in b64_list:
                    raw_images_bytes.append(base64.b64decode(b64))

            # Compress & base64
            for raw_bytes in raw_images_bytes:
                images_base64.append(_image_to_base64(raw_bytes))

            source_context = f"\n\n【核心参考源码 (脱水净化版)】：请结合上方截图与以下实际 DOM 结构进行语义化与代码规范维度评分！\n```html\n{source_code[:8000] if source_code else ''}\n```\n"

            json_format_req = """

【⚠️ 强制文本排版与系统兼容性要求】
为了让前端页面能够完美渲染卡片，你在编写长篇文字评价时，**必须且只能**严格按照以下四个固定模块输出（请严格保留【】符号，禁止使用其他 Markdown 标题符号如 ##）：

【综合评价】
（在此处填写总体评价...）
【现有优点】
（在此处填写亮点和优点...）
【现存缺陷】
（在此处填写缺陷和不足...）
【改进建议】
（在此处填写具体的修改建议...）

在输出完上述文本后，**必须在文本的最末尾**输出一个极其严格的 JSON 数组（必须用 ```json_array 和 ``` 包裹），供底层系统记录错题使用：
```json_array
[
  {
    "question_number": "综合评测",
    "question": "网页多设备响应式与体验设计",
    "knowledge_point": "UI/UX设计",
    "student_answer": "网页源码解析",
    "is_correct": "待优化",
    "error_cause": "暂存"
  }
]
```"""
            final_prompt = WEB_DESIGN_PROMPT + source_context + json_format_req

            result = await llm_service.call_doubao_vision_multi(
                req.api_key, final_prompt, images_base64, req.ai_model
            )
            ai_result = result["content"]

            match_array = re.search(r'```json_array\s*(\[.*?\])\s*```', ai_result, re.DOTALL)
            if match_array:
                grade_records = json.loads(
                    match_array.group(1).replace('\\', '\\\\').replace('\\\\n', '\\n').replace('\\\\"', '\\"'))
            else:
                grade_records = [{
                    "question_number": "综合评测",
                    "question": "网页多设备响应式",
                    "knowledge_point": "UI/UX设计",
                    "student_answer": "本地源码",
                    "is_correct": "待优化",
                    "error_cause": "暂存",
                }]

            if grade_records:
                grade_records[0]["error_cause"] = ai_result

        # ── Normal paper grading ──
        else:
            image_attachments = old_fields.get("作业图片", [])
            if not image_attachments:
                raise Exception("未找到作业图片和网页链接，无法批改！")

            file_token = image_attachments[0]["file_token"]
            raw_image_bytes = await feishu_client.download_image(file_token)
            image_base64 = _image_to_base64(raw_image_bytes)

            json_format_req = """

【⚠️ 强制输出格式要求】
请仔细批阅图片中该学生的作业，逐题诊断学生的作答情况。
请务必只输出一个纯粹的 JSON 数组格式（绝不要有任何 markdown 标记，严禁出现单反斜杠）。
JSON 数组中的每个对象必须严格包含以下六个字段：
- "question_number": 题号 (字符串，例如 "第1题"、"第2题" 等。若无明确题号请按顺序生成)
- "question": 题目 (字符串，摘录部分题干核心内容)
- "knowledge_point": 知识点 (字符串，该题考察的核心知识点)
- "student_answer": 学生答案 (字符串，由你从学生作业中精准识别出的结果)
- "is_correct": 是否正确 (字符串，只能填 "正确" 或 "错误")
- "error_cause": 错因 (字符串，如果做错，请一针见血指出错因；全对填 "无")"""
            final_prompt = req.system_prompt + json_format_req

            result = await llm_service.call_doubao_vision(
                req.api_key, final_prompt, image_base64, req.ai_model
            )
            ai_result = result["content"]

            clean_json_str = ""
            match_obj = re.search(r'\[.*\]', ai_result, re.DOTALL)
            if match_obj:
                clean_json_str = match_obj.group(0)
            else:
                match_single = re.search(r'\{.*\}', ai_result, re.DOTALL)
                if match_single:
                    clean_json_str = f"[{match_single.group(0)}]"
                else:
                    raise Exception("AI 未能输出规范的 JSON 数组")

            grade_records = json.loads(
                clean_json_str.replace('\\', '\\\\').replace('\\\\n', '\\n').replace('\\\\"', '\\"'))
            if not isinstance(grade_records, list):
                grade_records = [grade_records]

        # ── Write results to Feishu (shared logic) ──
        tables = await _get_tables_list(feishu_client, req.app_token)
        graded_table_id = _get_graded_table_id(tables)
        if not graded_table_id:
            graded_table_id = await feishu_client.create_table(req.app_token, "批改结果表")
            await feishu_client.add_field(req.app_token, graded_table_id, "学生姓名", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "题号", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "题目", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "知识点", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "学生答案", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "是否正确", 1)
            await feishu_client.add_field(req.app_token, graded_table_id, "错因", 1)

        feishu_records = [{
            "fields": {
                "学生姓名": student_name,
                "题号": str(item.get("question_number", "未知")),
                "题目": str(item.get("question", "未知")),
                "知识点": str(item.get("knowledge_point", "")),
                "学生答案": str(item.get("student_answer", "")),
                "是否正确": str(item.get("is_correct", "错误")),
                "错因": str(item.get("error_cause", "无")),
            }
        } for item in grade_records]

        await feishu_client.batch_create_records(req.app_token, graded_table_id, feishu_records)
        await feishu_client.update_record(req.app_token, active_table_id, req.record_id, {"状态": "已批改"})

        logger.info(f"✅ [任务完成] [{student_name}] 批改全流程总耗时: {time.time() - total_start:.2f} 秒")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [严重错误] 批改流程异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_dashboard_stats")
async def get_dashboard_stats(req: DashboardStatsRequest):
    try:
        feishu_client = FeishuService(req.feishu_app_id, req.feishu_app_secret)
        try:
            active_table_id = await _get_or_create_submit_table(feishu_client, req.app_token)
        except Exception as e:
            logger.warning(f"⚠️ [学情看板] 无法创建/查询看板（飞书鉴权可能未配置）: {e}")
            return {"status": "success", "stats": {
                "total_submissions": 0,
                "pending_count": 0,
                "graded_count": 0,
                "overall_correct_rate": 0,
                "kp_mastery": [],
                "common_errors": [],
                "raw_records": [],
            }}

        submit_records_resp = await feishu_client.get_table_records(req.app_token, active_table_id)
        submit_records = (submit_records_resp.get("data") or {}).get("items") or []

        total_submissions = len(submit_records)
        pending_count = len([r for r in submit_records if r.get("fields", {}).get("状态") == "待批改"])
        graded_count = len([r for r in submit_records if r.get("fields", {}).get("状态") == "已批改"])

        tables = await _get_tables_list(feishu_client, req.app_token)
        graded_table_id = _get_graded_table_id(tables)

        kp_mastery, common_errors, raw_records = [], [], []

        if graded_table_id:
            g_records_resp = await feishu_client.get_table_records(req.app_token, graded_table_id)
            g_records = (g_records_resp.get("data") or {}).get("items") or []
            kp_buckets, error_buckets, total_items, total_correct = {}, {}, 0, 0
            raw_records = []

            for r in g_records:
                fields = r.get("fields", {})
                kp = fields.get("知识点", "未归类") or "未归类"
                is_correct = fields.get("是否正确", "错误") or "错误"
                error_cause = fields.get("错因", "无") or "无"
                student_name_val = fields.get("学生姓名", "未知") or "未知"

                # 跳过异常数据，防止单条坏数据拖垮整个接口
                if not student_name_val or not kp:
                    continue

                raw_records.append({
                    "id": r.get("record_id"),
                    "student_name": str(student_name_val)[:50],
                    "question_number": str(fields.get("题号", "未知"))[:50],
                    "question": str(fields.get("题目", "未知"))[:200],
                    "knowledge_point": str(kp)[:50],
                    "student_answer": str(fields.get("学生答案", "未作答"))[:200],
                    "is_correct": str(is_correct)[:20],
                    "error_cause": str(error_cause),
                })
                total_items += 1
                if is_correct == "正确":
                    total_correct += 1
                if kp not in kp_buckets:
                    kp_buckets[kp] = {"total": 0, "correct": 0}
                kp_buckets[kp]["total"] += 1
                if is_correct == "正确":
                    kp_buckets[kp]["correct"] += 1
                if is_correct in ["错误", "待优化"] and error_cause != "无":
                    error_buckets[error_cause] = error_buckets.get(error_cause, 0) + 1

            for kp_name, bucket in kp_buckets.items():
                rate = int((bucket["correct"] / bucket["total"]) * 100) if bucket["total"] > 0 else 0
                kp_mastery.append({"knowledge_point": kp_name, "rate": rate, "count": bucket["total"]})
            kp_mastery.sort(key=lambda x: x["rate"])

            for err_text, count in error_buckets.items():
                common_errors.append({"cause": err_text, "count": count})
            common_errors.sort(key=lambda x: x["count"], reverse=True)

        overall_correct_rate = int((total_correct / total_items) * 100) if total_items > 0 else 0

        return {"status": "success", "stats": {
            "total_submissions": total_submissions,
            "pending_count": pending_count,
            "graded_count": graded_count,
            "overall_correct_rate": overall_correct_rate,
            "kp_mastery": kp_mastery,
            "common_errors": common_errors[:6],
            "raw_records": raw_records,
        }}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [dashboard_stats 异常]: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat_with_data")
async def chat_with_data(req: ChatBIRequest):
    """ChatBI: data-aware conversational agent (non-streaming for structured analysis)."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=req.api_key, base_url="https://ark.cn-beijing.volces.com/api/v3")

        system_prompt = f"""你是一个高级教务数据分析 AI 助手。
以下是当前班级最新的飞书学情脱水数据（JSON格式）：
{req.data_context}

【你的工作规范】：
1. 根据上述数据准确回答老师的问题，切勿捏造数据。
2. 如果老师查询某些特定学生（如不及格名单、某维度得分低的人），请务必使用 Markdown 表格的形式输出查询结果。
3. 表格必须包含合理的列名（如：学生姓名、综合得分、薄弱项等）。
4. 语气要保持专业、高效、有同理心，扮演一位资深教务助理。
5. 不要在回答中暴露你看到了 JSON 数据，直接自然地给出分析结果。"""

        response = await client.chat.completions.create(
            model=req.ai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.user_message},
            ],
            temperature=0.1,
            stream=False,
        )

        return {"status": "success", "reply": response.choices[0].message.content}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
