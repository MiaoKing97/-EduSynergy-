import requests


class FeishuService:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id.strip() if app_id else ""
        self.app_secret = app_secret.strip() if app_secret else ""
        self.tenant_access_token = None

    def _get_tenant_access_token(self):
        """获取飞书接口调用的凭证 (Token)"""
        if not self.app_id or not self.app_secret:
            raise ValueError("【配置错误】飞书 App ID 或 App Secret 为空，请在网页右侧面板填写！")

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("code") == 0:
            self.tenant_access_token = result["tenant_access_token"]
            return self.tenant_access_token
        else:
            raise Exception(f"【身份验证失败】获取飞书 Token 失败，错误详情: {result.get('msg')}")

    def create_bitable_app(self, name: str) -> str:
        """【新增能力】从零在飞书云空间中创建一个全新的独立多维表格文件，返回生成的 app_token"""
        token = self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/bitable/v1/apps"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {"name": name}
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("code") == 0:
            # 成功提取出飞书从零生成的全新文件级别的 app_token
            return result["data"]["app"]["app_token"]
        else:
            raise Exception(f"【从零生成多维表格文件失败】: {result.get('msg')} (错误码:{result.get('code')})")

    def share_with_tenant(self, file_token: str):
        """【修复权限】：通过修改文档的“公开设置”，让所有通过链接打开的同企业/团队成员都能编辑"""
        token = self._get_tenant_access_token()
        # 注意：这里换成了 PATCH 请求，并调用了 public 接口
        url = f"https://open.feishu.cn/open-apis/drive/v1/permissions/{file_token}/public?type=bitable"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "link_share_entity": "tenant_editable"  # 核心：开启“组织内获得链接的人可编辑”
        }
        response = requests.patch(url, headers=headers, json=data)
        result = response.json()

        if result.get("code") != 0:
            print(f"====== 🚨 飞书权限修改失败 ======\n{result}")
            # 抛出异常，让它在终端暴露出来
            raise Exception(f"飞书开放平台未授权或权限失败: {result.get('msg')}")

    def create_table(self, app_token: str, table_name: str) -> str:
        """在指定的多维表格文件中，新建一张数据子表 (Table)"""
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {"table": {"name": table_name}}
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if result.get("code") == 0:
            return result["data"]["table_id"]
        else:
            raise Exception(f"创建子表失败: {result.get('msg')}")

    def add_field(self, app_token: str, table_id: str, field_name: str, field_type: int, property_dict: dict = None):
        """为特定的数据表添加字段 (列)"""
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {"field_name": field_name, "type": field_type}
        if property_dict:
            data["property"] = property_dict

        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"添加字段 '{field_name}' 失败: {result.get('msg')}")

    def get_table_records(self, app_token: str, table_id: str):
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
        response = requests.get(url, headers=headers)
        return response.json()

    def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict):
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"}
        data = {"fields": fields}
        response = requests.put(url, headers=headers, json=data)
        return response.json()

    def download_image(self, image_token: str):
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/drive/v1/medias/{image_token}/download"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"【图片下载失败】: {response.text}")

    # ... 前面的代码（create_bitable_app, create_table, add_field等）保持完全不动 ...

    def batch_create_records(self, app_token: str, table_id: str, records: list):
        """【新增能力】调用飞书 bitable batch_create 接口，一次性将全卷所有题目、答案、解析写入表格"""
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "records": records
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"批量写入题目失败: {result.get('msg')} (代码:{result.get('code')})")
        return result
# ... 保留上面原有的所有代码 ...

    def upload_bitable_image(self, app_token: str, image_bytes: bytes, file_name: str = "homework.jpg") -> str:
        """【新增能力】将图片流上传到多维表格关联的云空间中，返回关键的 file_token"""
        token = self._get_tenant_access_token()
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        headers = {
            "Authorization": f"Bearer {token}"
            # 注意：使用 requests 的 files 参数时，不要手动写 Content-Type，它会自动生成 form-data 边界
        }
        data = {
            "file_name": file_name,
            "parent_type": "bitable_image", # 声明这是给多维表格用的图片
            "parent_node": app_token,
            "size": len(image_bytes)
        }
        files = {
            "file": (file_name, image_bytes, "image/jpeg")
        }
        response = requests.post(url, headers=headers, data=data, files=files)
        result = response.json()

        if result.get("code") == 0:
            return result["data"]["file_token"]
        else:
            raise Exception(f"图片上传飞书云盘失败: {result.get('msg')} (错误码:{result.get('code')})")

    def create_record(self, app_token: str, table_id: str, fields: dict):
        """向多维表格中新增单条记录 (比如新建一行学生作业)"""
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        payload = {
            "fields": fields
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"新建表格记录失败: {result.get('msg')}")
        return result