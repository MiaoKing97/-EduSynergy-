<template>
  <div class="student-app" :class="{'is-guest-mode': isGuest}">
    <!-- 顶部品牌带（仅访客模式）-->
    <div v-if="isGuest" class="brand-bar">
      <div class="brand-logo-wrap">
        <span class="brand-logo">杏</span>
      </div>
      <div class="brand-text">
        <strong>杏坛智伴</strong>
        <small>作业提交中心</small>
      </div>
    </div>

    <!-- 主卡 -->
    <main class="card-stack">
      <!-- ① 身份卡片 -->
      <section class="step-card" :class="{ done: !!finalSubmitterName }">
        <div class="step-head">
          <span class="step-no" :class="{ done: !!finalSubmitterName }">{{ finalSubmitterName ? '✓' : '1' }}</span>
          <div>
            <h3>{{ isWebTeacher ? '🎨 网页设计作业' : '📓 作业提交' }}</h3>
            <p>{{ headerSub }}</p>
          </div>
        </div>
        <div class="name-input-row">
          <template v-if="isGuest">
            <input
              type="text" v-model="guestName"
              class="big-input" placeholder="请输入你的真实姓名"
              autocomplete="name"
            />
          </template>
          <template v-else-if="isTeacher">
            <input
              type="text" v-model="customStudentName"
              class="big-input" placeholder="请输入被代交学生姓名"
            />
            <span class="role-chip" :class="{ web: isWebTeacher }">
              {{ isWebTeacher ? '🎨 网页设计代交' : '👨‍🏫 老师代交' }}
            </span>
          </template>
          <template v-else>
            <div class="auto-name">
              <span class="auto-name-icon">🧑‍🎓</span>
              <strong>{{ globalStore.auth.username || '未登录' }}</strong>
              <span class="auto-name-tag">已自动识别</span>
            </div>
          </template>
        </div>
      </section>

      <!-- ② 上传通道：网页老师有 3 个 / 普通只 1 个 -->
      <section v-if="isWebTeacher" class="channel-tabs">
        <button
          v-for="ch in webChannels" :key="ch.key"
          class="channel-tab" :class="{ active: activeChannel === ch.key }"
          @click="activeChannel = ch.key"
        >
          <span class="channel-icon">{{ ch.icon }}</span>
          <div class="channel-text">
            <strong>{{ ch.label }}</strong>
            <small>{{ ch.desc }}</small>
          </div>
        </button>
      </section>

      <!-- ②a 在线链接（网页老师） -->
      <section v-if="isWebTeacher && activeChannel === 'url'" class="step-card upload-card">
        <div class="step-head">
          <span class="step-no">2</span>
          <div>
            <h3>提交在线网页链接</h3>
            <p>支持 Vercel / GitHub Pages 等公开 HTTPS 部署，云端将自动多设备评测</p>
          </div>
        </div>
        <div class="url-input-row">
          <input
            v-model="liveUrl" type="text" class="big-input"
            placeholder="https://your-project.vercel.app"
            @keydown.enter="uploadUrl"
          />
          <button class="big-btn primary" @click="uploadUrl" :disabled="!canSubmitUrl || isUploading">
            <span v-if="isUploading">🔄 评测中…</span>
            <span v-else>🚀 启动多端评测</span>
          </button>
        </div>
      </section>

      <!-- ②b HTML 文件（网页老师） -->
      <section v-if="isWebTeacher && activeChannel === 'html'" class="step-card upload-card">
        <div class="step-head">
          <span class="step-no">2</span>
          <div>
            <h3>提交本地网页源码</h3>
            <p>云端无头浏览器将直接渲染源码并多设备截图</p>
          </div>
        </div>
        <div
          class="drop-zone"
          :class="{ 'has-file': !!selectedFile, 'is-dragover': isDragOver }"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @drop.prevent="handleHtmlDrop"
        >
          <input
            type="file" id="html-upload" accept=".html,.htm"
            @change="handleHtmlChange" class="hidden-input"
          />
          <label for="html-upload" class="drop-label">
            <span class="drop-icon">{{ selectedFile ? '✅' : '📄' }}</span>
            <strong>{{ selectedFile ? selectedFile.name : '点击或拖拽 .html 文件到这里' }}</strong>
            <small v-if="selectedFile">{{ formatSize(selectedFile.size) }}</small>
            <small v-else>支持 .html / .htm，单个文件 ≤ 10MB</small>
          </label>
        </div>
        <button class="big-btn primary full" @click="uploadHtmlFile" :disabled="!canSubmitHtml || isUploading">
          <span v-if="isUploading">🔄 上传中…</span>
          <span v-else>🚀 上传并启动评测</span>
        </button>
      </section>

      <!-- ②c / 普通老师：图片上传通道 -->
      <section v-if="!isWebTeacher || activeChannel === 'image'" class="step-card upload-card">
        <div class="step-head">
          <span class="step-no">2</span>
          <div>
            <h3>{{ isWebTeacher ? '上传网页截图' : '上传作业图片' }}</h3>
            <p>支持拖拽 / 多选；自动生成预览，可逐张命名后一键上传</p>
          </div>
        </div>

        <div
          class="drop-zone img-drop"
          :class="{ 'is-dragover': isDragOver, 'has-items': uploadQueue.length > 0 }"
          @dragover.prevent="isDragOver = true"
          @dragleave.prevent="isDragOver = false"
          @drop.prevent="handleImageDrop"
          @click="triggerFileSelect"
        >
          <input
            type="file" ref="fileInput" multiple accept="image/*"
            @change="handleAddFile" class="hidden-input"
          />
          <div v-if="uploadQueue.length === 0" class="drop-label">
            <span class="drop-icon">{{ isWebTeacher ? '🖼️' : '📸' }}</span>
            <strong>点击选择 · 或拖拽图片到这里</strong>
            <small>支持 JPG / PNG / WEBP · 可一次选多张</small>
          </div>
          <div v-else class="preview-grid" @click.stop>
            <div v-for="(item, idx) in uploadQueue" :key="item.id" class="preview-tile">
              <img :src="item.preview" :alt="item.name" />
              <button class="tile-remove" @click="removeItem(idx)" title="移除">✕</button>
              <input
                v-model="item.name" type="text"
                :placeholder="isWebTeacher ? '例：移动端首页' : '例：第一大题'"
                class="tile-name"
              />
              <div v-if="item.progress > 0" class="tile-progress">
                <div class="bar" :style="{ width: item.progress + '%' }"></div>
                <span>{{ item.progress }}%</span>
              </div>
              <div class="tile-size">{{ formatSize(item.file.size) }}</div>
            </div>
            <button class="add-more" @click.stop="triggerFileSelect">
              <span>＋</span><small>继续添加</small>
            </button>
          </div>
        </div>

        <button class="big-btn primary full" @click="uploadAll" :disabled="!canSubmitImages || isUploading">
          <span v-if="isUploading">🔄 上传中… ({{ uploadProgressOverall }}%)</span>
          <span v-else>🚀 确认上传 {{ uploadQueue.length }} 份{{ isWebTeacher ? '截图' : '图片' }}</span>
        </button>
      </section>

      <!-- ③ 提交记录 -->
      <section v-if="submitHistory.length > 0" class="step-card history-card">
        <div class="step-head">
          <span class="step-no done">✓</span>
          <div>
            <h3>本次会话提交记录</h3>
            <p>请截图保留以下编号，若老师查询，可直接报上</p>
          </div>
        </div>
        <div class="history-list">
          <div v-for="(rec, i) in submitHistory" :key="i" class="history-row" :class="rec.kind">
            <span class="history-icon">{{ rec.kind === 'fail' ? '❌' : '✅' }}</span>
            <div class="history-meta">
              <strong>{{ rec.name }}</strong>
              <small>{{ rec.time }} · {{ rec.detail }}</small>
            </div>
            <code class="history-no">#{{ rec.no }}</code>
          </div>
        </div>
      </section>
    </main>

    <!-- 成功动画浮层 -->
    <transition name="celebrate">
      <div v-if="showSuccess" class="celebrate-overlay" @click="showSuccess = false">
        <div class="celebrate-card">
          <div class="check-circle">
            <svg viewBox="0 0 52 52" class="check-svg">
              <circle cx="26" cy="26" r="25" fill="none" stroke="#10b981" stroke-width="3"/>
              <path fill="none" stroke="#10b981" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" d="M14 27 l8 8 l16 -18"/>
            </svg>
          </div>
          <h3>{{ successTitle }}</h3>
          <p>{{ successDesc }}</p>
          <code class="success-no">提交编号 #{{ successNo }}</code>
          <button class="big-btn primary" @click="showSuccess = false">我知道了</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { globalStore } from '../../store';

const API = '/api/homework';

// ─── 邀请链接解析 ───
const urlParams = new URLSearchParams(window.location.search);
const inviteParam = urlParams.get('invite');
let inviteData = null;
if (inviteParam) {
  try { inviteData = JSON.parse(decodeURIComponent(escape(atob(inviteParam)))); }
  catch (e) { console.error('解析专属链接失败', e); }
}

const isGuest = !!inviteData;
const isTeacher = computed(() => !isGuest && ['teacher', 'web_teacher'].includes(globalStore.auth.role));
const isWebTeacher = computed(() => isGuest ? inviteData.isWeb : globalStore.auth.role === 'web_teacher');

const guestName = ref('');
const customStudentName = ref('');
const finalSubmitterName = computed(() => {
  if (isGuest) return guestName.value.trim();
  if (isTeacher.value) return customStudentName.value.trim();
  return globalStore.auth.username || '';
});

const headerSub = computed(() => {
  if (isGuest) return `${inviteData.tableName || '专属作业'}  ·  请填写姓名后上传`;
  if (isWebTeacher.value) return '支持在线链接 / 本地源码 / 网页截图三种提交方式';
  return '请上传清晰的作业图片，每张都可单独命名';
});

const getApiCreds = () => {
  if (isGuest) return { feishu_app_id: inviteData.feishuAppId, feishu_app_secret: inviteData.feishuAppSecret, app_token: inviteData.appToken };
  return { feishu_app_id: globalStore.config.feishuAppId, feishu_app_secret: globalStore.config.feishuAppSecret, app_token: globalStore.config.feishuToken };
};

// ─── 通道切换（网页老师） ───
const webChannels = [
  { key: 'url',   icon: '🔗',  label: '在线链接',   desc: '已部署 Vercel / GitHub Pages' },
  { key: 'html',  icon: '📂',  label: '本地源码',   desc: '单页 .html / .htm 文件' },
  { key: 'image', icon: '📸',  label: '网页截图',   desc: '直接上传成品图，多张同时' },
];
const activeChannel = ref('url');

// ─── 共享状态 ───
const isUploading = ref(false);
const isDragOver = ref(false);
const showSuccess = ref(false);
const successTitle = ref('');
const successDesc = ref('');
const successNo = ref('');

const submitHistory = ref([]);
const genSubmitNo = () => {
  const t = new Date();
  const stamp = `${String(t.getMonth() + 1).padStart(2, '0')}${String(t.getDate()).padStart(2, '0')}${String(t.getHours()).padStart(2, '0')}${String(t.getMinutes()).padStart(2, '0')}`;
  const rnd = Math.random().toString(36).slice(2, 5).toUpperCase();
  return `${stamp}-${rnd}`;
};

const formatSize = (bytes) => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
};

const pushHistory = (record) => {
  submitHistory.value.unshift({ ...record, time: new Date().toLocaleTimeString() });
};

const fireSuccess = (title, desc, no) => {
  successTitle.value = title; successDesc.value = desc; successNo.value = no;
  showSuccess.value = true;
  setTimeout(() => { showSuccess.value = false; }, 6000);
};

// ─── ① URL 提交 ───
const liveUrl = ref('');
const canSubmitUrl = computed(() => finalSubmitterName.value && liveUrl.value.trim().startsWith('http'));

const uploadUrl = async () => {
  if (!canSubmitUrl.value) {
    if (!finalSubmitterName.value) return alert('⚠️ 请先填写姓名');
    return alert('链接需以 http:// 或 https:// 开头');
  }
  const creds = getApiCreds();
  if (!creds.app_token) return alert('配置错误：链接损坏或 Token 丢失');
  const no = genSubmitNo();
  isUploading.value = true;
  try {
    await axios.post(`${API}/upload_web_design`, {
      student_name: `${finalSubmitterName.value}-UI评测`,
      live_url: liveUrl.value.trim(),
      ...creds,
    });
    pushHistory({ kind: 'ok', name: finalSubmitterName.value, detail: `在线链接：${liveUrl.value.trim()}`, no });
    fireSuccess('🎉 链接已成功送达评测引擎', '云端正在多设备渲染并截图，几分钟后老师即可在大屏看到结果', no);
    liveUrl.value = '';
  } catch (e) {
    pushHistory({ kind: 'fail', name: finalSubmitterName.value, detail: e.response?.data?.detail || e.message, no });
    alert('❌ 提交失败：' + (e.response?.data?.detail || e.message));
  } finally { isUploading.value = false; }
};

// ─── ② HTML 文件提交 ───
const selectedFile = ref(null);
const canSubmitHtml = computed(() => finalSubmitterName.value && !!selectedFile.value);

const acceptHtmlFile = (file) => {
  if (!file) return;
  if (!file.name.match(/\.(html|htm)$/i)) return alert('⚠️ 请上传 .html / .htm 文件');
  if (file.size > 10 * 1024 * 1024) return alert('⚠️ 文件大小超过 10 MB，请压缩后再上传');
  selectedFile.value = file;
};

const handleHtmlChange = (e) => acceptHtmlFile(e.target.files?.[0]);
const handleHtmlDrop = (e) => { isDragOver.value = false; acceptHtmlFile(e.dataTransfer?.files?.[0]); };

const uploadHtmlFile = async () => {
  if (!canSubmitHtml.value) return alert(finalSubmitterName.value ? '⚠️ 请选择 .html 文件' : '⚠️ 请先填写姓名');
  const creds = getApiCreds();
  if (!creds.app_token) return alert('配置错误');
  const no = genSubmitNo();
  isUploading.value = true;
  try {
    const fd = new FormData();
    fd.append('student_name', finalSubmitterName.value + '-UI评测');
    fd.append('feishu_app_id', creds.feishu_app_id);
    fd.append('feishu_app_secret', creds.feishu_app_secret);
    fd.append('app_token', creds.app_token);
    fd.append('file', selectedFile.value);
    await axios.post(`${API}/upload_web_file`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
    pushHistory({ kind: 'ok', name: finalSubmitterName.value, detail: `源码：${selectedFile.value.name} · ${formatSize(selectedFile.value.size)}`, no });
    fireSuccess('🎉 源码已上传', '云端无头浏览器正在渲染并截图，请稍候', no);
    selectedFile.value = null;
  } catch (e) {
    pushHistory({ kind: 'fail', name: finalSubmitterName.value, detail: e.response?.data?.detail || e.message, no });
    alert('❌ 上传失败：' + (e.response?.data?.detail || e.message));
  } finally { isUploading.value = false; }
};

// ─── ③ 图片上传（多图 + 拖拽 + 进度） ───
const fileInput = ref(null);
const uploadQueue = ref([]);
let nextId = 1;

const triggerFileSelect = () => fileInput.value?.click();

const acceptImageFiles = (files) => {
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue;
    uploadQueue.value.push({
      id: nextId++,
      file,
      name: file.name.replace(/\.[^.]+$/, ''),
      preview: URL.createObjectURL(file),
      progress: 0,
    });
  }
};
const handleAddFile = (e) => { acceptImageFiles(e.target.files); e.target.value = ''; };
const handleImageDrop = (e) => { isDragOver.value = false; acceptImageFiles(e.dataTransfer?.files || []); };

const removeItem = (idx) => {
  URL.revokeObjectURL(uploadQueue.value[idx].preview);
  uploadQueue.value.splice(idx, 1);
};

const canSubmitImages = computed(() => finalSubmitterName.value && uploadQueue.value.length > 0);

const uploadProgressOverall = computed(() => {
  if (uploadQueue.value.length === 0) return 0;
  const sum = uploadQueue.value.reduce((a, b) => a + (b.progress || 0), 0);
  return Math.round(sum / uploadQueue.value.length);
});

const fileToBase64 = (file) => new Promise((resolve) => {
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => resolve(reader.result.split(',')[1]);
});

const uploadAll = async () => {
  if (!canSubmitImages.value) return alert(finalSubmitterName.value ? '⚠️ 请先添加图片' : '⚠️ 请先填写姓名');
  const creds = getApiCreds();
  if (!creds.app_token) return alert('配置错误');
  const no = genSubmitNo();
  isUploading.value = true;
  const total = uploadQueue.value.length;
  let okCount = 0;
  try {
    for (const item of uploadQueue.value) {
      item.progress = 5;
      const base64 = await fileToBase64(item.file);
      item.progress = 35;
      try {
        if (isWebTeacher.value) {
          await axios.post(`${API}/upload_web_screenshot`, {
            student_name: `${finalSubmitterName.value}-${item.name}`,
            image_base64: base64, ...creds,
          }, {
            onUploadProgress: (e) => {
              item.progress = 35 + Math.round((e.loaded / (e.total || e.loaded)) * 60);
            }
          });
        } else {
          await axios.post(`${API}/upload_student_work`, {
            student_name: `${finalSubmitterName.value}-${item.name}`,
            image_base64: base64, ...creds,
          }, {
            onUploadProgress: (e) => {
              item.progress = 35 + Math.round((e.loaded / (e.total || e.loaded)) * 60);
            }
          });
        }
        item.progress = 100;
        okCount++;
      } catch (err) {
        item.progress = 0;
        console.error('上传单张失败', err);
      }
    }
    pushHistory({
      kind: okCount === total ? 'ok' : 'fail',
      name: finalSubmitterName.value,
      detail: `图片 ${okCount}/${total} 成功`,
      no,
    });
    if (okCount === total) {
      fireSuccess(`🎉 ${okCount} 张图片提交成功`, '老师将看到带预览的提交记录', no);
      uploadQueue.value.forEach(i => URL.revokeObjectURL(i.preview));
      uploadQueue.value = [];
    } else {
      alert(`⚠️ ${okCount}/${total} 张上传成功，失败的请重试`);
    }
  } finally { isUploading.value = false; }
};
</script>

<style scoped>
/* ─── 容器：与教师后台完全切割的轻量风 ─── */
.student-app {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 16px;
  box-sizing: border-box;
  max-width: 720px;
  margin: 0 auto;
  font-size: 15px;
}
.student-app.is-guest-mode {
  background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
  border-radius: 24px;
  padding: 28px 24px 40px;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.08);
  margin: 4vh auto;
  max-width: 640px;
  border: 1px solid rgba(255,255,255,0.8);
}

/* ─── 顶部品牌 ─── */
.brand-bar {
  display: flex; align-items: center; gap: 12px;
  padding-bottom: 16px; border-bottom: 1px dashed #e2e8f0; margin-bottom: 4px;
}
.brand-logo-wrap {
  width: 44px; height: 44px;
  display: grid; place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  box-shadow: 0 8px 18px rgba(245, 158, 11, 0.25);
}
.brand-logo {
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 24px; font-weight: 900; color: #3730a3;
}
.brand-text { display: flex; flex-direction: column; }
.brand-text strong { font-size: 16px; color: #0f172a; letter-spacing: 1px; font-family: "STKaiti", "KaiTi", "楷体", serif; }
.brand-text small { font-size: 12px; color: #64748b; letter-spacing: 0.5px; }

/* ─── 步骤卡片 ─── */
.card-stack { display: flex; flex-direction: column; gap: 16px; }
.step-card {
  background: #fff;
  border-radius: 18px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 18px rgba(15, 23, 42, 0.04);
  display: flex; flex-direction: column; gap: 16px;
  transition: 0.25s;
}
.step-card.done { border-color: #bbf7d0; background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 60%); }
.step-head { display: flex; align-items: flex-start; gap: 12px; }
.step-no {
  width: 32px; height: 32px;
  display: grid; place-items: center;
  border-radius: 50%;
  background: #eff6ff; color: #2563eb;
  font-weight: 900; font-size: 14px;
  flex-shrink: 0;
}
.step-no.done { background: #10b981; color: #fff; box-shadow: 0 4px 10px rgba(16,185,129,0.3); }
.step-head h3 { margin: 0; font-size: 17px; color: #0f172a; font-weight: 800; }
.step-head p { margin: 4px 0 0; font-size: 13px; color: #64748b; line-height: 1.55; }

/* ─── 姓名输入 ─── */
.name-input-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.big-input {
  flex: 1; min-width: 0; height: 48px; padding: 0 16px;
  border: 1.5px solid #cbd5e1; border-radius: 12px;
  font-size: 16px; color: #0f172a; background: #f8fafc; outline: none;
  transition: 0.2s;
}
.big-input:focus { border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 4px rgba(59,130,246,0.12); }
.role-chip {
  padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700;
  background: #f3e8ff; color: #7c3aed; border: 1px solid #d8b4fe; white-space: nowrap;
}
.role-chip.web { background: #ecfdf5; color: #047857; border-color: #6ee7b7; }
.auto-name {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 12px;
  background: #f8fafc; border: 1px solid #e2e8f0; width: 100%;
}
.auto-name-icon { font-size: 22px; }
.auto-name strong { flex: 1; color: #0f172a; font-size: 16px; }
.auto-name-tag { font-size: 11px; color: #059669; background: #ecfdf5; border: 1px solid #6ee7b7; padding: 3px 8px; border-radius: 999px; font-weight: 800; }

/* ─── 通道切换 ─── */
.channel-tabs {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}
.channel-tab {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 12px;
  border-radius: 16px; border: 1.5px solid #e2e8f0;
  background: #fff; cursor: pointer; transition: 0.2s;
  text-align: left;
}
.channel-tab:hover { border-color: #93c5fd; background: #f0f7ff; }
.channel-tab.active {
  border-color: #2563eb;
  background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.15);
}
.channel-icon { font-size: 22px; flex-shrink: 0; }
.channel-text strong { display: block; font-size: 13px; color: #0f172a; font-weight: 800; }
.channel-text small { display: block; margin-top: 2px; font-size: 11px; color: #94a3b8; line-height: 1.4; }
.channel-tab.active .channel-text strong { color: #1d4ed8; }

/* ─── URL 行 ─── */
.url-input-row { display: flex; flex-direction: column; gap: 10px; }

/* ─── 拖拽区 ─── */
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 16px;
  background: #f8fafc; padding: 28px 18px;
  transition: 0.25s; cursor: pointer;
  position: relative; min-height: 120px;
}
.drop-zone.is-dragover { border-color: #3b82f6; background: #eff6ff; transform: scale(1.01); }
.drop-zone.has-file, .drop-zone.has-items { border-style: solid; border-color: #6ee7b7; background: #ffffff; cursor: default; }
.drop-zone.img-drop { padding: 16px; }
.hidden-input { display: none; }
.drop-label {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  cursor: pointer; text-align: center;
}
.drop-icon { font-size: 36px; }
.drop-label strong { font-size: 15px; color: #0f172a; font-weight: 800; }
.drop-label small { font-size: 12px; color: #94a3b8; }

/* ─── 图片预览栅格 ─── */
.preview-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 12px;
}
.preview-tile {
  position: relative; background: #fff; border-radius: 12px;
  overflow: hidden; box-shadow: 0 4px 10px rgba(15,23,42,0.06);
  border: 1px solid #e2e8f0; display: flex; flex-direction: column;
}
.preview-tile img {
  width: 100%; height: 90px; object-fit: cover; display: block;
}
.tile-remove {
  position: absolute; top: 6px; right: 6px;
  width: 24px; height: 24px;
  border: none; border-radius: 50%;
  background: rgba(15,23,42,0.7); color: #fff;
  cursor: pointer; font-size: 11px; font-weight: 900;
  display: grid; place-items: center;
}
.tile-remove:hover { background: #ef4444; }
.tile-name {
  width: 100%; height: 28px; padding: 0 8px;
  border: none; border-top: 1px solid #f1f5f9;
  font-size: 11px; outline: none; text-align: center; box-sizing: border-box;
  background: #f8fafc;
}
.tile-name:focus { background: #fff; }
.tile-size { font-size: 10px; color: #94a3b8; padding: 2px 6px 4px; text-align: center; }
.tile-progress {
  position: absolute; top: 0; left: 0; right: 0;
  height: 90px; display: flex; align-items: flex-end;
  pointer-events: none;
}
.tile-progress .bar {
  height: 4px; background: linear-gradient(90deg, #34d399, #10b981); transition: width 0.3s;
}
.tile-progress span {
  position: absolute; top: 6px; left: 6px;
  background: rgba(15,23,42,0.75); color: #fff;
  font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
}
.add-more {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 4px; height: 100%; min-height: 120px;
  background: #f8fafc; border: 1.5px dashed #cbd5e1; border-radius: 12px;
  cursor: pointer; color: #64748b; font-weight: 700; transition: 0.2s;
}
.add-more span { font-size: 28px; line-height: 1; }
.add-more small { font-size: 11px; }
.add-more:hover { background: #eff6ff; border-color: #3b82f6; color: #1d4ed8; }

/* ─── 大按钮 ─── */
.big-btn {
  height: 52px; padding: 0 20px;
  border: none; border-radius: 14px;
  font-size: 15px; font-weight: 900; letter-spacing: 1px;
  cursor: pointer; transition: 0.2s;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
}
.big-btn.full { width: 100%; }
.big-btn.primary {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #fff;
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.28);
}
.big-btn.primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 18px 36px rgba(37, 99, 235, 0.36); }
.big-btn.primary:disabled { background: #cbd5e1; color: #f1f5f9; cursor: not-allowed; box-shadow: none; }

/* ─── 提交记录 ─── */
.history-card { background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 80%); border-color: #bbf7d0; }
.history-list { display: flex; flex-direction: column; gap: 8px; }
.history-row {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border-radius: 12px;
  background: #fff; border: 1px solid #e2e8f0;
}
.history-row.fail { background: #fef2f2; border-color: #fecaca; }
.history-icon { font-size: 18px; }
.history-meta { flex: 1; min-width: 0; }
.history-meta strong { display: block; color: #0f172a; font-size: 13px; }
.history-meta small { display: block; color: #64748b; font-size: 11px; margin-top: 2px; word-break: break-all; }
.history-no {
  background: #0f172a; color: #fde68a;
  padding: 4px 10px; border-radius: 8px;
  font-family: "Menlo", monospace; font-size: 12px; font-weight: 700;
}

/* ─── 成功动画 ─── */
.celebrate-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(15, 23, 42, 0.55); backdrop-filter: blur(6px);
  display: grid; place-items: center; padding: 24px;
}
.celebrate-card {
  background: #fff; border-radius: 24px; padding: 36px 28px;
  text-align: center; max-width: 360px; width: 100%;
  box-shadow: 0 30px 80px rgba(15, 23, 42, 0.3);
  display: flex; flex-direction: column; align-items: center; gap: 14px;
}
.check-circle { width: 72px; height: 72px; }
.check-svg { width: 100%; height: 100%; }
.check-svg circle { stroke-dasharray: 166; stroke-dashoffset: 166; animation: dash 0.6s ease-out forwards; }
.check-svg path { stroke-dasharray: 50; stroke-dashoffset: 50; animation: dash 0.4s 0.5s ease-out forwards; }
@keyframes dash { to { stroke-dashoffset: 0; } }
.celebrate-card h3 { margin: 0; font-size: 19px; color: #0f172a; font-weight: 900; }
.celebrate-card p { margin: 0; font-size: 13px; color: #64748b; line-height: 1.6; }
.success-no {
  background: #0f172a; color: #fde68a;
  padding: 8px 14px; border-radius: 10px;
  font-family: "Menlo", monospace; font-size: 13px; font-weight: 800;
}
.celebrate-enter-active, .celebrate-leave-active { transition: opacity 0.3s; }
.celebrate-enter-active .celebrate-card { animation: pop 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes pop { from { transform: scale(0.85); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.celebrate-enter-from, .celebrate-leave-to { opacity: 0; }

/* ─── 移动端优化 ─── */
@media (max-width: 640px) {
  .student-app { padding: 12px; gap: 14px; }
  .student-app.is-guest-mode { margin: 0 auto; border-radius: 0; padding: 20px 16px 30px; max-width: 100%; box-shadow: none; }
  .channel-tabs { grid-template-columns: 1fr; }
  .channel-tab { padding: 12px; }
  .step-card { padding: 16px; border-radius: 14px; }
  .big-input { font-size: 16px; }
  .big-btn { height: 50px; font-size: 14px; }
  .preview-grid { grid-template-columns: repeat(2, 1fr); }
  .drop-icon { font-size: 30px; }
  .step-head h3 { font-size: 16px; }
}
</style>
