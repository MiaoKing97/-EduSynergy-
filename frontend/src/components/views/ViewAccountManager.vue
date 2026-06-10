<template>
  <div class="account-manager">
    <div class="header">
      <div class="title">
        <h3>👥 全局教职工账号管理</h3>
        <p>系统超级管理员专属视图。支持新增教职工、重置密码及身份分配。</p>
      </div>
      <div style="display:flex;gap:8px">
        <button class="btn-add" @click="addUser">➕ 新增教职工</button>
      </div>
    </div>

    <table class="styled-table">
      <thead>
        <tr>
          <th>UID</th>
          <th>账号名称</th>
          <th>登录密码</th>
          <th>身份角色</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(user, index) in globalStore.users" :key="user.id">
          <td class="uid">{{ user.id }}</td>
          <td><input v-model="user.username" class="edit-input" :disabled="user.role==='admin'" @change="syncUser(user)"/></td>
          <td style="display:flex;align-items:center;gap:2px">
            <input v-if="!showPasswords[user.id]" value="••••••" class="edit-input pwd-masked" readonly style="cursor:pointer" @click="togglePasswordShow(user)" />
            <input v-else v-model="user.password" class="edit-input" placeholder="设置密码" @input="syncPasswordCache(user)" @change="syncUser(user)" />
            <button class="btn-reveal" @click="togglePasswordShow(user)" title="点击查看/隐藏密码">
              {{ showPasswords[user.id] ? '🙈' : '👁️' }}
            </button>
          </td>

          <td>
            <span v-if="user.role === 'admin'" class="role-badge admin">超级管理员</span>
            <!-- 🌟 将下拉框绑定到 subject，并通过 change 事件自动同步底层 role 权限 -->
            <select v-else v-model="user.subject" class="edit-select" @change="syncRole(user); syncUser(user)">
              <option value="网页设计">💻 网页设计老师</option>
              <option value="高等数学">📐 高数老师</option>
              <option value="C语言程序设计">⌨️ C语言程序设计老师</option>
              <option value="英语">🌍 英语老师</option>
            </select>
          </td>

          <td>
            <button v-if="user.role !== 'admin'" class="btn-del" @click="deleteUser(index)">删除</button>
            <span v-else class="text-muted">不可操作</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { globalStore } from '../../store';
import { onMounted, reactive } from 'vue';

// 🌟 从后端拉取最新用户列表
const fetchUsers = async () => {
  try {
    const resp = await fetch('/api/auth/users');
    if (!resp.ok) {
      console.warn('Failed to fetch users:', resp.status);
      return;
    }
    const backendUsers = await resp.json();
    globalStore.users = backendUsers.map(u => ({
      id: u.id,
      username: u.username,
      password: '', // 密码不可逆，前端不显示
      role: u.role,
      subject: u.subject,
    }));
  } catch (e) {
    console.warn('Failed to fetch users:', e.message);
  }
};

// 登录时自动拉取一次
onMounted(fetchUsers);

// 🌟 核心逻辑：下拉框改变时，智能分配底层路由和菜单权限
const syncRole = (user) => {
  // 只要选择了网页设计，就赋予专属的 web_teacher 角色，其余统一为 teacher
  if (user.subject === '网页设计') {
    user.role = 'web_teacher';
  } else {
    user.role = 'teacher';
  }
};

// 🌟 密码显示控制 — 密码持久化到 localStorage
const PWD_CACHE_KEY = 'account_mgr_cached_passwords';

const loadCachedPasswords = () => {
  try {
    const raw = localStorage.getItem(PWD_CACHE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

const saveCachedPasswords = (cached) => {
  try {
    localStorage.setItem(PWD_CACHE_KEY, JSON.stringify(cached));
  } catch {}
};

const cachedPasswords = loadCachedPasswords();

const showPasswords = reactive({});

const togglePasswordShow = (user) => {
  showPasswords[user.id] = !showPasswords[user.id];
  if (showPasswords[user.id]) {
    // 有缓存就用缓存，无缓存则留空让用户首次输入
    user.password = cachedPasswords[user.id] || '';
  } else {
    // 关闭明文显示时，更新缓存
    syncPasswordCache(user);
  }
};

const syncPasswordCache = (user) => {
  // 当用户修改了密码时，更新缓存
  if (user.password && user.password.trim()) {
    cachedPasswords[user.id] = user.password;
    saveCachedPasswords(cachedPasswords);
  }
};

const addUser = async () => {
  const uid = 'u_teacher_' + Math.floor(Math.random() * 10000);
  try {
    const resp = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: '新老师',
        password: '123',
        role: 'teacher',
        subject: '高等数学',
      }),
    });
    if (!resp.ok) {
      const err = await resp.json();
      alert('❌ 创建失败: ' + (err.detail || '未知错误'));
      return;
    }
    const result = await resp.json();
    // 同步后端返回的真实信息
    globalStore.users.push({
      id: uid,
      username: result.username,
      password: '',
      role: result.role,
      subject: result.subject
    });
    // 同步后刷新列表，拿到最新数据
    await fetchUsers();
  } catch (e) {
    alert('❌ 网络错误: ' + e.message);
  }
};

const syncUser = async (user) => {
  if (!user.username) return;
  try {
    const body = {
      username: user.username,
      role: user.role,
      subject: user.subject,
    };
    // 只有用户主动输入了新密码时才更新
    if (user.password && user.password.trim()) {
      body.password = user.password;
      syncPasswordCache(user);
    }
    if (user.id && user.id.startsWith('u_')) {
      body.id = user.id;
    }
    console.log('syncUser calling:', body);
    const resp = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    console.log('syncUser response:', resp.status);
    if (!resp.ok) {
      const err = await resp.json();
      console.warn('User sync failed:', err);
    }
  } catch (e) {
    console.warn('User sync failed:', e.message);
  }
};

const deleteUser = (index) => {
  if (confirm("确定要删除该老师账号吗？该操作会自动生效，不可撤销！")) {
    globalStore.users.splice(index, 1);
  }
};
</script>

<style scoped>
.account-manager { padding: 20px; background: #fff; border-radius: 8px; border: 1px solid #ebeef5;}
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #eee; padding-bottom: 16px;}
.title h3 { margin: 0 0 6px 0; }
.title p { margin: 0; font-size: 13px; color: #888; }
.btn-add { background: #1890ff; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; transition: 0.2s;}
.btn-add:hover { background: #40a9ff; transform: translateY(-1px);}

.styled-table { width: 100%; border-collapse: collapse; text-align: left; }
.styled-table th { background: #f4f5f7; padding: 12px; font-size: 13px; color: #666; }
.styled-table td { padding: 12px; border-bottom: 1px solid #eee; }

.uid { font-family: monospace; color: #999; font-size: 12px; }

.edit-input { border: 1px solid transparent; padding: 6px 8px; border-radius: 4px; background: #fafafa; outline: none; transition: 0.2s; width: 120px; font-size: 13px;}
.edit-input:focus { border-color: #1890ff; background: #fff; box-shadow: 0 0 0 2px rgba(24,144,255,0.1);}
.edit-input:disabled { background: transparent; color: #333; font-weight: bold; }
.edit-input.pwd-masked { font-family: 'Courier New', monospace; letter-spacing: 2px; text-align: center; background: #fffbe6; border: 1px solid #ffe58f; color: #d48806; font-weight: 600; cursor: pointer; }
.edit-input.pwd-masked:hover { background: #fff1b0; border-color: #ffd666; }
.btn-reveal { background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px 2px; width: 28px; height: 28px; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; transition: 0.2s; }
.btn-reveal:hover { background: #f0f0f0; }

.edit-select { border: 1px solid transparent; padding: 6px 8px; border-radius: 4px; background: #fafafa; outline: none; transition: 0.2s; font-size: 13px; color: #333; cursor: pointer;}
.edit-select:focus { border-color: #1890ff; background: #fff; border: 1px solid #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.1);}

.role-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;}
.role-badge.admin { background: #fff1f0; color: #f5222d; border: 1px solid #ffa39e;}

.btn-del { background: #ff4d4f; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: 0.2s;}
.btn-del:hover { background: #ff7875; }

.text-muted { font-size: 12px; color: #ccc; }
</style>