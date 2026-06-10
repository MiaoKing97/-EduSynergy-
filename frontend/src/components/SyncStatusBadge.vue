<template>
  <button
    class="sync-badge"
    :class="[statusClass, { 'is-disabled': !globalStore.config.feishuToken }]"
    :title="tooltip"
    @click="handleClick"
  >
    <span class="badge-icon" :class="{ 'is-spinning': status === 'loading' }">{{ statusIcon }}</span>
    <span class="badge-text">{{ statusText }}</span>
  </button>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { globalStore } from '../store';
import syncCenter from '../services/syncCenter';

const tick = ref(0); // 用于驱动 relativeTime 每 30s 刷新
let timer = null;

onMounted(() => { timer = setInterval(() => { tick.value++; }, 30000); });
onUnmounted(() => { if (timer) clearInterval(timer); });

const status = computed(() => {
  if (globalStore.sync.loading) return 'loading';
  if (globalStore.sync.error) return 'error';
  if (globalStore.sync.lastSyncAt) return 'success';
  return 'idle';
});

const statusIcon = computed(() => ({
  idle: '⚪', loading: '🔄', success: '✅', error: '❌',
}[status.value]));

const relativeTime = computed(() => {
  // eslint-disable-next-line no-unused-expressions
  tick.value; // 强制依赖收集
  if (!globalStore.sync.lastSyncAt) return '';
  const diffMs = Date.now() - new Date(globalStore.sync.lastSyncAt).getTime();
  const sec = Math.floor(diffMs / 1000);
  if (sec < 30) return '刚刚';
  if (sec < 60) return `${sec} 秒前`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  return `${Math.floor(hr / 24)} 天前`;
});

const statusText = computed(() => ({
  idle: '暂未同步',
  loading: '同步中…',
  success: `已同步 · ${relativeTime.value}`,
  error: '同步失败',
}[status.value]));

const statusClass = computed(() => `is-${status.value}`);

const tooltip = computed(() => {
  if (status.value === 'error') return `同步失败：${globalStore.sync.error}（点击重试）`;
  if (status.value === 'loading') return '正在从飞书拉取最新数据…';
  if (status.value === 'success') return `最后同步于 ${new Date(globalStore.sync.lastSyncAt).toLocaleString()}（点击强制刷新）`;
  if (!globalStore.config.feishuToken) return '请先选择一个飞书多维表格';
  return '点击同步当前表格数据';
});

const handleClick = () => {
  if (!globalStore.config.feishuToken || status.value === 'loading') return;
  syncCenter.forceRefreshCurrent();
};
</script>

<style scoped>
.sync-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--edu-border);
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.2px;
  color: #475569;
  transition: all 0.2s ease;
  box-shadow: var(--edu-shadow-soft);
  white-space: nowrap;
}

.sync-badge:hover:not(.is-disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.10);
}

.sync-badge.is-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.badge-icon {
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.badge-text { font-size: 12px; }

/* 状态色 */
.sync-badge.is-idle    { color: #64748b; border-color: #e2e8f0; }
.sync-badge.is-loading { color: #1d4ed8; border-color: #bfdbfe; background: #eff6ff; }
.sync-badge.is-success { color: #047857; border-color: #bbf7d0; background: #f0fdf4; }
.sync-badge.is-error   { color: #b91c1c; border-color: #fecaca; background: #fef2f2; }

.is-spinning { animation: badge-spin 1s linear infinite; }
@keyframes badge-spin { to { transform: rotate(360deg); } }
</style>
