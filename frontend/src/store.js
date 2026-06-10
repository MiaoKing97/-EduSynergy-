import { reactive, watch } from 'vue';

// ─── Helpers ───
const loadCache = (key, defaultVal) => {
  try {
    const data = localStorage.getItem(key);
    if (data && data !== 'undefined' && data !== 'null') {
      return JSON.parse(data);
    }
  } catch (e) {
    console.error(`❌ 解析本地缓存 [${key}] 失败`, e);
  }
  return defaultVal;
};

const saveCache = (key, value) => {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn('❌ localStorage 容量已满，跳过保存:', key);
  }
};

// ─── Default data ───
const defaultUsers = [
  { id: 'u_admin', username: 'Admin', password: '123', role: 'admin', subject: '全局管理' },
  { id: 'u_math1', username: '张老师', password: '123', role: 'teacher', subject: '高等数学' },
  { id: 'u_math2', username: '王老师', password: '123', role: 'teacher', subject: '高等数学' },
  { id: 'u_c1', username: '李老师', password: '123', role: 'teacher', subject: 'C语言' },
  { id: 'u_c2', username: '赵老师', password: '123', role: 'teacher', subject: 'C语言' },
  { id: 'u_web1', username: '陈老师', password: '123', role: 'web_teacher', subject: '网页设计' },
  { id: 'u_web2', username: '林老师', password: '123', role: 'web_teacher', subject: '网页设计' },
];

// ─── Reactive store ───
export const globalStore = reactive({
  auth: loadCache('ai_assistant_auth', {
    isLoggedIn: false, role: '', username: '', userId: '', subject: '', token: '',
  }),
  config: loadCache('ai_assistant_config', {
    feishuAppId: '', feishuAppSecret: '', feishuToken: '', feishuTableId: '',
    apiKey: '', model: 'doubao-seed-2-0-pro-260215',
    systemPrompt: '', customPrompt: '', concurrency: 1,
  }),
  users: loadCache('ai_assistant_users', defaultUsers),
  tableDataCache: {},
  sync: {
    loading: false,        // 当前是否正在同步
    lastSyncAt: '',        // 全局最近一次成功同步的 ISO 时间
    error: '',             // 最近一次同步错误（空表示无错）
    currentToken: '',      // 最近一次同步对应的 token
    inflight: {},          // { [token]: Promise } —— 同 token 并发请求去重
  },
});

// Auto-save on deep mutation
watch(globalStore, (newVal) => {
  saveCache('ai_assistant_auth', newVal.auth);
  saveCache('ai_assistant_config', newVal.config);
  saveCache('ai_assistant_users', newVal.users);
}, { deep: true });

// ─── Cache helpers ───
export const clearTableCache = (token) => {
  if (!token) return;
  delete globalStore.tableDataCache[token];
  delete globalStore.tableDataCache[token + '_grades'];
};

// ─── Auth actions (separate to avoid reactive proxy issues) ───
export const login = async (username, password) => {
  try {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || '登录失败');

    globalStore.auth = {
      isLoggedIn: true, role: data.role, username: data.username,
      userId: data.username, subject: data.subject, token: data.access_token,
    };
    return { success: true };
  } catch (e) {
    return { success: false, error: e.message };
  }
};

export const logout = () => {
  globalStore.auth = { isLoggedIn: false, role: '', username: '', userId: '', subject: '', token: '' };
};

export const saveConfig = async () => {
  try {
    await fetch('/api/auth/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${globalStore.auth.token}`,
      },
      body: JSON.stringify(globalStore.config),
    });
    return { success: true };
  } catch (e) {
    console.warn('Config save degraded to localStorage:', e);
    return { success: false, error: e.message };
  }
};
