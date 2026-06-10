<template>
  <div class="login-page">
    <div class="aurora aurora-1"></div>
    <div class="aurora aurora-2"></div>
    <div class="aurora aurora-3"></div>
    <div class="grid-bg"></div>

    <main class="login-shell">
      <section class="brand-panel">
        <div class="brand-badge">AI + 教育数据中台</div>

        <div class="brand-hero">
          <div class="brand-title-group">
            <div class="logo-stack">
              <span class="logo-ring"></span>
              <span class="logo-mark">杏</span>
            </div>
            <h1 class="brand-title">
              <span class="brand-title-text">坛智析</span>
              <span class="brand-title-shine"></span>
            </h1>
          </div>
          <p class="brand-sub">EduSynergy ·人机协同学情共创平台</p>
          <div class="brand-divider"></div>
        </div>

        <div class="hero-copy">
          <h2>让教、学、评数据<br />在同一张智能图谱中协同生长</h2>
          <p>接入飞书多维表格、AI 批改、学情分析与学生档案，构建老师可用、学生可见的教学闭环。</p>
        </div>

        <div class="feature-list">
          <div class="feature-item">
            <span>🧠</span>
            <div>
              <strong>智能批改</strong>
              <small>多模态作业识别与错因诊断</small>
            </div>
          </div>
          <div class="feature-item">
            <span>📊</span>
            <div>
              <strong>学情看板</strong>
              <small>飞书云端数据实时汇总</small>
            </div>
          </div>
          <div class="feature-item">
            <span>🧑‍🎓</span>
            <div>
              <strong>学生档案</strong>
              <small>个人能力画像与追踪分析</small>
            </div>
          </div>
        </div>
      </section>

      <section class="login-card">
        <div class="card-heading">
          <div>
            <span class="eyebrow">Welcome back</span>
            <h3>登录工作台</h3>
          </div>
          <span class="status-pill">安全认证</span>
        </div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="subject">所属教研组 / 身份</label>
            <div class="select-wrapper">
              <span class="field-icon">🏫</span>
              <select id="subject" v-model="selectedSubject" required>
                <option value="" disabled>请选择您的教研组或身份</option>
                <option v-for="sub in availableSubjects" :key="sub.name" :value="sub.name">
                  {{ sub.icon }} {{ sub.name }}
                </option>
              </select>
            </div>
          </div>

          <transition name="field-fade">
            <div v-if="selectedSubject" class="form-group">
              <label for="account">专属账号</label>
              <div class="select-wrapper">
                <span class="field-icon">🧑‍🏫</span>
                <select id="account" v-model="selectedUsername" required>
                  <option value="" disabled>请选择您的专属账号</option>
                  <option v-for="acc in availableAccounts" :key="acc.id || acc.username" :value="acc.username">
                    {{ acc.username }}
                  </option>
                </select>
              </div>
            </div>
          </transition>

          <div class="form-group">
            <label for="password">系统密码</label>
            <div class="input-wrapper">
              <span class="field-icon">🔒</span>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入系统密码"
                autocomplete="current-password"
              />
              <button type="button" class="toggle-visibility" @click="showPassword = !showPassword">
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
          </div>

          <div class="helper-row" v-if="availableAccounts.length">
            <span>{{ availableAccounts.length }} 个可用账号</span>
          </div>

          <button type="submit" class="btn-login" :disabled="loggingIn || !canSubmit">
            <span v-if="loggingIn" class="loading-text">
              <span class="spinner-dot"></span>
              正在进入系统...
            </span>
            <span v-else>{{ canSubmit ? '进入智能教务工作台' : '请先填写完整信息' }}</span>
          </button>
        </form>

        <div class="card-footer">
          <span>© 2026 杏坛智析 · 人机协同学情共创平台</span>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { globalStore, login } from '../../store';

const router = useRouter();
const password = ref('');
const selectedSubject = ref('');
const selectedUsername = ref('');
const showPassword = ref(false);
const loggingIn = ref(false);

onMounted(async () => {
  try {
    const resp = await fetch('/api/auth/users');
    if (resp.ok) {
      globalStore.users = await resp.json();
    }
  } catch (e) {
    console.warn('Failed to fetch users:', e);
  }
});

watch(selectedSubject, () => {
  selectedUsername.value = '';
});

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

const canSubmit = computed(() => {
  return selectedSubject.value && selectedUsername.value && password.value;
});

const handleLogin = async () => {
  if (!canSubmit.value || loggingIn.value) return;

  loggingIn.value = true;
  const result = await login(selectedUsername.value, password.value);
  loggingIn.value = false;

  if (!result.success) {
    alert('❌ ' + result.error);
    return;
  }

  if (globalStore.auth.role === 'admin') {
    router.replace('/account-manager');
  } else if (globalStore.auth.role === 'student') {
    router.replace('/student');
  } else {
    router.replace('/dashboard');
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.24), transparent 30%),
    radial-gradient(circle at 80% 0%, rgba(14, 165, 233, 0.20), transparent 28%),
    linear-gradient(135deg, #eef4ff 0%, #f8fbff 42%, #eef2ff 100%);
}

.grid-bg {
  position: absolute;
  inset: 0;
  opacity: 0.55;
  background-image:
    linear-gradient(rgba(59, 130, 246, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.08) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 25%, transparent 75%);
}

.aurora {
  position: absolute;
  border-radius: 999px;
  filter: blur(18px);
  opacity: 0.55;
  animation: float 9s ease-in-out infinite;
}
.aurora-1 { width: 360px; height: 360px; left: -90px; top: -90px; background: #93c5fd; }
.aurora-2 { width: 300px; height: 300px; right: -70px; top: 12%; background: #c4b5fd; animation-delay: -2s; }
.aurora-3 { width: 260px; height: 260px; left: 48%; bottom: -100px; background: #67e8f9; animation-delay: -4s; }

@keyframes float {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(16px, -18px, 0) scale(1.04); }
}

.login-shell {
  width: min(1080px, 100%);
  min-height: 640px;
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 30px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(24px);
  box-shadow: 0 30px 90px rgba(30, 64, 175, 0.18);
  animation: shellEnter 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes shellEnter {
  from { opacity: 0; transform: translateY(24px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.brand-panel {
  position: relative;
  padding: 48px;
  color: #fff;
  background:
    linear-gradient(135deg, rgba(30, 64, 175, 0.92), rgba(79, 70, 229, 0.86)),
    url("data:image/svg+xml,%3Csvg width='180' height='180' viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' stroke='%23ffffff' stroke-opacity='0.12'%3E%3Cpath d='M20 90h140M90 20v140'/%3E%3Ccircle cx='90' cy='90' r='54'/%3E%3C/g%3E%3C/svg%3E");
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}

.brand-panel::after {
  content: '';
  position: absolute;
  width: 360px;
  height: 360px;
  right: -170px;
  bottom: -150px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.brand-badge {
  position: absolute;
  top: 48px;
  right: 48px;
  z-index: 10;
  width: fit-content;
  padding: 8px 14px;
  border: 1px solid rgba(255,255,255,0.28);
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.8px;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 42px;
}

.brand-hero {
  position: relative;
  z-index: 1;
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
}

/* 新增的flex容器，使图标和标题在同一行 */
.brand-title-group {
  display: flex;
  align-items: center;
  gap: 18px;
}

.logo-stack {
  position: relative;
  width: 86px;
  height: 86px;
  display: grid;
  place-items: center;
}

.logo-ring {
  position: absolute;
  inset: -8px;
  border-radius: 28px;
  background: conic-gradient(from 90deg, rgba(253, 224, 71, 0.85), rgba(255, 255, 255, 0.35), rgba(125, 211, 252, 0.85), rgba(253, 224, 71, 0.85));
  filter: blur(10px);
  opacity: 0.6;
  animation: ringSpin 8s linear infinite;
}

@keyframes ringSpin {
  to { transform: rotate(360deg); }
}

.logo-stack .logo-mark {
  position: relative;
  width: 86px;
  height: 86px;
  border-radius: 26px;
  background: linear-gradient(140deg, #ffffff 0%, #fef3c7 60%, #fde68a 100%);
  color: #3730a3;
  font-size: 44px;
  font-weight: 900;
  display: grid;
  place-items: center;
  box-shadow: 0 22px 50px rgba(15, 23, 42, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  font-family: "STKaiti", "KaiTi", "楷体", serif;
}

.brand-title {
  position: relative;
  margin: 0; /* 移除原有margin-top，确保垂直对齐中心 */
  font-size: 56px;
  font-weight: 900;
  letter-spacing: 10px;
  line-height: 1;
  font-family: "STKaiti", "KaiTi", "楷体", "Microsoft YaHei", serif;
  text-shadow: 0 4px 22px rgba(15, 23, 42, 0.45);
}

.brand-title-text {
  background: linear-gradient(120deg, #ffffff 0%, #fef9c3 38%, #fde68a 60%, #ffffff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-stroke: 1px rgba(255, 255, 255, 0.45);
}

.brand-title-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 30%, rgba(255, 255, 255, 0.55) 50%, transparent 70%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: shineSweep 4.5s ease-in-out infinite;
  pointer-events: none;
}

@keyframes shineSweep {
  0% { background-position: -200% 0; }
  60%, 100% { background-position: 220% 0; }
}

.brand-sub {
  margin: 0;
  color: rgba(255, 255, 255, 0.82);
  font-weight: 700;
  letter-spacing: 3px;
  font-size: 26px; /* 字体增大两倍（原为13px） */
}

.brand-divider {
  width: 96px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #fde68a, rgba(255, 255, 255, 0.0));
  box-shadow: 0 0 18px rgba(253, 224, 71, 0.55);
}

.hero-copy {
  margin: 34px 0 auto;
  max-width: 460px;
  position: relative;
  z-index: 1;
}

/* 调整后的标题字号 */
.hero-copy h2 {
  margin: 0;
  font-size: 20px; /* 进一步缩小（原为28px） */
  line-height: 1.45;
  letter-spacing: -0.5px;
}

.hero-copy p {
  margin: 18px 0 0;
  color: rgba(255,255,255,0.78);
  line-height: 1.85;
  font-size: 15px;
}

.feature-list {
  display: grid;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.14);
}

.feature-item span {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(255,255,255,0.16);
}

.feature-item strong {
  display: block;
  font-size: 14px;
}

.feature-item small {
  display: block;
  margin-top: 3px;
  color: rgba(255,255,255,0.68);
}

.login-card {
  padding: 52px 46px 34px;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  flex-direction: column;
}

.card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 34px;
}

.eyebrow {
  color: #2563eb;
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 1.8px;
}

.card-heading h3 {
  margin: 6px 0 0;
  color: #0f172a;
  font-size: 30px;
  letter-spacing: -0.6px;
}

.status-pill {
  flex-shrink: 0;
  padding: 8px 12px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #047857;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid #bbf7d0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.form-group label {
  color: #334155;
  font-size: 13px;
  font-weight: 800;
}

.select-wrapper,
.input-wrapper {
  position: relative;
}

.field-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 17px;
  z-index: 1;
  opacity: 0.72;
  pointer-events: none;
}

select,
.input-wrapper input {
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  border: 1.5px solid #dbe4f0;
  border-radius: 16px;
  background-color: #f8fafc;
  color: #0f172a;
  font-size: 15px;
  font-weight: 650;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

select {
  padding: 0 44px 0 48px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 16px center;
  background-size: 17px;
}

.input-wrapper input {
  padding: 0 76px 0 48px;
}

select:hover,
select:focus,
.input-wrapper input:hover,
.input-wrapper input:focus {
  border-color: #3b82f6;
  background-color: #fff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
  outline: none;
}

.input-wrapper input::placeholder {
  color: #94a3b8;
  font-weight: 500;
}

.toggle-visibility {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  height: 32px;
  padding: 0 10px;
  border: none;
  border-radius: 10px;
  background: #e0e7ff;
  color: #3730a3;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: 0.2s;
}

.toggle-visibility:hover {
  background: #c7d2fe;
}

.helper-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #64748b;
  font-size: 12px;
}

.helper-row strong {
  color: #334155;
}

.btn-login {
  height: 54px;
  border: none;
  border-radius: 17px;
  color: #fff;
  background: linear-gradient(135deg, #2563eb 0%, #4f46e5 55%, #7c3aed 100%);
  box-shadow: 0 16px 32px rgba(79, 70, 229, 0.28);
  font-size: 15px;
  font-weight: 900;
  letter-spacing: 1px;
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, opacity 0.22s ease;
}

.btn-login:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 42px rgba(79, 70, 229, 0.35);
}

.btn-login:active:not(:disabled) {
  transform: translateY(0);
}

.btn-login:disabled {
  cursor: not-allowed;
  opacity: 0.58;
  box-shadow: none;
}

.loading-text {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.spinner-dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  border: 2px solid rgba(255,255,255,0.45);
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-footer {
  margin-top: auto;
  padding-top: 34px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
}

.field-fade-enter-active,
.field-fade-leave-active {
  transition: all 0.2s ease;
}

.field-fade-enter-from,
.field-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 920px) {
  .login-page { padding: 24px; }
  .login-shell {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .brand-panel {
    padding: 34px;
  }
  /* 响应式适配右上角标签的内边距 */
  .brand-badge {
    top: 34px;
    right: 34px;
  }
  .brand-title {
    font-size: 44px;
    letter-spacing: 8px;
  }
  .hero-copy {
    margin: 28px 0;
  }
  .hero-copy h2 {
    font-size: 16px; /* 移动端进一步缩小 */
  }
  .feature-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .login-page { padding: 14px; }
  .brand-panel { display: none; }
  .login-card { padding: 34px 22px 26px; }
  .card-heading { margin-bottom: 26px; }
  .card-heading h3 { font-size: 26px; }
  .helper-row { align-items: flex-start; flex-direction: column; gap: 6px; }
}
</style>