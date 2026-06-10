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
            <span class="logo-icon">杏</span>
            <div class="logo-title-group">
              <h1 class="logo-text">杏坛智析</h1>
              <span class="logo-subtitle">EduSynergy</span>
            </div>
          </div>
        </div>

        <nav class="menu-list">
          <div v-if="globalStore.auth.role === 'admin'"
               class="menu-item"
               :class="{ active: $route.path === '/account-manager' }"
               @click="$router.push('/account-manager')">
            <span class="menu-item-icon">👥</span>
            <span class="menu-item-text">账号权限管理</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)"
               class="menu-item"
               :class="{ active: $route.path === '/dashboard' }"
               @click="$router.push('/dashboard')">
            <span class="menu-item-icon">📊</span>
            <span class="menu-item-text">运行仪表盘</span>
          </div>

          <div v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)"
               class="menu-item"
               :class="{ active: $route.path === '/table-manager' }"
               @click="$router.push('/table-manager')">
            <span class="menu-item-icon">🗂️</span>
            <span class="menu-item-text">表格大盘管理</span>
          </div>

          <div v-if="globalStore.auth.role === 'teacher'"
               class="menu-item"
               :class="{ active: $route.path === '/teacher' }"
               @click="$router.push('/teacher')">
            <span class="menu-item-icon">📝</span>
            <span class="menu-item-text">老师模板设置</span>
          </div>

          <div v-if="globalStore.auth.role !== 'admin'"
               class="menu-item"
               :class="{ active: $route.path === '/student' }"
               @click="$router.push('/student')">
            <span class="menu-item-icon">📤</span>
            <span class="menu-item-text">学生作业代交</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)"
               class="menu-item"
               :class="{ active: $route.path === '/grading' }"
               @click="$router.push('/grading')">
            <span class="menu-item-icon">✅</span>
            <span class="menu-item-text">智能作业批改</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)"
               class="menu-item"
               :class="{ active: $route.path === '/analytics' }"
               @click="$router.push('/analytics')">
            <span class="menu-item-icon">📈</span>
            <span class="menu-item-text">学情分析大屏</span>
          </div>

          <div v-if="['teacher', 'web_teacher'].includes(globalStore.auth.role)"
               class="menu-item"
               :class="{ active: $route.path === '/grades' }"
               @click="$router.push('/grades')">
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
          <button class="btn-logout" @click="handleLogoutAction">退出登录</button>
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
                 @click="useBitable(item)">
              <span class="tab-icon">📊</span>
              <span class="tab-name" :title="item.name">{{ item.name }}</span>
              <div class="tab-actions">
                <button class="tab-btn" @click.stop="openBitableLink(item)" title="在浏览器打开多维表格">🌐</button>
                <button class="tab-btn tab-delete" @click.stop="unpinTab(item)" title="从顶栏取消固定">✕</button>
              </div>
            </div>
          </div>

          <button v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)"
                  class="btn-toggle-panel" @click="isConfigOpen = !isConfigOpen">
            <span v-if="isConfigOpen">⚙️ 收起参数底盘 ➡️</span>
            <span v-else>⬅️ 展开参数底盘 ⚙️</span>
          </button>
          <SyncStatusBadge v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)" />
          <div v-else class="student-header-hint">欢迎来到作业提交系统，请上传清晰的作业图片！</div>
        </div>

        <div class="workspace-content">
          <transition name="fade-slide" mode="out-in">
            <router-view v-slot="{ Component }">
              <keep-alive :max="3">
                <component :is="Component" />
              </keep-alive>
            </router-view>
          </transition>
        </div>
      </main>

      <aside v-if="['teacher', 'web_teacher', 'admin'].includes(globalStore.auth.role)"
             class="sidebar-right" :class="{ 'is-collapsed': !isConfigOpen }">
        <div class="config-header">
          <div>
            <span class="config-kicker">Control Center</span>
            <h3><span class="config-header-icon">⚙️</span> 参数配置中心</h3>
          </div>
        </div>

        <div class="config-body">
          <div class="status-overview">
            <div class="status-hero">
              <span class="status-hero-icon">{{ feishuReady && aiReady ? '✅' : '⚡' }}</span>
              <div>
                <strong>{{ feishuReady && aiReady ? '核心服务已就绪' : '仍有配置待完成' }}</strong>
                <p>{{ activeTableName }}</p>
              </div>
            </div>
            <div class="status-grid">
              <div v-for="item in configHealthItems" :key="item.label" class="status-chip" :class="item.ready ? 'is-ready' : 'is-warn'">
                <span>{{ item.icon }}</span>
                <div>
                  <small>{{ item.label }}</small>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
            </div>
          </div>

          <div class="config-card">
            <div class="config-section-title">
              <span>🧠</span>
              <div>
                <strong>大模型服务配置</strong>
                <small>控制 AI 批改、ChatBI 与视觉诊断能力</small>
              </div>
            </div>
            <div class="form-group">
              <label>选择 AI 大模型</label>
              <select v-model="globalStore.config.model">
                <option v-for="model in modelOptions" :key="model.value" :value="model.value">{{ model.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>模型 API Key</label>
              <input type="password" v-model="globalStore.config.apiKey" placeholder="输入 sk-..." />
              <p class="field-hint">仅显示配置状态，不在面板摘要中展示密钥内容。</p>
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
            <div class="config-section-title">
              <span>📑</span>
              <div>
                <strong>飞书开放平台接入</strong>
                <small>连接多维表格，承载作业提交与学情数据</small>
              </div>
            </div>
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
              <p class="field-hint">当前工作表：{{ activeTableName }}</p>
            </div>
          </div>

          <button class="btn-save" @click="saveGlobalConfig" :disabled="savingConfig">
            <span class="save-icon">{{ savingConfig ? '⏳' : '💾' }}</span>
            {{ savingConfig ? '保存中...' : '缓存并应用全局配置' }}
          </button>
        </div>
      </aside>
    </div>
  </template>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { globalStore, saveConfig } from './store';
import syncCenter from './services/syncCenter';
import ViewStudent from './components/views/ViewStudent.vue';
import ViewLogin from './components/views/ViewLogin.vue';
import SyncStatusBadge from './components/SyncStatusBadge.vue';

const route = useRoute();
const isGuestMode = ref(!!new URLSearchParams(window.location.search).get('invite'));
const isConfigOpen = ref(true);
const savingConfig = ref(false);

const modelOptions = [
  { value: 'doubao-seed-2-0-pro-260215', label: '火山豆包 2.0 Pro (多模态批改)' },
  { value: 'doubao-seed-2-0-mini-260428', label: '火山豆包 2.0 Mini (极速视觉模型)' },
  { value: 'doubao-seed-2-0-lite-260428', label: '火山豆包 2.0 Lite (轻量视觉模型)' },
  { value: 'deepseek-chat', label: 'DeepSeek-V3 (标准文本模型)' },
  { value: 'deepseek-reasoner', label: 'DeepSeek-R1 (深度思考模型)' },
];

const pinnedTables = computed(() => {
  if (!globalStore.config.bitableList) return [];
  return globalStore.config.bitableList.filter(item =>
    item.isPinned !== false && (globalStore.auth.role === 'admin' || item.ownerId === globalStore.auth.userId)
  );
});

const activeTable = computed(() => {
  const list = globalStore.config.bitableList || [];
  return list.find(item => item.token === globalStore.config.feishuToken) || null;
});

const activeTableName = computed(() => {
  if (activeTable.value?.name) return activeTable.value.name;
  if (globalStore.config.feishuToken) return '已绑定外部飞书表格';
  return '尚未选择工作表';
});

const feishuReady = computed(() => Boolean(globalStore.config.feishuAppId && globalStore.config.feishuAppSecret));
const aiReady = computed(() => Boolean(globalStore.config.apiKey));
const currentModelLabel = computed(() => modelOptions.find(item => item.value === globalStore.config.model)?.label || '未选择模型');

const configHealthItems = computed(() => [
  { icon: '📑', label: '飞书接入', value: feishuReady.value ? '已配置' : '待配置', ready: feishuReady.value },
  { icon: '🗂️', label: '当前表格', value: globalStore.config.feishuToken ? '已绑定' : '未绑定', ready: Boolean(globalStore.config.feishuToken) },
  { icon: '🧠', label: 'AI Key', value: aiReady.value ? '已配置' : '待配置', ready: aiReady.value },
  { icon: '⚙️', label: '当前模型', value: currentModelLabel.value.replace(/\s*\(.+\)/, ''), ready: Boolean(globalStore.config.model) },
]);

const currentViewTitle = computed(() => {
  const titles = {
    '/account-manager': '👥 全局教职工账号管理',
    '/table-manager': '🗂️ 班级表格大盘管理',
    '/dashboard': '运行仪表盘',
    '/teacher': '老师模板设置',
    '/student': '学生作业同步',
    '/grading': '智能作业批改',
    '/analytics': '学情分析大屏',
    '/grades': '学生成绩档案中心',
  };
  return titles[route.path] || '工作台';
});

const saveGlobalConfig = async () => {
  savingConfig.value = true;
  const result = await saveConfig();
  savingConfig.value = false;
  if (result.success) {
    alert('✅ 底层凭证及并发策略参数应用成功！');
  } else {
    alert('⚠️ 配置缓存已保存（后端持久化不可用，已降级到本地存储）');
  }
};

const handleLogoutAction = () => { globalStore.auth = { isLoggedIn: false, role: '', username: '', userId: '', subject: '', token: '' }; };
const useBitable = (item) => {
  globalStore.config.feishuToken = item.token;
  syncCenter.onTableSwitch(item.token);
};
const openBitableLink = (item) => { if (item.token) window.open(`https://www.feishu.cn/base/${item.token}`, '_blank'); };
const unpinTab = (item) => { item.isPinned = false; };

const quickPrompts = ['严格扣分：无过程不得分', '忽略轻微错别字', '注重鼓励：多用赞美语气', '重点检查：漏写单位扣半分布'];
const appendPrompt = (tag) => {
  let current = globalStore.config.customPrompt || '';
  if (current.includes(tag)) return;
  globalStore.config.customPrompt = current.trim() === '' ? tag : current.trim() + '，' + tag;
};
</script>

<style>
:root {
  --edu-primary: #2563eb;
  --edu-primary-dark: #4f46e5;
  --edu-primary-soft: #eff6ff;
  --edu-success: #10b981;
  --edu-warning: #f59e0b;
  --edu-danger: #ef4444;
  --edu-text: #0f172a;
  --edu-muted: #64748b;
  --edu-border: #e2e8f0;
  --edu-card: rgba(255, 255, 255, 0.88);
  --edu-radius: 16px;
  --edu-radius-lg: 22px;
  --edu-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
  --edu-shadow-soft: 0 6px 18px rgba(15, 23, 42, 0.05);
}

html, body {
  margin: 0; padding: 0; height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #eef4ff; overflow: hidden;
  color: var(--edu-text);
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
.guest-fullscreen-layout {
  width: 100vw; height: 100vh; overflow-y: auto;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  display: flex; justify-content: center; align-items: flex-start;
  padding: 40px 20px; box-sizing: border-box;
}

.dashboard-layout {
  display: flex; height: 100vh; width: 100vw; overflow: hidden;
  background:
    radial-gradient(circle at 22% 12%, rgba(37, 99, 235, 0.12), transparent 28%),
    radial-gradient(circle at 75% 0%, rgba(124, 58, 237, 0.10), transparent 24%),
    linear-gradient(135deg, #eef4ff 0%, #f8fbff 42%, #eef2ff 100%);
}

.sidebar-left {
  width: 260px; background: linear-gradient(180deg, #0f172a 0%, #111827 48%, #020617 100%);
  color: #f3f4f6; display: flex; flex-direction: column;
  flex-shrink: 0; z-index: 11; border-right: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 12px 0 30px rgba(15, 23, 42, 0.12);
}
.logo-area { height: 76px; display: flex; align-items: center; padding: 0 22px; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
.logo-wrapper { display: flex; align-items: center; gap: 12px; }
.logo-icon {
  width: 38px; height: 38px; display: grid; place-items: center;
  border-radius: 13px; background: linear-gradient(135deg, #fff 0%, #dbeafe 100%);
  color: #1d4ed8; font-weight: 900; font-size: 22px;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
}
.logo-title-group { display: flex; flex-direction: column; gap: 2px; }
.logo-area h1.logo-text { font-size: 17px; margin: 0; font-weight: 800; letter-spacing: 1px;
  background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.logo-subtitle { font-size: 10px; color: #93c5fd; font-weight: 800; letter-spacing: 1.8px; text-transform: uppercase; }
.menu-list { padding: 24px 12px; display: flex; flex-direction: column; gap: 6px; flex: 1; overflow-y: auto;}

.menu-item { padding: 12px 16px; cursor: pointer; color: #a8b3c7; font-size: 14px;
  font-weight: 650; border-radius: 12px; display: flex; align-items: center; gap: 12px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.menu-item-icon { font-size: 16px; width: 20px; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
.menu-item-text { letter-spacing: 0.3px; }
.menu-item:hover { color: #ffffff; background-color: rgba(255, 255, 255, 0.07); transform: translateX(2px); }
.menu-item:hover .menu-item-icon { transform: scale(1.15); }
.menu-item.active { background: linear-gradient(135deg, var(--edu-primary) 0%, var(--edu-primary-dark) 100%);
  color: #ffffff; font-weight: 800; box-shadow: 0 10px 24px rgba(37, 99, 235, 0.26); }

.user-profile { padding: 16px; margin: 12px; border-radius: var(--edu-radius);
  background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex; flex-direction: column; gap: 12px; }
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar { font-size: 18px; background: rgba(255, 255, 255, 0.08);
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%; border: 1px solid rgba(255, 255, 255, 0.12); }
.user-meta { display: flex; flex-direction: column; overflow: hidden; }
.user-name { font-size: 14px; font-weight: 700; color: #ffffff; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis;}
.user-sub { font-size: 11px; color: #60a5fa; font-weight: 700; margin-top: 2px; }

.btn-logout { background: rgba(255,255,255,0.05); color: #cbd5e1; border: 1px solid rgba(255,255,255,0.08);
  padding: 9px; border-radius: 10px; cursor: pointer; font-size: 12px; font-weight: 700; transition: all 0.2s;}
.btn-logout:hover { background: rgba(239, 68, 68, 0.13); color: #fca5a5; border-color: rgba(239, 68, 68, 0.32); }

.main-workspace { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.workspace-header { height: 76px; background: rgba(255,255,255,0.86); backdrop-filter: blur(18px); display: flex; align-items: center;
  padding: 0 24px; box-shadow: 0 1px 0 rgba(226, 232, 240, 0.8); border-bottom: 1px solid rgba(226,232,240,0.75);
  z-index: 10; flex-shrink: 0; gap: 24px; }
.header-title { margin: 0; font-size: 17px; color: var(--edu-text); font-weight: 900; white-space: nowrap; flex-shrink: 0; }

.header-table-tabs { flex: 1; display: flex; align-items: center; gap: 10px; overflow-x: auto; height: 100%; scrollbar-width: none; }
.header-table-tabs::-webkit-scrollbar { display: none; }
.empty-tab-hint { font-size: 13px; color: #94a3b8; font-weight: 600; font-style: italic; }
.table-tab { display: flex; align-items: center; gap: 6px; padding: 0 8px 0 14px; height: 38px;
  background: rgba(255,255,255,0.78); border: 1px solid var(--edu-border); border-radius: 999px; cursor: pointer;
  transition: all 0.2s; flex-shrink: 0; box-shadow: var(--edu-shadow-soft); }
.table-tab:hover { border-color: #bfdbfe; background: #fff; transform: translateY(-1px); }
.table-tab.is-active { background: var(--edu-primary-soft); border-color: #3b82f6; box-shadow: 0 8px 18px rgba(37,99,235,0.12); }
.tab-name { font-size: 13px; font-weight: 650; color: #475569; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.table-tab.is-active .tab-name { color: #2563eb; font-weight: 900; }
.tab-actions { display: flex; align-items: center; }
.tab-btn { background: transparent; border: none; cursor: pointer; font-size: 12px;
  opacity: 0.55; padding: 0; width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; transition: 0.2s; }
.tab-btn:hover { opacity: 1; background: rgba(0,0,0,0.05); }
.tab-btn.tab-delete:hover { background: #fee2e2; color: #ef4444; }

.btn-toggle-panel { flex-shrink: 0; background: #fff; border: 1px solid var(--edu-border);
  padding: 9px 16px; border-radius: 999px; cursor: pointer; color: #475569; font-size: 13px; font-weight: 800; box-shadow: var(--edu-shadow-soft); }
.btn-toggle-panel:hover { color: var(--edu-primary); border-color: #93c5fd; background-color: var(--edu-primary-soft); box-shadow: 0 8px 18px rgba(37,99,235,0.12); }
.student-header-hint { font-size: 14px; color: #16a34a; font-weight: bold; }

.workspace-content { flex: 1; padding: 24px; overflow-y: auto; box-sizing: border-box; }
:deep(.view-container) { background-color: #fff; padding: 24px; border-radius: var(--edu-radius);
  box-shadow: var(--edu-shadow-soft); min-height: 100%; box-sizing: border-box; border: 1px solid rgba(226, 232, 240, 0.8); }

.sidebar-right {
  width: 370px; background: rgba(248, 250, 252, 0.92); border-left: 1px solid rgba(226,232,240,0.86);
  display: flex; flex-direction: column; box-shadow: -16px 0 34px rgba(15, 23, 42, 0.06);
  z-index: 10; flex-shrink: 0; transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1), border-left 0.3s ease;
  overflow: hidden; backdrop-filter: blur(18px);
}
.sidebar-right.is-collapsed { width: 0; border-left: none; }
.config-header, .config-body { width: 370px; box-sizing: border-box; }
.config-header {
  height: 76px; display: flex; align-items: center; padding: 0 24px;
  border-bottom: 1px solid rgba(226,232,240,0.82); background: rgba(255,255,255,0.8); flex-shrink: 0;
}
.config-header h3 { margin: 2px 0 0; font-size: 17px; font-weight: 900; color: var(--edu-text); display: flex; align-items: center; gap: 8px; }
.config-kicker { font-size: 11px; color: #3b82f6; font-weight: 900; letter-spacing: 1.6px; text-transform: uppercase; }
.config-header-icon { font-size: 18px; }
.config-body { padding: 22px; overflow-y: auto; flex: 1; }

.status-overview { background: linear-gradient(135deg, #1d4ed8 0%, #4f46e5 58%, #7c3aed 100%); color: #fff; border-radius: 22px; padding: 18px; margin-bottom: 18px; box-shadow: 0 18px 38px rgba(79, 70, 229, 0.24); }
.status-hero { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.status-hero-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 14px; background: rgba(255,255,255,0.16); font-size: 20px; }
.status-hero strong { display: block; font-size: 15px; }
.status-hero p { margin: 4px 0 0; color: rgba(255,255,255,0.76); font-size: 12px; font-weight: 650; }
.status-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.status-chip { display: flex; gap: 8px; align-items: center; padding: 10px; border-radius: 14px; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.14); min-width: 0; }
.status-chip small { display: block; color: rgba(255,255,255,0.66); font-size: 10px; font-weight: 800; }
.status-chip strong { display: block; font-size: 12px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.status-chip.is-ready span { filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.5)); }
.status-chip.is-warn span { filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.5)); }

.config-card { background: var(--edu-card); border: 1px solid rgba(226,232,240,0.9); border-radius: 20px;
  padding: 20px; margin-bottom: 18px; box-shadow: var(--edu-shadow-soft); backdrop-filter: blur(12px); }
.config-section-title { font-size: 14px; font-weight: 800; color: #1e293b; margin-bottom: 18px; display: flex; align-items: flex-start; gap: 10px; }
.config-section-title span { font-size: 20px; }
.config-section-title strong { display: block; }
.config-section-title small { display: block; margin-top: 3px; color: #94a3b8; font-size: 11px; font-weight: 700; line-height: 1.4; }
.form-group { margin-bottom: 18px; }
.form-group:last-child { margin-bottom: 0; }
.form-group label { display: block; margin-bottom: 8px; font-size: 12px; color: #64748b;
  font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 11px 14px; border: 1.5px solid #dbe4f0; border-radius: 12px;
  font-size: 13px; color: #0f172a; font-weight: 650; box-sizing: border-box; transition: all 0.25s ease;
  background-color: #f8fafc;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  outline: none; border-color: #3b82f6; background-color: #fff; box-shadow: 0 0 0 4px rgba(59,130,246,0.12);
}
.field-hint { margin: 8px 0 0; font-size: 11px; color: #94a3b8; line-height: 1.45; }
.quick-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.tag-btn { font-size: 11px; font-weight: 700; color: #2563eb; background: #eff6ff;
  padding: 6px 10px; border-radius: 999px; border: 1px solid #bfdbfe; cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.tag-btn:hover { background: #dbeafe; border-color: #93c5fd; transform: translateY(-1px); }
.tag-btn.tag-clear { color: #ef4444; background: #fef2f2; border-color: #fecaca; }
.tag-btn.tag-clear:hover { background: #fee2e2; border-color: #f87171; }

.btn-save {
  width: 100%; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #fff;
  border: none; padding: 15px 16px; border-radius: 16px; font-size: 14px; font-weight: 900;
  cursor: pointer; transition: all 0.3s ease; box-shadow: 0 12px 26px rgba(16, 185, 129, 0.24);
  display: flex; justify-content: center; align-items: center; gap: 8px;
}
.btn-save:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 18px 34px rgba(16, 185, 129, 0.34); }
.btn-save:disabled { background: #94a3b8; cursor: not-allowed; box-shadow: none; }
.save-icon { font-size: 16px; }
</style>
