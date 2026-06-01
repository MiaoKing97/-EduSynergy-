<template>
  <div v-if="isGuestMode" class="guest-fullscreen-layout">
    <ViewStudent />
  </div>

  <template v-else>
    <ViewLogin v-if="!globalStore.auth.isLoggedIn" />

    <div v-else class="dashboard-layout">
      <aside class="sidebar-left">
        <div class="logo-area">
          <div class="logo-wrapper">
            <span class="logo-icon">🤖</span>
            <h1 class="logo-text">杏坛智析・人机协同学情共创平台</h1>
          </div>
        </div>

        <nav class="menu-list">
          <div v-if="globalStore.auth.role === 'admin'" class="menu-item" :class="{ active: currentView === 'accountManager' }" @click="currentView = 'accountManager'">
            <span class="menu-item-icon">👥</span>
            <span class="menu-item-text">账号权限管理</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)" class="menu-item" :class="{ active: currentView === 'dashboard' }" @click="currentView = 'dashboard'">
            <span class="menu-item-icon">📊</span>
            <span class="menu-item-text">运行仪表盘</span>
          </div>

          <div v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)" class="menu-item" :class="{ active: currentView === 'tableManager' }" @click="currentView = 'tableManager'">
            <span class="menu-item-icon">🗂️</span>
            <span class="menu-item-text">表格大盘管理</span>
          </div>

          <div v-if="globalStore.auth.role === 'teacher'" class="menu-item" :class="{ active: currentView === 'teacher' }" @click="currentView = 'teacher'">
            <span class="menu-item-icon">📝</span>
            <span class="menu-item-text">老师模板设置</span>
          </div>

          <div v-if="globalStore.auth.role !== 'admin'" class="menu-item" :class="{ active: currentView === 'student' }" @click="currentView = 'student'">
            <span class="menu-item-icon">📤</span>
            <span class="menu-item-text">学生作业代交</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)" class="menu-item" :class="{ active: currentView === 'grading' }" @click="currentView = 'grading'">
            <span class="menu-item-icon">✅</span>
            <span class="menu-item-text">智能作业批改</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)" class="menu-item" :class="{ active: currentView === 'analytics' }" @click="currentView = 'analytics'">
            <span class="menu-item-icon">📈</span>
            <span class="menu-item-text">学情分析大屏</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)" class="menu-item" :class="{ active: currentView === 'grades' }" @click="currentView = 'grades'">
            <span class="menu-item-icon">🧑‍🎓</span>
            <span class="menu-item-text">学生成绩档案</span>
          </div>
        </nav>

        <div class="user-profile">
          <div class="user-info">
            <span class="user-avatar">
              {{ globalStore.auth.role === 'admin' ? '👨‍💼' : (['teacher', 'web_teacher'].includes(globalStore.auth.role) ? '👨‍🏫' : '🧑‍🎓') }}
            </span>
            <div class="user-meta">
              <span class="user-name">{{ globalStore.auth.username }}</span>
              <span class="user-sub">{{ globalStore.auth.subject }}</span>
            </div>
          </div>
          <button class="btn-logout" @click="handleLogout">退出登录</button>
        </div>
      </aside>

      <main class="main-workspace">
        <div class="workspace-header">
          <h2 class="header-title">{{ currentViewTitle }}</h2>

          <div v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)" class="header-table-tabs">
            <div v-if="pinnedTables.length === 0" class="empty-tab-hint">
              📭 暂无固定的常用表格，请前往「表格大盘管理」中勾选固定
            </div>

            <div v-else
                 v-for="item in pinnedTables"
                 :key="item.token"
                 class="table-tab"
                 :class="{ 'is-active': globalStore.config.feishuToken === item.token }"
                 @click="useBitable(item)"
            >
              <span class="tab-icon">📊</span>
              <span class="tab-name" :title="item.name">{{ item.name }}</span>
              <div class="tab-actions">
                <button class="tab-btn" @click.stop="openBitableLink(item)" title="在浏览器打开多维表格">🌐</button>
                <button class="tab-btn tab-delete" @click.stop="unpinTab(item)" title="从顶栏取消固定">✕</button>
              </div>
            </div>
          </div>

          <button v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)" class="btn-toggle-panel" @click="toggleConfigPanel">
            <span v-if="isConfigOpen">⚙️ 收起参数底盘 ➡️</span>
            <span v-else>⬅️ 展开参数底盘 ⚙️</span>
          </button>
          <div v-else class="student-header-hint">欢迎来到作业提交系统，请上传清晰的作业图片！</div>
        </div>

        <div class="workspace-content">
  <transition name="fade-slide" mode="out-in">
    <keep-alive>
      <component :is="currentViewComponent" :key="currentView" @changeView="currentView = $event"></component>
    </keep-alive>
  </transition>
</div>
      </main>

      <aside v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)" class="sidebar-right" :class="{ 'is-collapsed': !isConfigOpen }">
        <div class="config-header">
          <span class="config-header-icon">⚙️</span> 开发者参数底盘
        </div>
        <div class="config-body">

          <div class="config-card">
            <div class="config-section-title">🧠 大模型服务配置</div>
            <div class="form-group">
              <label>选择 AI 大模型</label>
              <select v-model="globalStore.config.model">
                <option value="doubao-seed-2-0-pro-260215">火山豆包 2.0 Pro (多模态批改)</option>
                <option value="doubao-seed-2-0-mini-260428">火山豆包 2.0 Mini (极速视觉模型)</option>
                <option value="doubao-seed-2-0-lite-260428">火山豆包 2.0 Lite (轻量视觉模型)</option>
                <option value="deepseek-chat">DeepSeek-V3 (标准文本模型)</option>
                <option value="deepseek-reasoner">DeepSeek-R1 (深度思考模型)</option>
              </select>
            </div>
            <div class="form-group">
              <label>模型 API Key</label>
              <input type="password" v-model="globalStore.config.apiKey" placeholder="输入 sk-..." />
            </div>

            <div class="form-group">
              <label>⚡ AI 并发批改车道数</label>
              <select v-model.number="globalStore.config.concurrency">
                <option :value="1">单线程排队 (1份/次) - 稳定防封</option>
                <option :value="3">多线程并发 (3份/次) - 官方推荐</option>
                <option :value="5">高并发提速 (5份/次) - 极速</option>
              </select>
            </div>

            <div class="form-group">
              <label>🗣️ 附加批改偏好 (可选)</label>
              <textarea v-model="globalStore.config.customPrompt" rows="3" placeholder="添加特殊批改要求..."></textarea>
              <div class="quick-tags">
                <span class="tag-btn" v-for="tag in quickPrompts" :key="tag" @click="appendPrompt(tag)">+ {{ tag }}</span>
                <span class="tag-btn tag-clear" v-if="globalStore.config.customPrompt" @click="globalStore.config.customPrompt = ''">清空</span>
              </div>
            </div>
          </div>

          <div class="config-card">
            <div class="config-section-title">📑 飞书开放平台接入</div>
            <div class="form-group">
              <label>飞书 App ID</label>
              <input type="text" v-model="globalStore.config.feishuAppId" placeholder="cli_..." />
            </div>
            <div class="form-group">
              <label>飞书 App Secret</label>
              <input type="password" v-model="globalStore.config.feishuAppSecret" placeholder="输入 App Secret" />
            </div>
            <div class="form-group">
              <label>当前全局焦点 Token</label>
              <input type="text" v-model="globalStore.config.feishuToken" placeholder="bascn..." />
            </div>
          </div>

          <button class="btn-save" @click="saveGlobalConfig">
            <span class="save-icon">💾</span> 缓存并应用全局配置
          </button>
        </div>
      </aside>
    </div>
  </template>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { globalStore } from './store';
import ViewAccountManager from './components/views/ViewAccountManager.vue';
import ViewTableManager from './components/views/ViewTableManager.vue';
import ViewGrades from './components/views/ViewGrades.vue';
import ViewLogin from './components/views/ViewLogin.vue';
import ViewDashboard from './components/views/ViewDashboard.vue';
import ViewTeacher from './components/views/ViewTeacher.vue';
import ViewStudent from './components/views/ViewStudent.vue';
import ViewGrading from './components/views/ViewGrading.vue';
import ViewAnalytics from './components/views/ViewAnalytics.vue';

// 🌟 核心路由拦截：判断是否带有专属邀请码
const urlParams = new URLSearchParams(window.location.search);
const isGuestMode = ref(!!urlParams.get('invite'));

const currentView = ref('dashboard');

const viewMap = {
  accountManager: { component: ViewAccountManager, title: '👥 全局教职工账号管理' },
  tableManager: { component: ViewTableManager, title: '🗂️ 班级表格大盘管理' },
  dashboard: { component: ViewDashboard, title: '运行仪表盘' },
  teacher: { component: ViewTeacher, title: '老师模板设置' },
  student: { component: ViewStudent, title: '学生作业同步' },
  grading: { component: ViewGrading, title: '智能作业批改' },
  analytics: { component: ViewAnalytics, title: '学情分析大屏' },
  grades: { component: ViewGrades, title: '学生成绩档案中心' }
};

const currentViewComponent = computed(() => viewMap[currentView.value]?.component || ViewDashboard);
const currentViewTitle = computed(() => viewMap[currentView.value]?.title || '工作台');

const pinnedTables = computed(() => {
  if (!globalStore.config.bitableList) return [];
  return globalStore.config.bitableList.filter(item =>
    item.isPinned !== false &&
    (globalStore.auth.role === 'admin' || item.ownerId === globalStore.auth.userId)
  );
});

const isConfigOpen = ref(true);
const toggleConfigPanel = () => { isConfigOpen.value = !isConfigOpen.value; };

const saveGlobalConfig = () => { alert('✅ 底层凭证及并发策略参数应用成功！'); };
const handleLogout = () => {
  globalStore.auth = { isLoggedIn: false, role: '', username: '', userId: '', subject: '' };
};

const useBitable = (item) => { globalStore.config.feishuToken = item.token; };
const openBitableLink = (item) => {
  if (item.token) window.open(`https://www.feishu.cn/base/${item.token}`, '_blank');
};
const unpinTab = (item) => { item.isPinned = false; };

const quickPrompts = ["严格扣分：无过程不得分", "忽略轻微错别字", "注重鼓励：多用赞美语气", "重点检查：漏写单位扣半分布"];
const appendPrompt = (tag) => {
  let current = globalStore.config.customPrompt || '';
  if (current.includes(tag)) return;
  globalStore.config.customPrompt = current.trim() === '' ? tag : current.trim() + '，' + tag;
};

watch(
  () => globalStore.auth.isLoggedIn,
  (isLoggedIn) => {
    // 只有非访客模式，才需要判断权限跳转
    if (isLoggedIn && !isGuestMode.value) {
      if (globalStore.auth.role === 'student') {
        currentView.value = 'student';
        isConfigOpen.value = false;
      } else if (globalStore.auth.role === 'admin') {
        currentView.value = 'accountManager';
      } else {
        currentView.value = 'dashboard';
      }
    }
  },
  { immediate: true }
);
</script>

<style>
html, body {
  margin: 0; padding: 0; height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f4f5f7; overflow: hidden;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: rgba(100, 116, 139, 0.2); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background-color: rgba(100, 116, 139, 0.4); }

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(8px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>

<style scoped>
/* 🌟 新增：专属学生沉浸式提交页背景 */
.guest-fullscreen-layout {
  width: 100vw;
  height: 100vh;
  overflow-y: auto;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 40px 20px;
  box-sizing: border-box;
}

.dashboard-layout { display: flex; height: 100vh; width: 100vw; overflow: hidden; }

.sidebar-left {
  width: 250px;
  background: linear-gradient(180deg, #0b0f19 0%, #070a12 100%);
  color: #f3f4f6;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 11;
  border-right: 1px solid rgba(255, 255, 255, 0.04);
}
.logo-area { height: 72px; display: flex; align-items: center; padding: 0 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
.logo-wrapper { display: flex; align-items: center; gap: 12px; }
.logo-icon { font-size: 22px; filter: drop-shadow(0 2px 8px rgba(24, 144, 255, 0.4)); }
.logo-area h1.logo-text { font-size: 16px; margin: 0; font-weight: 700; letter-spacing: 0.8px; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.menu-list { padding: 24px 12px; display: flex; flex-direction: column; gap: 4px; flex: 1; overflow-y: auto;}

.menu-item { padding: 12px 16px; cursor: pointer; color: #9ca3af; font-size: 14px; font-weight: 500; border-radius: 8px; display: flex; align-items: center; gap: 12px; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.menu-item-icon { font-size: 16px; width: 20px; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
.menu-item-text { letter-spacing: 0.3px; }
.menu-item:hover { color: #ffffff; background-color: rgba(255, 255, 255, 0.05); }
.menu-item:hover .menu-item-icon { transform: scale(1.15); }
.menu-item.active { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: #ffffff; font-weight: 600; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); }
.menu-item.active .menu-item-icon { transform: scale(1.05); }

.user-profile { padding: 16px; margin: 12px; border-radius: 12px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.04); display: flex; flex-direction: column; gap: 12px; }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { font-size: 18px; background: rgba(255, 255, 255, 0.06); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 1px solid rgba(255, 255, 255, 0.1); }
.user-meta { display: flex; flex-direction: column; overflow: hidden; }
.user-name { font-size: 14px; font-weight: 600; color: #ffffff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.user-sub { font-size: 11px; color: #60a5fa; font-weight: 500; margin-top: 1px; }

.btn-logout { background: rgba(255,255,255,0.04); color: #9ca3af; border: 1px solid rgba(255,255,255,0.06); padding: 8px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s;}
.btn-logout:hover { background: rgba(239, 68, 68, 0.12); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }

.main-workspace { flex: 1; display: flex; flex-direction: column; background-color: #f8fafc; min-width: 0; }
.workspace-header { height: 72px; background-color: #fff; display: flex; align-items: center; padding: 0 24px; box-shadow: 0 1px 4px rgba(0,21,41,.03); border-bottom: 1px solid #edf2f7; z-index: 10; flex-shrink: 0; gap: 24px; }
.header-title { margin: 0; font-size: 16px; color: #1a202c; font-weight: 700; white-space: nowrap; flex-shrink: 0; }

.header-table-tabs { flex: 1; display: flex; align-items: center; gap: 10px; overflow-x: auto; height: 100%; scrollbar-width: none; }
.header-table-tabs::-webkit-scrollbar { display: none; }
.empty-tab-hint { font-size: 13px; color: #94a3b8; font-weight: 500; font-style: italic; }
.table-tab { display: flex; align-items: center; gap: 6px; padding: 0 8px 0 14px; height: 36px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 18px; cursor: pointer; transition: all 0.2s; flex-shrink: 0; }
.table-tab:hover { border-color: #cbd5e1; background: #e2e8f0; }
.table-tab.is-active { background: #eff6ff; border-color: #3b82f6; box-shadow: 0 2px 6px rgba(37,99,235,0.06); }
.tab-name { font-size: 13px; font-weight: 500; color: #475569; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-tab.is-active .tab-name { color: #2563eb; font-weight: 700; }
.tab-actions { display: flex; align-items: center; }
.tab-btn { background: transparent; border: none; cursor: pointer; font-size: 12px; opacity: 0.4; padding: 0; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
.tab-btn:hover { opacity: 1; background: rgba(0,0,0,0.05); }
.tab-btn.tab-delete:hover { background: #fee2e2; color: #ef4444; }

.btn-toggle-panel { flex-shrink: 0; background: #fff; border: 1px solid #e2e8f0; padding: 8px 16px; border-radius: 8px; cursor: pointer; color: #475569; font-size: 13px; font-weight: 600; transition: all 0.2s ease; }
.btn-toggle-panel:hover { color: #2563eb; border-color: #2563eb; background-color: #eff6ff; box-shadow: 0 2px 8px rgba(37,99,235,0.1); }
.student-header-hint { font-size: 14px; color: #16a34a; font-weight: bold; }

.workspace-content { flex: 1; padding: 24px; overflow-y: auto; box-sizing: border-box; }
:deep(.view-container) { background-color: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.02); min-height: 100%; box-sizing: border-box; border: 1px solid #edf2f7; }

.sidebar-right {
  width: 340px;
  background-color: #f8fafc;
  border-left: 1px solid #e2e8f0;
  display: flex; flex-direction: column;
  box-shadow: -4px 0 24px rgba(0,0,0,0.02);
  z-index: 10; flex-shrink: 0;
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), border-left 0.3s ease;
  overflow: hidden;
}
.sidebar-right.is-collapsed { width: 0; border-left: none; }
.config-header, .config-body { width: 340px; box-sizing: border-box; }
.config-header {
  height: 72px; display: flex; align-items: center; padding: 0 24px;
  font-size: 16px; font-weight: 700; color: #0f172a;
  border-bottom: 1px solid #e2e8f0; background-color: #fff; flex-shrink: 0;
}
.config-header-icon { margin-right: 8px; font-size: 18px; }

.config-body { padding: 24px; overflow-y: auto; flex: 1; }

.config-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
}

.config-section-title {
  font-size: 14px; font-weight: 700; color: #1e293b;
  margin-bottom: 16px; display: flex; align-items: center; gap: 6px;
}

.form-group { margin-bottom: 18px; }
.form-group:last-child { margin-bottom: 0; }
.form-group label {
  display: block; margin-bottom: 8px; font-size: 12px; color: #64748b;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
}

.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 10px 14px; border: 1.5px solid #cbd5e1;
  border-radius: 8px; font-size: 13px; color: #0f172a; font-weight: 500;
  box-sizing: border-box; transition: all 0.25s ease;
  background-color: #f8fafc;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  outline: none; border-color: #3b82f6; background-color: #fff;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.quick-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.tag-btn {
  font-size: 11px; font-weight: 600; color: #3b82f6;
  background: #eff6ff; padding: 6px 10px; border-radius: 6px;
  border: 1px solid #bfdbfe; cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.tag-btn:hover { background: #dbeafe; border-color: #93c5fd; transform: translateY(-1px); }
.tag-btn.tag-clear { color: #ef4444; background: #fef2f2; border-color: #fecaca; }
.tag-btn.tag-clear:hover { background: #fee2e2; border-color: #f87171; }

.btn-save {
  width: 100%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff; border: none; padding: 14px 16px; border-radius: 10px;
  font-size: 14px; font-weight: 700; cursor: pointer;
  transition: all 0.3s ease; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25);
  display: flex; justify-content: center; align-items: center; gap: 8px;
}
.btn-save:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4); }
.save-icon { font-size: 16px; }
</style>