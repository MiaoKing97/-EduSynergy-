import { reactive, watch } from 'vue';

// 封装本地存储读取器 (自带防崩溃机制)
const loadCache = (key, defaultVal) => {
  try {
    const data = localStorage.getItem(key);
    if (data && data !== 'undefined' && data !== 'null') {
      return JSON.parse(data);
    }
    return defaultVal;
  } catch (e) {
    console.error(`❌ 解析本地缓存 [${key}] 失败，已恢复默认值:`, e);
    return defaultVal;
  }
};

// 默认教职工大名单
const defaultUsers = [
  { id: 'u_admin', username: 'Admin', password: '123', role: 'admin', subject: '全局管理' },
  { id: 'u_math1', username: '张老师', password: '123', role: 'teacher', subject: '高等数学' },
  { id: 'u_math2', username: '王老师', password: '123', role: 'teacher', subject: '高等数学' },
  { id: 'u_c1', username: '李老师', password: '123', role: 'teacher', subject: 'C语言' },
  { id: 'u_c2', username: '赵老师', password: '123', role: 'teacher', subject: 'C语言' },
  { id: 'u_web1', username: '陈老师', password: '123', role: 'web_teacher', subject: '网页设计' },
  { id: 'u_web2', username: '林老师', password: '123', role: 'web_teacher', subject: '网页设计' }
];

// 初始化全局响应式状态库
export const globalStore = reactive({
  auth: loadCache('ai_assistant_auth', {
    isLoggedIn: false,
    role: '',
    username: '',
    userId: '',
    subject: ''
  }),
  config: loadCache('ai_assistant_config', {
    feishuAppId: '', feishuAppSecret: '', feishuToken: '', feishuTableId: '',
    apiKey: '', model: 'doubao-seed-2-0-pro-260215',
    systemPrompt: '', customPrompt: '', concurrency: 1
  }),
  users: loadCache('ai_assistant_users', defaultUsers),

  // 🌟 核心修复：增加这个内存级的表格数据缓存对象，防止页面读取时报错崩溃！
  tableDataCache: {}
});

// 深度监听：自动保存到本地缓存
watch(globalStore, (newVal) => {
  try {
    localStorage.setItem('ai_assistant_auth', JSON.stringify(newVal.auth));
    localStorage.setItem('ai_assistant_config', JSON.stringify(newVal.config));
    localStorage.setItem('ai_assistant_users', JSON.stringify(newVal.users));
    // 注意：tableDataCache 属于页面临时提速缓存，不需要存入硬盘
  } catch (e) {
    console.error('❌ 保存本地缓存失败:', e);
  }
}, { deep: true });