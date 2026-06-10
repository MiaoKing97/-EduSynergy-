"""
Async Feishu Bitable API client using httpx with connection pooling.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Reusable connection pool — 30s timeout per request
_POOL_TIMEOUT = httpx.Timeout(30.0, connect=10.0, read=30.0, write=10.0)
_POOL_LIMIT = 20


class FeishuService:
    """Async-compatible Feishu Bitable client."""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id.strip() if app_id else ""
        self.app_secret = app_secret.strip() if app_secret else ""
        self._token: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=_POOL_TIMEOUT, limits=httpx.Limits(max_connections=_POOL_LIMIT))

    async def _get_tenant_access_token(self) -> str:
        if not self.app_id or not self.app_secret:
            raise ValueError("【配置错误】飞书 App ID 或 App Secret 为空，请在网页右侧面板填写！")

        if self._token:
            return self._token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = await self._client.post(url, json={"app_id": self.app_id, "app_secret": self.app_secret})
        result = resp.json()

        if result.get("code") == 0:
            self._token = result["tenant_access_token"]
            return self._token
        raise Exception(f"【身份验证失败】获取飞书 Token 失败: {result.get('msg')}")

    async def create_bitable_app(self, name: str) -> str:
        token = await self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, json={"name": name})
        result = resp.json()
        if result.get("code") == 0:
            return result["data"]["app"]["app_token"]
        raise Exception(f"【从零生成多维表格文件失败】: {result.get('msg')} (错误码:{result.get('code')})")

    async def share_with_tenant(self, file_token: str):
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{file_token}/public?type=bitable"
        resp = await self._client.patch(url, headers={"Authorization": f"Bearer {token}"}, json={
            "link_share_entity": "tenant_editable"
        })
        result = resp.json()
        if result.get("code") != 0:
            logger.warning(f"飞书权限修改失败: {result.get('msg')}")
            raise Exception(f"飞书开放平台未授权或权限失败: {result.get('msg')}")

    async def create_table(self, app_token: str, table_name: str) -> str:
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, json={"table": {"name": table_name}})
        result = resp.json()
        if result.get("code") == 0:
            return result["data"]["table_id"]
        raise Exception(f"创建子表失败: {result.get('msg')}")

    async def add_field(self, app_token: str, table_id: str, field_name: str, field_type: int,
                        property_dict: dict = None):
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        data = {"field_name": field_name, "type": field_type}
        if property_dict:
            data["property"] = property_dict
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, json=data)
        result = resp.json()
        if result.get("code") != 0:
            raise Exception(f"添加字段 '{field_name}' 失败: {result.get('msg')}")

    async def get_table_records(self, app_token: str, table_id: str) -> dict:
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"page_size": 500}
        items = []

        while True:
            resp = await self._client.get(url, headers=headers, params=params)
            result = resp.json()
            if result.get("code") != 0:
                raise Exception(f"读取表格记录失败: {result.get('msg')} (代码:{result.get('code')})")

            data = result.get("data") or {}
            items.extend(data.get("items") or [])
            if not data.get("has_more"):
                return {**result, "data": {**data, "items": items}}
            params["page_token"] = data.get("page_token")

    async def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict):
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        resp = await self._client.put(url, headers={"Authorization": f"Bearer {token}"}, json={"fields": fields})
        return resp.json()

    async def download_image(self, image_token: str) -> bytes:
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{image_token}/download"
        resp = await self._client.get(url, headers={"Authorization": f"Bearer {token}"})
        if resp.status_code == 200:
            return resp.content
        raise Exception(f"【图片下载失败】: {resp.text}")

    async def batch_create_records(self, app_token: str, table_id: str, records: list):
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, json={"records": records})
        result = resp.json()
        if result.get("code") != 0:
            raise Exception(f"批量写入失败: {result.get('msg')} (代码:{result.get('code')})")
        return result

    async def upload_bitable_image(self, app_token: str, image_bytes: bytes, file_name: str = "homework.jpg") -> str:
        token = await self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        data = {
            "file_name": file_name,
            "parent_type": "bitable_image",
            "parent_node": app_token,
            "size": len(image_bytes),
        }
        files = {"file": (file_name, image_bytes, "image/jpeg")}
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, data=data, files=files)
        result = resp.json()
        if result.get("code") == 0:
            return result["data"]["file_token"]
        raise Exception(f"图片上传飞书云盘失败: {result.get('msg')} (错误码:{result.get('code')})")

    async def create_record(self, app_token: str, table_id: str, fields: dict):
        token = await self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        resp = await self._client.post(url, headers={"Authorization": f"Bearer {token}"}, json={"fields": fields})
        result = resp.json()
        if result.get("code") != 0:
            raise Exception(f"新建表格记录失败: {result.get('msg')}")
        return result

    async def close(self):
        """Cleanup httpx client."""
        await self._client.aclose()
