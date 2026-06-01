<template>
  <div class="login-container">
    <div class="login-box">
      <h2>🤖 AI 教务内部后台登录</h2>

      <div class="form-area">
        <div class="select-wrapper">
          <select v-model="selectedSubject" class="styled-select" @change="selectedUsername = ''">
            <option value="" disabled>请选择您的教研组 / 身份</option>
            <option v-for="sub in availableSubjects" :key="sub.name" :value="sub.name">
              {{ sub.icon }} {{ sub.name }}
            </option>
          </select>
        </div>

        <div v-if="selectedSubject" class="select-wrapper slide-down">
          <select v-model="selectedUsername" class="styled-select account-select">
            <option value="" disabled>请选择您的专属账号</option>
            <option v-for="acc in availableAccounts" :key="acc.id" :value="acc.username">
              🧑‍🏫 {{ acc.username }}
            </option>
          </select>
        </div>

        <input
          v-model="password"
          type="password"
          placeholder="请输入系统密码 (默认: 123)"
          @keyup.enter="handleLogin"
        />
        <button class="btn-login" @click="handleLogin">系统登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { globalStore } from '../../store';

const password = ref('');
const selectedSubject = ref('');
const selectedUsername = ref('');

const availableSubjects = computed(() => {
  const map = new Map();
  globalStore.users.forEach(u => {
    if (['admin', 'teacher', 'web_teacher'].includes(u.role)) {
      if (!map.has(u.subject)) {
        let icon = '📚';
        if (u.subject.includes('网页')) icon = '🎨';
        else if (u.subject.includes('管理')) icon = '⚙️';
        else if (u.subject.includes('数学')) icon = '📐';
        else if (u.subject.includes('C语言') || u.subject.includes('编程')) icon = '💻';
        else if (u.subject.includes('英语')) icon = '🌍';
        map.set(u.subject, { name: u.subject, icon: icon });
      }
    }
  });
  return Array.from(map.values());
});

const availableAccounts = computed(() => {
  if (!selectedSubject.value) return [];
  return globalStore.users.filter(u => u.subject === selectedSubject.value);
});

const handleLogin = () => {
  if (!selectedSubject.value) return alert("⚠️ 请先选择教研组/身份！");
  if (!selectedUsername.value) return alert("⚠️ 请选择您的专属账号！");
  if (!password.value) return alert("⚠️ 请输入密码！");

  const user = globalStore.users.find(u =>
    u.subject === selectedSubject.value &&
    u.username === selectedUsername.value &&
    u.password === password.value
  );

  if (user) {
    globalStore.auth = {
      isLoggedIn: true, role: user.role, username: user.username,
      userId: user.id, subject: user.subject
    };
  } else {
    alert("❌ 密码错误，请重试！");
  }
};
</script>

<style scoped>
.login-container { height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f0f4fd 0%, #e0e9fa 100%); position: relative; overflow: hidden; }
.login-container::before { content: ''; position: absolute; top: -20%; left: -10%; width: 500px; height: 500px; background: radial-gradient(circle, rgba(24,144,255,0.15) 0%, transparent 70%); border-radius: 50%; }
.login-box { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); padding: 48px 40px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 16px 40px rgba(0, 40, 100, 0.08); width: 400px; text-align: center; position: relative; z-index: 1; }
.login-box h2 { margin-bottom: 30px; color: #1a202c; font-weight: 700; letter-spacing: 0.5px; }
.form-area { display: flex; flex-direction: column; gap: 18px; }
.select-wrapper { position: relative; width: 100%; }
.styled-select, .form-area input { width: 100%; padding: 14px 16px; border: 1.5px solid #e2e8f0; border-radius: 8px; outline: none; font-size: 14px; transition: all 0.2s ease; background: #f8fafc; color: #1a202c; box-sizing: border-box; }
.account-select { background-color: #fff; border-color: #cbd5e1; }
.styled-select { cursor: pointer; appearance: none; background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a0aec0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e"); background-repeat: no-repeat; background-position: right 14px center; background-size: 16px; }
.styled-select:focus, .form-area input:focus { border-color: #1890ff; background: #fff; box-shadow: 0 0 0 3px rgba(24,144,255,0.15); }
.styled-select:invalid { color: #a0aec0; }
.slide-down { animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.btn-login { background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%); color: white; border: none; padding: 14px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(24,144,255,0.3); margin-top: 4px; }
.btn-login:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(24,144,255,0.4); }
</style>