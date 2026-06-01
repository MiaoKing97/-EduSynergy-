<template>
  <div class="student-view-container" :class="{'is-guest-mode': isGuest}">

    <div v-if="isGuest" class="brand-header">
      <span class="bot-icon">🤖</span> 杏坛智伴 · 作业提交中心
    </div>

    <div class="header">
      <div class="title-area">
        <h3 v-if="isWebTeacher">📤 {{ isGuest ? inviteData.tableName : '网页设计作业' }} 同步空间</h3>
        <h3 v-else>📤 {{ isGuest ? inviteData.tableName : '学生作业' }} 同步空间</h3>

        <p v-if="isWebTeacher">支持提交在线网页设计作品、本地 HTML 源码或网页静态截图。</p>
        <p v-else>请在此添加本次作业的图片，并为每张图片指定内容（如“第一大题”）。</p>
      </div>
    </div>

    <div class="upload-card">
      <div class="submitter-info">
        <template v-if="isGuest">
          <span class="label">🧑‍🎓 你的姓名：</span>
          <input type="text" v-model="guestName" placeholder="请输入你的真实姓名" class="student-name-input guest-input" />
        </template>

        <template v-else-if="isTeacher">
          <span class="label">当前操作人：</span>
          <div class="teacher-input-wrapper">
            <input type="text" v-model="customStudentName" placeholder="请输入被代交学生姓名" class="student-name-input" />
            <span class="role-tag" :class="{'web-tag': isWebTeacher}">
              {{ isWebTeacher ? '网页设计老师代交' : '老师代交模式' }}
            </span>
          </div>
        </template>
      </div>

      <div class="web-design-section" v-if="isWebTeacher">
        <div class="url-submit-area">
          <div class="area-header">
            <span class="icon">🔗</span>
            <strong>提交在线网页链接 (针对已部署的项目)</strong>
          </div>
          <div class="input-with-button">
            <input type="text" v-model="liveUrl" placeholder="输入 Vercel/GitHub Pages 等公开链接 (以 http 开头)" />
            <button class="btn-primary-green" @click="uploadUrl" :disabled="isUploading || !liveUrl.trim() || !finalSubmitterName">
              {{ isUploading ? '评测中...' : '启动多设备 UI 评测' }}
            </button>
          </div>
        </div>

        <div class="divider-text"><span>或</span></div>

        <div class="file-submit-area">
          <div class="area-header">
            <span class="icon">📂</span>
            <strong>提交本地网页源码 (针对未部署的单页面项目)</strong>
          </div>
          <div class="file-upload-box" :class="{ 'has-file': selectedFile }">
            <input type="file" id="html-upload" accept=".html,.htm" @change="handleFileChange" class="hidden-input" />
            <label for="html-upload" class="upload-label">
              <span class="upload-icon">{{ selectedFile ? '✅' : '📄' }}</span>
              <span class="upload-text">{{ selectedFile ? selectedFile.name : '点击选择 .html 源码文件' }}</span>
            </label>
            <button class="btn-primary-blue" @click="uploadHtmlFile" :disabled="isUploading || !selectedFile || !finalSubmitterName">
              {{ isUploading ? '上传中...' : '上传并启动评测' }}
            </button>
          </div>
          <p class="help-text">⚡️ 云端无头浏览器将在内存中直接渲染该源码，并提取多端快照喂给 AI 进行五维能力生成。</p>
        </div>
      </div>

      <div class="divider-text" style="margin: 16px 0;">
        <span>{{ isWebTeacher ? '或直接上传网页静态截图' : '图片上传区' }}</span>
      </div>

      <div class="image-upload-section" :class="{'web-theme': isWebTeacher}">
        <div class="upload-header">
          <button class="btn-add-image" @click="triggerFileSelect">
            <span class="icon">{{ isWebTeacher ? '📸' : '➕' }}</span>
            {{ isWebTeacher ? '上传网页高清截图 (.jpg/.png)' : '添加作业图片' }}
          </button>
          <input type="file" ref="fileInput" @change="handleAddFile" accept="image/*" multiple style="display: none;" />
        </div>

        <div class="image-preview-area" v-if="uploadQueue.length > 0">
          <div class="preview-card" v-for="(item, index) in uploadQueue" :key="index">
            <img :src="item.preview" class="preview-img" />
            <button class="btn-remove" @click="removeItem(index)">✕</button>
            <input v-model="item.name" :placeholder="isWebTeacher ? '例如: 移动端界面' : '图片命名'" class="img-name-mini" />
          </div>
        </div>
        <div class="empty-image-area" v-else>
          {{ isWebTeacher ? '暂未选择截图，系统支持直接读取截图进行 UI/UX 评价' : '暂未添加图片' }}
        </div>

        <button class="btn-submit-all" @click="uploadAll" :disabled="isUploading || uploadQueue.length === 0 || !finalSubmitterName">
          <span v-if="isUploading" class="spin">🔄</span>
          {{ isUploading ? '正在极速传输中...' : (isWebTeacher ? `🚀 确认上传 ${uploadQueue.length} 份设计截图` : `🚀 确认上传 ${uploadQueue.length} 份图片作业`) }}
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { globalStore } from '../../store';

const API_BASE_URL = 'http://localhost:8000/api/homework';

const urlParams = new URLSearchParams(window.location.search);
const inviteParam = urlParams.get('invite');
let inviteData = null;

if (inviteParam) {
  try {
    inviteData = JSON.parse(decodeURIComponent(escape(atob(inviteParam))));
  } catch(e) {
    console.error("解析专属链接失败", e);
  }
}

const isGuest = !!inviteData;
const isTeacher = computed(() => !isGuest && ['teacher', 'web_teacher'].includes(globalStore.auth.role));
const isWebTeacher = computed(() => isGuest ? inviteData.isWeb : globalStore.auth.role === 'web_teacher');

const guestName = ref('');
const customStudentName = ref('');
const finalSubmitterName = computed(() => {
  if (isGuest) return guestName.value.trim();
  return isTeacher.value ? customStudentName.value.trim() : (globalStore.auth.username || '未知');
});

const getApiCreds = () => {
  if (isGuest) {
    return { feishu_app_id: inviteData.feishuAppId, feishu_app_secret: inviteData.feishuAppSecret, app_token: inviteData.appToken };
  }
  return { feishu_app_id: globalStore.config.feishuAppId, feishu_app_secret: globalStore.config.feishuAppSecret, app_token: globalStore.config.feishuToken };
};

const isUploading = ref(false);
const liveUrl = ref('');

// ======== 1. 网址提交 ========
const uploadUrl = async () => {
  if (!finalSubmitterName.value) return alert("⚠️ 请务必输入您的姓名！");
  if (!liveUrl.value.startsWith('http')) return alert("链接请务必以 http:// 或 https:// 开头！");

  const creds = getApiCreds();
  if (!creds.app_token) return alert("配置错误：链接损坏或 Token 丢失！");

  isUploading.value = true;
  try {
    await axios.post(`${API_BASE_URL}/upload_web_design`, {
      student_name: `${finalSubmitterName.value}-UI评测`,
      live_url: liveUrl.value.trim(),
      ...creds
    });
    alert(`🎉 成功！网页链接已发往云端渲染评测。`);
    liveUrl.value = ''; guestName.value = ''; customStudentName.value = '';
  } catch (e) {
    alert("❌ 上传失败: " + (e.response?.data?.detail || e.message));
  } finally { isUploading.value = false; }
};

// ======== 2. 本地 HTML 文件提交 ========
const selectedFile = ref(null);
const handleFileChange = (e) => {
  if (e.target.files && e.target.files.length > 0) {
    const file = e.target.files[0];
    if (!file.name.endsWith('.html') && !file.name.endsWith('.htm')) {
      alert("⚠️ 请上传 .html 格式的网页源码文件！"); e.target.value = ''; return;
    }
    selectedFile.value = file;
  }
};
const uploadHtmlFile = async () => {
  if (!finalSubmitterName.value) return alert("⚠️ 请务必输入姓名！");
  if (!selectedFile.value) return alert("⚠️ 请选择 HTML 文件！");
  const creds = getApiCreds();
  if (!creds.app_token) return alert("配置错误！");

  isUploading.value = true;
  try {
    const formData = new FormData();
    formData.append('student_name', finalSubmitterName.value + '-UI评测');
    formData.append('feishu_app_id', creds.feishu_app_id);
    formData.append('feishu_app_secret', creds.feishu_app_secret);
    formData.append('app_token', creds.app_token);
    formData.append('file', selectedFile.value);

    await axios.post(`${API_BASE_URL}/upload_web_file`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    alert(`🎉 成功！本地源码已上传。`);
    selectedFile.value = null; guestName.value = ''; customStudentName.value = '';
  } catch (error) { alert(`❌ 上传失败: ${error.response?.data?.detail || error.message}`); } finally { isUploading.value = false; }
};

// ======== 3. 图片/截图 智能分流提交 ========
const fileInput = ref(null);
const uploadQueue = ref([]);

const triggerFileSelect = () => fileInput.value.click();
const handleAddFile = (event) => {
  const files = event.target.files;
  for (let file of files) {
    uploadQueue.value.push({ file: file, name: file.name.split('.')[0], preview: URL.createObjectURL(file) });
  }
  event.target.value = '';
};
const removeItem = (index) => {
  URL.revokeObjectURL(uploadQueue.value[index].preview);
  uploadQueue.value.splice(index, 1);
};
const fileToBase64 = (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader(); reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
  });
};

const uploadAll = async () => {
  if (!finalSubmitterName.value) return alert("⚠️ 请务必输入姓名！");
  const creds = getApiCreds();
  if (!creds.app_token) return alert("配置错误！");

  isUploading.value = true;
  try {
    for (const item of uploadQueue.value) {
      const base64 = await fileToBase64(item.file);

      // 🌟 核心分流逻辑：网页设计老师走专属接口触发雷达图，普通老师走老通道
      if (isWebTeacher.value) {
        await axios.post(`${API_BASE_URL}/upload_web_screenshot`, {
          student_name: `${finalSubmitterName.value}-${item.name}`,
          image_base64: base64,
          ...creds
        });
      } else {
        await axios.post(`${API_BASE_URL}/upload_student_work`, {
          student_name: `${finalSubmitterName.value}-${item.name}`,
          image_base64: base64,
          ...creds
        });
      }
    }
    alert(`🎉 成功上传 ${uploadQueue.value.length} 份文件！`);
    uploadQueue.value = []; guestName.value = ''; customStudentName.value = '';
  } catch (e) {
    alert("❌ 上传失败: " + (e.response?.data?.detail || e.message));
  } finally { isUploading.value = false; }
};
</script>

<style scoped>
.student-view-container { max-width: 700px; margin: 0 auto; padding: 20px; }
.is-guest-mode { background: #fff; border-radius: 16px; padding: 40px; box-shadow: 0 20px 40px rgba(0,0,0,0.06); margin-top: 5vh; border: 1px solid rgba(255,255,255,0.8); }
.brand-header { text-align: center; font-size: 14px; font-weight: bold; color: #1890ff; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid #f1f5f9;}
.bot-icon { font-size: 20px; vertical-align: middle; margin-right: 4px; }

.header { margin-bottom: 20px; }
.title-area h3 { margin: 0 0 6px 0; font-size: 22px; color: #1e293b; font-weight: 800; display: flex; align-items: center; gap: 8px;}
.title-area p { margin: 0; font-size: 14px; color: #64748b; }

.upload-card { background: #fff; border-radius: 12px; display: flex; flex-direction: column; gap: 20px; }
.is-guest-mode .upload-card { box-shadow: none; padding: 0; border: none; }

.submitter-info { display: flex; align-items: center; gap: 12px; background: #f8fafc; padding: 16px 20px; border-radius: 10px; border: 1px solid #e2e8f0;}
.label { color: #475569; font-size: 15px; font-weight: 600; white-space: nowrap;}
.teacher-input-wrapper { display: flex; align-items: center; gap: 12px; flex: 1; }
.student-name-input { flex: 1; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 15px; transition: 0.2s;}
.student-name-input:focus { border-color: #3b82f6; outline: none; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);}
.guest-input { background: #fff; font-weight: bold; color: #0f172a;}
.role-tag { font-size: 12px; color: #722ed1; background: #f9f0ff; padding: 4px 8px; border-radius: 6px; border: 1px solid #d3adf7; white-space: nowrap;}
.role-tag.web-tag { color: #16a34a; background: #dcfce3; border-color: #86efac; }

/* Web 专属区块样式 */
.web-design-section { background: linear-gradient(to bottom, #f0fdf4, #ffffff); border: 1.5px solid #bbf7d0; border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 16px;}
.area-header { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #166534; margin-bottom: 12px; }
.input-with-button { display: flex; gap: 10px; }
.input-with-button input { flex: 1; padding: 12px 16px; border: 1.5px solid #86efac; border-radius: 8px; outline: none; font-size: 14px; background: #fff; }
.input-with-button input:focus { border-color: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.2); }
.btn-primary-green { background: #22c55e; color: white; border: none; padding: 0 20px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s; white-space: nowrap; box-shadow: 0 4px 12px rgba(34, 197, 94, 0.2); }
.btn-primary-green:hover:not(:disabled) { background: #16a34a; transform: translateY(-1px); }
.btn-primary-green:disabled { background: #86efac; cursor: not-allowed; box-shadow: none;}

.divider-text { display: flex; align-items: center; text-align: center; color: #94a3b8; font-size: 13px; font-weight: 600; }
.divider-text::before, .divider-text::after { content: ''; flex: 1; border-bottom: 1px dashed #cbd5e1; }
.divider-text span { padding: 0 12px; }

.file-upload-box { display: flex; gap: 10px; align-items: stretch; height: 46px; }
.hidden-input { display: none; }
.upload-label { flex: 1; background: #fff; border: 1.5px dashed #93c5fd; border-radius: 8px; display: flex; align-items: center; padding: 0 16px; gap: 10px; cursor: pointer; transition: 0.2s; color: #3b82f6; font-size: 14px; font-weight: 600; }
.upload-label:hover { background: #eff6ff; border-color: #3b82f6; }
.file-upload-box.has-file .upload-label { border-style: solid; border-color: #3b82f6; background: #eff6ff; color: #1e3a8a; }
.btn-primary-blue { background: #3b82f6; color: white; border: none; padding: 0 20px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s; white-space: nowrap; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);}
.btn-primary-blue:hover:not(:disabled) { background: #2563eb; transform: translateY(-1px); }
.btn-primary-blue:disabled { background: #93c5fd; cursor: not-allowed; box-shadow: none;}
.help-text { font-size: 12px; color: #15803d; margin: 8px 0 0 0; line-height: 1.5; opacity: 0.9;}

/* 🌟 通用图片/截图 上传区 */
.image-upload-section { display: flex; flex-direction: column; gap: 16px; padding: 16px; border: 1.5px dashed #cbd5e1; border-radius: 12px; background: #f8fafc; transition: 0.3s;}
.btn-add-image { background: #eff6ff; color: #2563eb; border: 1px dashed #bfdbfe; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s; width: 100%; display: flex; justify-content: center; align-items: center; gap: 8px;}
.btn-add-image:hover { background: #dbeafe; border-color: #60a5fa; }
.empty-image-area { height: 100px; display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 14px; }
.image-preview-area { display: flex; flex-wrap: wrap; gap: 12px; background: #fff; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; }
.preview-card { position: relative; width: 100px; height: 130px; display: flex; flex-direction: column; gap: 6px; }
.preview-card img { width: 100px; height: 100px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.img-name-mini { width: 100%; padding: 4px; font-size: 11px; border: 1px solid #cbd5e1; border-radius: 4px; outline: none; text-align: center; box-sizing: border-box;}
.img-name-mini:focus { border-color: #3b82f6;}
.btn-remove { position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,0.6); color: white; border: none; width: 20px; height: 20px; border-radius: 50%; font-size: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.btn-remove:hover { background: #ef4444; }

.btn-submit-all { background: #1e293b; color: white; border: none; padding: 14px; border-radius: 8px; font-size: 15px; font-weight: 800; cursor: pointer; transition: 0.2s; margin-top: 5px; }
.btn-submit-all:hover:not(:disabled) { background: #0f172a; box-shadow: 0 6px 20px rgba(15,23,42,0.2); transform: translateY(-1px); }
.btn-submit-all:disabled { opacity: 0.6; cursor: not-allowed; }
.spin { animation: spin 1s linear infinite; display: inline-block; margin-right: 8px;}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* 🌟 Web 专属皮肤：紫罗兰科技风 */
.image-upload-section.web-theme { background: #faf5ff; border-color: #d8b4fe; }
.image-upload-section.web-theme .btn-add-image { background: #f3e8ff; color: #7e22ce; border-color: #d8b4fe; }
.image-upload-section.web-theme .btn-add-image:hover { background: #e9d5ff; border-color: #c084fc; }
.image-upload-section.web-theme .empty-image-area { color: #a855f7; }
.image-upload-section.web-theme .btn-submit-all { background: linear-gradient(135deg, #a855f7 0%, #7e22ce 100%); }
.image-upload-section.web-theme .btn-submit-all:hover:not(:disabled) { box-shadow: 0 6px 20px rgba(126,34,206,0.3); }
</style>