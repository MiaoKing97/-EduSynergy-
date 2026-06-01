<template>
  <div class="account-manager">
    <div class="header">
      <div class="title">
        <h3>👥 全局教职工账号管理</h3>
        <p>系统超级管理员专属视图。支持新增教职工、重置密码及身份分配。</p>
      </div>
      <button class="btn-add" @click="addUser">➕ 新增教职工</button>
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
          <td><input v-model="user.username" class="edit-input" :disabled="user.role==='admin'"/></td>
          <td><input v-model="user.password" class="edit-input" placeholder="设置密码"/></td>

          <td>
            <span v-if="user.role === 'admin'" class="role-badge admin">超级管理员</span>
            <!-- 🌟 将下拉框绑定到 subject，并通过 change 事件自动同步底层 role 权限 -->
            <select v-else v-model="user.subject" class="edit-select" @change="syncRole(user)">
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

// 🌟 核心逻辑：下拉框改变时，智能分配底层路由和菜单权限
const syncRole = (user) => {
  // 只要选择了网页设计，就赋予专属的 web_teacher 角色，其余统一为 teacher
  if (user.subject === '网页设计') {
    user.role = 'web_teacher';
  } else {
    user.role = 'teacher';
  }
};

const addUser = () => {
  const uid = 'u_teacher_' + Math.floor(Math.random() * 10000);
  // 新增账号时，提供一个默认值（例如高数老师）
  globalStore.users.push({
    id: uid,
    username: '新老师',
    password: '123',
    role: 'teacher',
    subject: '高等数学'
  });
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

.edit-select { border: 1px solid transparent; padding: 6px 8px; border-radius: 4px; background: #fafafa; outline: none; transition: 0.2s; font-size: 13px; color: #333; cursor: pointer;}
.edit-select:focus { border-color: #1890ff; background: #fff; border: 1px solid #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.1);}

.role-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;}
.role-badge.admin { background: #fff1f0; color: #f5222d; border: 1px solid #ffa39e;}

.btn-del { background: #ff4d4f; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: 0.2s;}
.btn-del:hover { background: #ff7875; }

.text-muted { font-size: 12px; color: #ccc; }
</style>