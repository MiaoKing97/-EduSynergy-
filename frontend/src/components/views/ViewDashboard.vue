<template>
  <div class="ai-workspace-container">
    <div class="chat-layout">

      <!-- 🌟 左侧：千人千面的极客指令舱 -->
      <div class="prompt-sidebar">
        <div class="sidebar-header">
          <div class="bot-avatar-box">
            <span class="bot-avatar">🤖</span>
            <span class="status-dot"></span>
          </div>
          <div class="header-text">
            <h4>{{ teacherSubject }} AI 工作台</h4>
            <p>已连入云端飞书数据流</p>
          </div>
        </div>

        <div class="sidebar-scroll custom-scrollbar">
          <div class="quick-actions-group">
            <span class="action-label">🛠️ 基础教务指令</span>
            <button class="action-btn btn-primary" @click="showTableModal = true">
              <span class="icon">📑</span> 创建全自动多维表格
            </button>
            <button class="action-btn" @click="sendQuickPrompt(`请帮我看看目前 ${teacherSubject} 作业的整体提交和得分情况。`)">
              <span class="icon">📊</span> 检查作业整体进度
            </button>
          </div>

          <!-- 🌟 核心优化：根据不同学科老师，动态渲染专属的 ChatBI 快捷指令 -->
          <div class="quick-actions-group">
            <span class="action-label">⚡️ {{ teacherSubject }}专属洞察</span>

            <button v-for="(action, idx) in dynamicQuickActions" :key="idx" class="action-btn" @click="sendQuickPrompt(action.prompt)">
              <span class="icon">{{ action.icon }}</span> {{ action.label }}
            </button>
          </div>
        </div>

        <div class="sidebar-footer">
          <button class="btn-danger" @click="clearChatHistory">
            <span class="icon">🗑️</span> 清空当前对话记录
          </button>
        </div>
      </div>

      <!-- 🌟 右侧：沉浸式对话舱 -->
      <div class="chat-window">
        <div class="chat-history custom-scrollbar" ref="chatMainRef">

          <div v-if="messages.length === 0" class="chat-empty">
            <div class="empty-logo">✨</div>
            <h3>你好，我是你的专属 {{ teacherSubject }} 教务助理</h3>
            <p>我可以实时读取并分析飞书多维表格中的学情数据。<br>请在下方提问，或者点击左侧的快捷洞察指令。</p>
          </div>

          <!-- 对话气泡流 -->
          <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role === 'user' ? 'is-user' : 'is-assistant']">
            <div class="avatar">{{ msg.role === 'user' ? '🧑‍🏫' : '🤖' }}</div>
            <div class="message-content">
              <!-- AI 思考中动画 -->
              <div v-if="msg.role === 'assistant' && !msg.content" class="bubble typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <!-- AI 回答 (Markdown富文本) -->
              <div v-else-if="msg.role === 'assistant'" class="bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <!-- 用户提问 -->
              <div v-else class="bubble">{{ msg.content }}</div>
            </div>
          </div>
        </div>

        <!-- 底部输入框 -->
        <div class="chat-input-area">
          <textarea
            v-model="userInput"
            :placeholder="`输入自然语言查询${teacherSubject}学情，例如：“帮我出几道巩固练习题” (按 Enter 发送)`"
            @keydown.enter.prevent="sendMessage"
            :disabled="isGenerating"
          ></textarea>
          <button class="btn-send" :disabled="!userInput.trim() || isGenerating" @click="sendMessage">
            <span class="send-icon">↑</span>
          </button>
        </div>
      </div>

    </div>

    <!-- 🌟 创建表格弹窗 -->
    <div v-if="showTableModal" class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h3>📑 新建飞书多维表格</h3>
          <button class="close-btn" @click="showTableModal = false">✕</button>
        </div>
        <div class="modal-body">
          <label>作业登记表名称</label>
          <input
            v-model="newTableName"
            type="text"
            placeholder="例如：25计科3班网页设计chapter1"
            @keydown.enter="submitCreateTable"
          />
          <p class="help-text">系统将自动为您配置【姓名】、【作业图片】、【状态】、【得分】、【评语】等标准教务流水线字段。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showTableModal = false">取消</button>
          <button class="btn-confirm" @click="submitCreateTable" :disabled="!newTableName.trim() || isGenerating">立即创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import axios from 'axios';
import MarkdownIt from 'markdown-it';
import { globalStore } from '../../store';

const API_HOMEWORK_URL = '/api/homework';

const chatMainRef = ref(null);
const userInput = ref('');
const isGenerating = ref(false);
const showTableModal = ref(false);
const newTableName = ref('');

// 🌟 学科身份感知
const isWebTeacher = computed(() => globalStore.auth.role === 'web_teacher');
const teacherSubject = computed(() => globalStore.auth.subject || '通用学科');

// 🌟 动态生成千人千面快捷指令
const dynamicQuickActions = computed(() => {
  if (isWebTeacher.value) {
    return [
      { icon: '🚨', label: '提取不及格预警名单', prompt: '帮我列出本次综合评分低于 60 分的学生名单，请用表格展示。' },
      { icon: '📱', label: '检索移动端薄弱学生', prompt: '帮我查一下，【响应式适配】这一项，得分低于 60 分的都有谁？' },
      { icon: '💡', label: '盘点全班高频错因', prompt: '分析一下当前多维表格里，大家最薄弱的设计规范和高频错因是什么？' },
      { icon: '🏆', label: '撰写优秀榜样表扬信', prompt: '根据全班得分最高的前3名同学的页面表现，生成一段表扬信。' }
    ];
  } else {
    // 通用学科老师（语数外等）专属的“痛点指令”
    return [
      { icon: '📉', label: '提取易错知识点', prompt: `根据最近的${teacherSubject.value}作业，帮我列出全班错误率最高的 3 个知识点，用表格展示。` },
      { icon: '🎯', label: '生成针对性练习题', prompt: `针对全班最薄弱的知识点，帮我生成 3 道难度适中的${teacherSubject.value}巩固练习题，并附带答案。` },
      { icon: '🚨', label: '检索不及格名单', prompt: '帮我查一下，最近一次作业没有做对的同学都有谁？' },
      { icon: '📝', label: '撰写班级学情周报', prompt: `请结合当前多维表格的数据，帮我生成一份本周的${teacherSubject.value}班级学情分析周报，要求包含整体正确率、存在的问题和下一步教学建议。` }
    ];
  }
});

const md = new MarkdownIt({ breaks: true, html: true });
const renderMarkdown = (text) => {
  if (!text) return '';
  return md.render(text);
};

// 动态构建打招呼信息
const getDefaultMessages = () => [
  {
    role: 'assistant',
    content: `👋 **${globalStore.auth.username || '老师'}** 您好！我是您的 **${teacherSubject.value} AI 教务助理**。\n\n我已经连入底层大模型，并具备 **云端飞书数据实时调阅权限**。您可以直接问我关于班级作业提交、知识点掌握情况以及各项分数统计的问题。\n\n**建议操作**：您可以点击左侧面板的「📑 创建全自动多维表格」，系统会自动生成专用表格并派发专属的学生提交链接。`
  }
];

const getStorageKey = () => {
  const userId = globalStore.auth.userId || 'guest';
  return `ai_assistant_chat_history_${userId}`;
};

const loadMessages = () => {
  const saved = localStorage.getItem(getStorageKey());
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      return parsed.filter(msg => !(msg.role === 'assistant' && !msg.content));
    } catch (e) {
      return getDefaultMessages();
    }
  }
  return getDefaultMessages();
};

const messages = ref(loadMessages());

watch(
  () => globalStore.auth.userId,
  (newId, oldId) => { if (newId !== oldId) messages.value = loadMessages(); }
);

watch(
  messages,
  (newVal) => { localStorage.setItem(getStorageKey(), JSON.stringify(newVal)); },
  { deep: true }
);

const clearChatHistory = () => {
  if (confirm('⚠️ 确定要清空当前账号的所有对话记录吗？')) {
    messages.value = getDefaultMessages();
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatMainRef.value) {
    chatMainRef.value.scrollTop = chatMainRef.value.scrollHeight;
  }
};

const sendQuickPrompt = (text) => {
  userInput.value = text;
  sendMessage();
};

// 🌟 核心引擎双轨化：智能提纯脱水，不浪费大模型 Token
const extractDataContext = () => {
  const token = globalStore.config.feishuToken;
  if (!token || !globalStore.tableDataCache[token]) return "[]";

  const rawRecords = globalStore.tableDataCache[token].rawRecords || [];

  const condensedData = rawRecords.map(r => {
    const isPass = r.is_correct === 'true' || r.is_correct === '正确';
    const cleanName = (r.student_name || '未知').replace('-UI评测', '');

    // 如果是网页老师，提取 5 维雷达图 JSON 数据
    if (isWebTeacher.value) {
      let uiScore = 0, responsiveScore = 0, semanticsScore = 0, perfScore = 0, interactionScore = 0;
      try {
        const match = String(r.error_cause).match(/`{3}json([\s\S]*?)`{3}/);
        if (match) {
          const jsonObj = JSON.parse(match[1].trim());
          const values = jsonObj.series?.[0]?.data?.[0]?.value || [];
          uiScore = values[0] || 0;
          responsiveScore = values[1] || 0;
          semanticsScore = values[2] || 0;
          perfScore = values[3] || 0;
          interactionScore = values[4] || 0;
        }
      } catch(e){}

      const totalScore = uiScore || responsiveScore ? Math.round((uiScore + responsiveScore + semanticsScore + perfScore + interactionScore) / 5) : (isPass ? 100 : 0);
      return {
        name: cleanName,
        project: r.question_number,
        score: totalScore,
        dimensions: { "UI美观度": uiScore, "响应式适配": responsiveScore, "语义化": semanticsScore, "性能": perfScore, "交互": interactionScore }
      };
    }
    // 如果是通用学科老师，提取 核心考点与具体错因
    else {
      // 简单清洗错因，去除冗余 markdown 代码块
      let cleanError = String(r.error_cause || '无').replace(/`{3}json_array[\s\S]*?`{3}/g, '').replace(/`{3}json[\s\S]*?`{3}/g, '').trim();
      if (cleanError.length > 50) cleanError = cleanError.substring(0, 50) + '...'; // 限制长度，防止超出 Token

      return {
        name: cleanName,
        question: r.question_number,
        knowledge_point: r.knowledge_point || '未分类',
        is_correct: isPass ? '做对' : '做错',
        error_detail: isPass ? '无' : cleanError
      };
    }
  });

  return JSON.stringify(condensedData);
};

const sendMessage = async () => {
  if (!userInput.value.trim() || isGenerating.value) return;

  if (!globalStore.config.apiKey) {
    alert("⚠️ 请先在【开发者参数底盘】配置您的大模型 API KEY！");
    return;
  }

  const text = userInput.value.trim();
  userInput.value = '';

  messages.value.push({ role: 'user', content: text });
  isGenerating.value = true;
  await scrollToBottom();

  messages.value.push({ role: 'assistant', content: '' });
  await scrollToBottom();

  try {
    const dataContext = extractDataContext();

    const response = await axios.post(`${API_HOMEWORK_URL}/chat_with_data`, {
      user_message: text,
      data_context: dataContext,
      ai_model: globalStore.config.model || 'ep-20240523091929-28c94',
      api_key: globalStore.config.apiKey
    });

    if (response.data.status === 'success') {
      messages.value[messages.value.length - 1].content = response.data.reply;
    }
  } catch (error) {
    console.error("AI 接口调用失败:", error);
    messages.value[messages.value.length - 1].content = `❌ **数据引擎调用失败**\n原因: ${error.response?.data?.detail || error.message}\n请检查您的 API KEY 和网络，或者确认后端 /chat_with_data 接口已正确部署。`;
  } finally {
    isGenerating.value = false;
    await scrollToBottom();
  }
};

const submitCreateTable = async () => {
  if (!newTableName.value.trim()) return;
  const tableName = newTableName.value;
  showTableModal.value = false;
  newTableName.value = '';

  messages.value.push({ role: 'user', content: `请帮我从零创建一个飞书多维表格，命名为「${tableName}」` });
  messages.value.push({ role: 'assistant', content: '' });
  isGenerating.value = true;
  await scrollToBottom();

  try {
    const cfg = globalStore.config;
    if (!cfg.feishuAppId || !cfg.feishuAppSecret) {
      throw new Error("请先在右侧配置飞书 App ID 和 App Secret");
    }

    const response = await axios.post(`${API_HOMEWORK_URL}/create_table`, {
      table_name: tableName,
      feishu_app_id: cfg.feishuAppId,
      feishu_app_secret: cfg.feishuAppSecret
    });

    if (response.data.status === 'success') {
      globalStore.config.feishuToken = response.data.app_token;
      globalStore.config.feishuTableId = response.data.table_id;

      if (!globalStore.config.bitableList) globalStore.config.bitableList = [];
      const isExist = globalStore.config.bitableList.find(item => item.token === response.data.app_token);
      if (!isExist) {
        globalStore.config.bitableList.unshift({
          name: tableName,
          token: response.data.app_token,
          date: new Date().toLocaleString(),
          ownerId: globalStore.auth.userId,
          ownerName: globalStore.auth.username,
          subject: globalStore.auth.subject
        });
      }

      const invitePayload = {
        feishuAppId: cfg.feishuAppId,
        feishuAppSecret: cfg.feishuAppSecret,
        appToken: response.data.app_token,
        isWeb: globalStore.auth.role === 'web_teacher',
        tableName: tableName
      };

      const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(invitePayload))));
      const inviteLink = `${window.location.origin}/?invite=${encoded}`;

      messages.value[messages.value.length - 1].content = `✅ **表格引擎搭建完毕！**\n\n📌 **管理后台链接 (老师专属)**\n👉 <a href="${response.data.url}" target="_blank" style="color:#1890ff;font-weight:bold;text-decoration:underline;">点击进入飞书多维表格后台</a>\n\n📢 **作业分发链接（请复制下发给学生）**\n🔗 <a href="${inviteLink}" target="_blank" style="color:#10b981;font-weight:bold;word-break:break-all;">${inviteLink}</a>\n\n*提示：学生点击该链接即可免登录访问专属通道，所提交的数据将实现物理级隔离，精确落入本表格中。*`;
    }
  } catch (error) {
    console.error("建表失败:", error);
    messages.value[messages.value.length - 1].content = `❌ 创建失败: ${error.response?.data?.detail || error.message}\n请检查您的飞书凭证是否正确或权限是否开启。`;
  } finally {
    isGenerating.value = false;
    await scrollToBottom();
  }
};
</script>

<style scoped>
.ai-workspace-container { width: 100%; height: 100%; background: #fff; border-radius: 12px; border: 1px solid #edf2f7; box-shadow: 0 4px 20px rgba(0,0,0,0.03); overflow: hidden; }
.chat-layout { display: flex; height: 100%; }

/* 左侧预设指令舱 */
.prompt-sidebar { width: 300px; background: #f8fafc; border-right: 1px solid #edf2f7; display: flex; flex-direction: column; }
.sidebar-header { display: flex; align-items: center; gap: 14px; padding: 24px 20px; border-bottom: 1px solid #e2e8f0;}
.bot-avatar-box { position: relative; }
.bot-avatar { font-size: 26px; background: #e0e7ff; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 14px; border: 1px solid #c7d2fe;}
.status-dot { position: absolute; bottom: -2px; right: -2px; width: 12px; height: 12px; background: #10b981; border: 2px solid #f8fafc; border-radius: 50%; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);}
.header-text h4 { margin: 0 0 4px 0; font-size: 16px; color: #1e293b; font-weight: 800; }
.header-text p { margin: 0; font-size: 12px; color: #10b981; font-weight: 700; }

.sidebar-scroll { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 24px; }
.quick-actions-group { display: flex; flex-direction: column; gap: 10px; }
.action-label { font-size: 12px; color: #64748b; font-weight: 700; margin-bottom: 4px; padding-left: 4px;}
.action-btn { background: #fff; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 10px; text-align: left; font-size: 13px; color: #334155; font-weight: 600; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.01);}
.action-btn:hover { background: #eff6ff; border-color: #bfdbfe; color: #2563eb; transform: translateX(2px); box-shadow: 0 4px 8px rgba(37,99,235,0.05);}
.btn-primary { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; font-weight: 700; }
.btn-primary:hover { background: #dbeafe; border-color: #93c5fd; }
.action-btn .icon { font-size: 16px; }

.sidebar-footer { padding: 16px 20px; border-top: 1px solid #e2e8f0; }
.btn-danger { width: 100%; background: #fef2f2; border: 1px dashed #fecaca; padding: 10px; border-radius: 8px; color: #dc2626; font-size: 13px; font-weight: 600; cursor: pointer; transition: 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px;}
.btn-danger:hover { background: #fee2e2; border-style: solid; border-color: #f87171; }

/* 右侧对话舱 */
.chat-window { flex: 1; display: flex; flex-direction: column; background: #fff; position: relative; }
.chat-history { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; }

.chat-empty { margin: auto; display: flex; flex-direction: column; align-items: center; text-align: center; color: #64748b; max-width: 450px; }
.empty-logo { font-size: 46px; margin-bottom: 20px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.05));}
.chat-empty h3 { color: #1e293b; margin-bottom: 10px; font-weight: 800;}
.chat-empty p { font-size: 14px; line-height: 1.6; color: #94a3b8;}

.message-wrapper { display: flex; gap: 16px; max-width: 85%; }
.message-wrapper.is-user { align-self: flex-end; flex-direction: row-reverse; }
.avatar { font-size: 20px; background: #f1f5f9; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 50%; flex-shrink: 0; border: 1px solid #e2e8f0;}
.message-wrapper.is-user .avatar { background: #dbeafe; border-color: #bfdbfe; }

.bubble { padding: 14px 20px; border-radius: 14px; font-size: 14px; line-height: 1.6; color: #1e293b; background: #f8fafc; border: 1px solid #e2e8f0; }
.message-wrapper.is-user .bubble { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #fff; border: none; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); border-top-right-radius: 4px;}
.message-wrapper.is-assistant .bubble { border-top-left-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.02);}

/* Markdown 精美解析样式 */
:deep(.markdown-body p) { margin-top: 0; margin-bottom: 12px; }
:deep(.markdown-body p:last-child) { margin-bottom: 0; }
:deep(.markdown-body ul), :deep(.markdown-body ol) { margin: 8px 0; padding-left: 20px; }
:deep(.markdown-body strong) { color: #0f172a; font-weight: 800; }
:deep(.markdown-body pre) { background: #0f172a; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 12px 0; border: none; }
:deep(.markdown-body code) { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; color: #db2777;}
:deep(.markdown-body pre code) { background: transparent; padding: 0; color: #e2e8f0; }
/* AI 智能生成的表格样式 */
:deep(.markdown-body table) { width: 100%; border-collapse: collapse; margin: 16px 0; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.02);}
:deep(.markdown-body th) { background: #f1f5f9; padding: 12px 16px; text-align: left; font-weight: 800; color: #334155; border-bottom: 2px solid #cbd5e1; }
:deep(.markdown-body td) { padding: 12px 16px; border-bottom: 1px solid #f1f5f9; color: #475569; }
:deep(.markdown-body tr:last-child td) { border-bottom: none; }
:deep(.markdown-body tr:hover td) { background: #f8fafc; }

/* 思考动画 */
.typing-indicator { display: flex; align-items: center; gap: 4px; padding: 16px 20px !important; }
.typing-indicator span { width: 6px; height: 6px; background-color: #3b82f6; border-radius: 50%; animation: blink 1.4s infinite both; }
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.2; transform: scale(0.8);} 40% { opacity: 1; transform: scale(1.2);} }

/* 底部输入框 */
.chat-input-area { padding: 20px 24px; background: #fff; border-top: 1px solid #edf2f7; position: relative; display: flex; align-items: flex-end; gap: 12px; }
.chat-input-area textarea { flex: 1; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 14px 60px 14px 16px; font-size: 14px; resize: none; height: 50px; outline: none; transition: 0.2s; font-family: inherit; line-height: 1.5; color: #1e293b; box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);}
.chat-input-area textarea:focus { background: #fff; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15); }
.btn-send { position: absolute; right: 34px; bottom: 25px; width: 38px; height: 38px; background: #2563eb; color: #fff; border: none; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 10px rgba(37,99,235,0.3);}
.btn-send:hover:not(:disabled) { transform: translateY(-2px); background: #1d4ed8; box-shadow: 0 6px 14px rgba(29, 78, 216, 0.4);}
.btn-send:disabled { background: #cbd5e1; cursor: not-allowed; box-shadow: none; color: #f1f5f9;}

.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* Modal 保持原有优雅设计 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(15,23,42,0.4); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(4px); }
.modal-content { background: white; border-radius: 16px; width: 440px; box-shadow: 0 20px 40px rgba(0,0,0,0.15); animation: slideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes slideIn { from { transform: translateY(-30px) scale(0.95); opacity: 0; } to { transform: translateY(0) scale(1); opacity: 1; } }
.modal-header { padding: 20px 24px; border-bottom: 1px solid #edf2f7; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 18px; color: #1e293b; font-weight: 800; }
.close-btn { background: none; border: none; font-size: 20px; color: #94a3b8; cursor: pointer; transition: 0.2s;}
.close-btn:hover { color: #ef4444; transform: rotate(90deg); }
.modal-body { padding: 24px; display: flex; flex-direction: column; gap: 14px; }
.modal-body label { font-size: 14px; color: #475569; font-weight: 700; }
.modal-body input { padding: 12px 14px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; transition: 0.2s; }
.modal-body input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.15); }
.help-text { font-size: 13px; color: #64748b; margin: 0; line-height: 1.6; }
.modal-footer { padding: 16px 24px; border-top: 1px solid #edf2f7; display: flex; justify-content: flex-end; gap: 12px; background: #f8fafc; border-bottom-left-radius: 16px; border-bottom-right-radius: 16px; }
.btn-cancel { background: white; border: 1px solid #cbd5e1; padding: 10px 20px; border-radius: 8px; font-weight: 600; color: #475569; cursor: pointer; transition: 0.2s;}
.btn-cancel:hover { color: #3b82f6; border-color: #93c5fd; background: #eff6ff;}
.btn-confirm { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.2s;}
.btn-confirm:hover:not(:disabled) { background: #1d4ed8; box-shadow: 0 4px 12px rgba(29, 78, 216, 0.3); }
.btn-confirm:disabled { background: #94a3b8; cursor: not-allowed; }
</style>