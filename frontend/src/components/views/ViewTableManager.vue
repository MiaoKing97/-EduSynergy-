<template>
  <div class="table-manager-container">
    <div class="action-header">
      <div class="header-left">
        <h3>🗂️ 班级多维表格集中管理</h3>
        <p class="sub-title">在这里总览系统生成的所有多维表格档案，您可以将当前学期的常用班级固定到顶部工作栏。</p>
      </div>
      <div class="header-right">
        <button class="btn-batch" @click="batchPin(true)" :disabled="selectedTokens.length === 0">
          📌 批量固定到顶栏
        </button>
        <button class="btn-batch" @click="batchPin(false)" :disabled="selectedTokens.length === 0">
          ❌ 批量取消固定
        </button>
        <button class="btn-batch btn-danger" @click="batchDelete" :disabled="selectedTokens.length === 0">
          🗑️ 批量删除记录
        </button>
      </div>
    </div>

    <!-- 🌟 过滤工具条：搜索 / 科目 / 创建人 / 排序 / 视图切换 -->
    <div class="filter-bar">
      <div class="filter-search">
        <span class="search-icon">🔍</span>
        <input v-model="searchKeyword" type="text" placeholder="搜索表格名 / Token 关键词…" />
        <button v-if="searchKeyword" class="clear-btn" @click="searchKeyword = ''" title="清除搜索">✕</button>
      </div>
      <div class="filter-group">
        <label>科目</label>
        <select v-model="filterSubject">
          <option value="">全部</option>
          <option v-for="s in subjectOptions" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>创建人</label>
        <select v-model="filterOwner">
          <option value="">全部</option>
          <option v-for="o in ownerOptions" :key="o.id" :value="o.id">{{ o.name }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>排序</label>
        <select v-model="sortBy">
          <option value="recent">最近使用</option>
          <option value="created">创建时间</option>
          <option value="name">名称</option>
        </select>
      </div>
      <div class="view-switcher">
        <button
          class="view-btn"
          :class="{ active: viewMode === 'table' }"
          @click="setViewMode('table')"
          title="表格视图"
        >📋 表格</button>
        <button
          class="view-btn"
          :class="{ active: viewMode === 'card' }"
          @click="setViewMode('card')"
          title="卡片视图"
        >🔳 卡片</button>
      </div>
    </div>

    <div class="result-summary">
      共 <strong>{{ displayedTables.length }}</strong> 个表格
      <span v-if="hasActiveFilter">（已应用筛选）</span>
      <span v-if="globalStore.config.feishuToken && currentTable" class="current-hint">
        · 当前使用中：<strong>{{ currentTable.name }}</strong>
      </span>
    </div>

    <!-- 🌟 表格视图 -->
    <div v-if="viewMode === 'table'" class="table-content">
      <table class="manager-table">
        <thead>
        <tr>
          <th width="5%"><input type="checkbox" @change="toggleAll" :checked="isAllSelected"/></th>
          <th width="22%">作业/考试名称</th>
          <th width="14%">所属科目 (创建人)</th>
          <th width="18%">多维表格 Token</th>
          <th width="12%">创建时间</th>
          <th width="12%">最近使用</th>
          <th width="9%">顶栏状态</th>
          <th width="13%">快捷操作</th>
        </tr>
        </thead>
        <tbody>
        <tr v-if="displayedTables.length === 0">
          <td colspan="8" class="empty-text">📭 暂无符合筛选条件的表格。</td>
        </tr>
        <tr v-for="item in displayedTables" :key="item.token"
            :class="{ 'is-selected': selectedTokens.includes(item.token), 'is-current': item.token === globalStore.config.feishuToken }">
          <td><input type="checkbox" :value="item.token" v-model="selectedTokens"/></td>
          <td class="font-bold">
            <span v-if="item.token === globalStore.config.feishuToken" class="current-dot" title="当前使用中"></span>
            📊 {{ item.name }}
            <span v-if="item.token === globalStore.config.feishuToken" class="current-tag">当前</span>
          </td>
          <td>
            <span class="subject-tag">{{ item.subject || '通用' }}</span>
            <span class="owner-name">{{ item.ownerName || '未知' }}</span>
          </td>
          <td><span class="font-mono">{{ shortToken(item.token) }}</span></td>
          <td class="date-text">{{ item.date || '—' }}</td>
          <td class="date-text">{{ lastUsedLabel(item.token) }}</td>
          <td>
            <span v-if="item.isPinned !== false" class="badge-pinned">📌 已固定</span>
            <span v-else class="badge-unpinned">未固定</span>
          </td>
          <td class="action-cells">
            <button class="btn-icon" @click="useThisTable(item)"
                    :title="item.token === globalStore.config.feishuToken ? '已是当前表' : '切换为当前工作表'"
                    :disabled="item.token === globalStore.config.feishuToken">
              ⚡
            </button>
            <button class="btn-icon" @click="toggleSinglePin(item)"
                    :title="item.isPinned !== false ? '从顶栏取消固定' : '固定到网页顶栏'">
              {{ item.isPinned !== false ? '❌' : '📌' }}
            </button>
            <button class="btn-icon" @click="openLink(item)" title="在浏览器打开飞书原生文档">🌐</button>
            <button class="btn-icon text-success" @click="openSubmitPage(item)"
                    title="打开专属学生交卷页面，方便复制链接">📤
            </button>
            <button class="btn-icon text-danger" @click="deleteSingle(item)" title="删除此条记录">🗑️</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- 🌟 卡片视图 -->
    <div v-else class="card-grid">
      <div v-if="displayedTables.length === 0" class="empty-card">
        📭 暂无符合筛选条件的表格。
      </div>
      <div
        v-for="item in displayedTables"
        :key="item.token"
        class="bitable-card"
        :class="{ 'is-selected': selectedTokens.includes(item.token), 'is-current': item.token === globalStore.config.feishuToken }"
      >
        <div class="card-top">
          <input type="checkbox" :value="item.token" v-model="selectedTokens" />
          <span class="card-title" :title="item.name">📊 {{ item.name }}</span>
          <span v-if="item.isPinned !== false" class="badge-pinned-sm">📌</span>
        </div>
        <div class="card-meta">
          <span class="subject-tag">{{ item.subject || '通用' }}</span>
          <span class="owner-name">{{ item.ownerName || '未知' }}</span>
        </div>
        <div class="card-token">
          <span class="font-mono">{{ shortToken(item.token) }}</span>
        </div>
        <div class="card-time">
          <div><span class="lbl">创建</span> {{ item.date || '—' }}</div>
          <div><span class="lbl">最近使用</span> {{ lastUsedLabel(item.token) }}</div>
        </div>
        <div class="card-current-tag" v-if="item.token === globalStore.config.feishuToken">
          ⚡ 当前使用中
        </div>
        <div class="card-actions">
          <button class="btn-icon" @click="useThisTable(item)"
                  :disabled="item.token === globalStore.config.feishuToken"
                  :title="item.token === globalStore.config.feishuToken ? '已是当前表' : '切换为当前'">⚡</button>
          <button class="btn-icon" @click="toggleSinglePin(item)"
                  :title="item.isPinned !== false ? '取消固定' : '固定到顶栏'">
            {{ item.isPinned !== false ? '❌' : '📌' }}
          </button>
          <button class="btn-icon" @click="openLink(item)" title="打开飞书">🌐</button>
          <button class="btn-icon text-success" @click="openSubmitPage(item)" title="学生交卷链接">📤</button>
          <button class="btn-icon text-danger" @click="deleteSingle(item)" title="删除本地记录">🗑️</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { globalStore } from '../../store';
import syncCenter from '../../services/syncCenter';

// 复选选中
const selectedTokens = ref([]);

// 🌟 过滤 / 排序 / 视图状态
const searchKeyword = ref('');
const filterSubject = ref('');
const filterOwner = ref('');
const sortBy = ref('recent');
const VIEW_KEY = 'ai_assistant_tm_view';
const viewMode = ref(localStorage.getItem(VIEW_KEY) || 'table');
const setViewMode = (mode) => {
  viewMode.value = mode;
  try { localStorage.setItem(VIEW_KEY, mode); } catch (e) {}
};

// 权限隔离后的基础列表
const visibleTables = computed(() => {
  const list = globalStore.config.bitableList || [];
  if (globalStore.auth.role === 'admin') return list;
  return list.filter(t => t.ownerId === globalStore.auth.userId);
});

// 派生科目 / 创建人选项
const subjectOptions = computed(() => {
  const set = new Set();
  visibleTables.value.forEach(t => { if (t.subject) set.add(t.subject); });
  return Array.from(set);
});
const ownerOptions = computed(() => {
  const map = new Map();
  visibleTables.value.forEach(t => {
    if (t.ownerId && !map.has(t.ownerId)) map.set(t.ownerId, { id: t.ownerId, name: t.ownerName || t.ownerId });
  });
  return Array.from(map.values());
});

// 当前激活的表
const currentTable = computed(() =>
  visibleTables.value.find(t => t.token === globalStore.config.feishuToken) || null
);

// 是否有筛选条件
const hasActiveFilter = computed(() =>
  Boolean(searchKeyword.value || filterSubject.value || filterOwner.value)
);

// 取该表的"最近使用时间"（来自 syncCenter 写入的 lastSyncAt）
const getLastUsed = (token) => globalStore.tableDataCache[token]?.lastSyncAt || '';
const lastUsedLabel = (token) => {
  const stamp = getLastUsed(token);
  if (!stamp) return '未使用';
  const diffMs = Date.now() - new Date(stamp).getTime();
  const min = Math.floor(diffMs / 60000);
  if (min < 1) return '刚刚';
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day} 天前`;
  return new Date(stamp).toLocaleDateString();
};

const shortToken = (token) => {
  if (!token) return '';
  if (token.length <= 18) return token;
  return `${token.slice(0, 8)}…${token.slice(-6)}`;
};

// 🌟 最终展示列表：过滤链 + 排序
const displayedTables = computed(() => {
  let arr = [...visibleTables.value];
  const kw = searchKeyword.value.trim().toLowerCase();
  if (kw) arr = arr.filter(t => (t.name || '').toLowerCase().includes(kw) || (t.token || '').toLowerCase().includes(kw));
  if (filterSubject.value) arr = arr.filter(t => (t.subject || '') === filterSubject.value);
  if (filterOwner.value) arr = arr.filter(t => t.ownerId === filterOwner.value);

  if (sortBy.value === 'recent') {
    arr.sort((a, b) => {
      const ta = getLastUsed(a.token);
      const tb = getLastUsed(b.token);
      if (!ta && !tb) return 0;
      if (!ta) return 1;
      if (!tb) return -1;
      return new Date(tb).getTime() - new Date(ta).getTime();
    });
  } else if (sortBy.value === 'name') {
    arr.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'zh'));
  } else if (sortBy.value === 'created') {
    arr.sort((a, b) => {
      const ta = a.date ? new Date(a.date).getTime() : 0;
      const tb = b.date ? new Date(b.date).getTime() : 0;
      return tb - ta;
    });
  }
  return arr;
});

const isAllSelected = computed(() =>
  displayedTables.value.length > 0 && displayedTables.value.every(i => selectedTokens.value.includes(i.token))
);

const toggleAll = (e) => {
  selectedTokens.value = e.target.checked ? displayedTables.value.map(i => i.token) : [];
};

const toggleSinglePin = (item) => { item.isPinned = item.isPinned === false ? true : false; };

const batchPin = (pinStatus) => {
  globalStore.config.bitableList.forEach(item => {
    if (selectedTokens.value.includes(item.token)) item.isPinned = pinStatus;
  });
  selectedTokens.value = [];
};

// ⚠️ 删除文案统一加上"不删飞书原表"免责说明
const batchDelete = () => {
  if (!confirm(
    `⚠️ 确定要删除选中的 ${selectedTokens.value.length} 个表格记录吗？\n\n` +
    `此操作仅会移除本系统的关联记录，飞书云端的多维表格文件不会被删除，` +
    `仍可通过原链接访问。`
  )) return;

  globalStore.config.bitableList = globalStore.config.bitableList.filter(
    item => !selectedTokens.value.includes(item.token)
  );
  // 同时清掉这些表的本地缓存
  selectedTokens.value.forEach(t => syncCenter.clearTableCache(t));
  selectedTokens.value = [];
};

const deleteSingle = (item) => {
  if (confirm(
    `⚠️ 确定要从记录中移除「${item.name}」吗？\n\n` +
    `此操作仅移除本系统的关联记录，飞书云端的多维表格文件不会被删除，仍可通过原链接访问。`
  )) {
    const realIndex = globalStore.config.bitableList.findIndex(t => t.token === item.token);
    if (realIndex > -1) globalStore.config.bitableList.splice(realIndex, 1);
    syncCenter.clearTableCache(item.token);
    selectedTokens.value = selectedTokens.value.filter(t => t !== item.token);
  }
};

// 切换为当前工作表（直接复用顶栏 useBitable 的语义）
const useThisTable = (item) => {
  if (item.token === globalStore.config.feishuToken) return;
  globalStore.config.feishuToken = item.token;
  syncCenter.onTableSwitch(item.token);
};

const openLink = (item) => window.open(`https://www.feishu.cn/base/${item.token}`, '_blank');

const openSubmitPage = (item) => {
  const cfg = globalStore.config;
  if (!cfg.feishuAppId || !cfg.feishuAppSecret) {
    alert("⚠️ 请先在右侧参数底盘配置您的飞书 App ID 和 App Secret！");
    return;
  }
  const invitePayload = {
    feishuAppId: cfg.feishuAppId,
    feishuAppSecret: cfg.feishuAppSecret,
    appToken: item.token,
    isWeb: item.subject === '网页设计' || globalStore.auth.role === 'web_teacher',
    tableName: item.name
  };
  const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(invitePayload))));
  window.open(`${window.location.origin}/?invite=${encoded}`, '_blank');
};
</script>

<style scoped>
.text-success:hover { color: #52c41a; background: #f6ffed; border-color: #b7eb8f; }

.table-manager-container { display: flex; flex-direction: column; height: 100%; box-sizing: border-box; gap: 16px; }

.action-header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 16px; border-bottom: 1px solid #ebeef5;
}
.header-left h3 { margin: 0 0 8px 0; font-size: 18px; color: #303133; }
.sub-title { margin: 0; font-size: 13px; color: #909399; }
.header-right { display: flex; gap: 10px; }

.btn-batch {
  padding: 8px 16px; border: 1px solid #dcdfe6; border-radius: 6px;
  background: #fff; cursor: pointer; font-size: 13px; font-weight: 500;
  transition: 0.2s; color: #606266;
}
.btn-batch:hover:not(:disabled) { border-color: #1890ff; color: #1890ff; background: #e6f7ff; }
.btn-batch:disabled { opacity: 0.5; cursor: not-allowed; background: #f5f7fa; }
.btn-danger:hover:not(:disabled) { border-color: #ff4d4f; color: #ff4d4f; background: #fff1f0; }

/* 🌟 过滤工具条 */
.filter-bar {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 12px 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
}
.filter-search {
  position: relative; flex: 1; min-width: 220px; max-width: 360px;
  display: flex; align-items: center;
}
.search-icon { position: absolute; left: 12px; font-size: 14px; color: #94a3b8; pointer-events: none; }
.filter-search input {
  width: 100%; height: 36px; padding: 0 32px 0 34px;
  border: 1px solid #dbe4f0; border-radius: 10px; background: #fff;
  font-size: 13px; color: #0f172a; outline: none; transition: 0.2s;
}
.filter-search input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.12); }
.clear-btn {
  position: absolute; right: 8px; width: 22px; height: 22px;
  border: none; background: #f1f5f9; color: #64748b; border-radius: 50%;
  cursor: pointer; font-size: 11px;
}
.clear-btn:hover { background: #e2e8f0; color: #1e293b; }

.filter-group { display: flex; align-items: center; gap: 6px; }
.filter-group label { font-size: 12px; color: #64748b; font-weight: 700; }
.filter-group select {
  height: 36px; padding: 0 28px 0 10px;
  border: 1px solid #dbe4f0; border-radius: 10px; background: #fff;
  font-size: 13px; color: #1e293b; cursor: pointer; outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat; background-position: right 8px center; background-size: 12px;
}
.filter-group select:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.12); }

.view-switcher {
  margin-left: auto; display: inline-flex; padding: 3px; border-radius: 10px;
  background: #e2e8f0; gap: 2px;
}
.view-btn {
  height: 30px; padding: 0 12px; border: none; background: transparent;
  border-radius: 8px; font-size: 12px; font-weight: 700; color: #475569; cursor: pointer; transition: 0.2s;
}
.view-btn.active { background: #fff; color: #1d4ed8; box-shadow: 0 2px 6px rgba(15,23,42,0.08); }
.view-btn:hover:not(.active) { color: #1d4ed8; }

.result-summary { font-size: 12px; color: #64748b; padding: 0 4px; }
.result-summary strong { color: #1e293b; font-weight: 800; }
.current-hint { margin-left: 8px; color: #1d4ed8; }

/* 表格视图 */
.table-content {
  background: #fff; border: 1px solid #ebeef5; border-radius: 8px;
  overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.02);
}
.manager-table { width: 100%; border-collapse: collapse; text-align: left; }
.manager-table th {
  background: #f9fafc; padding: 14px 16px; font-size: 13px; color: #606266;
  font-weight: 600; border-bottom: 1px solid #ebeef5;
}
.manager-table td {
  padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #ebeef5;
  color: #333; transition: background-color 0.2s;
}
.manager-table tbody tr:hover td { background-color: #f5f7fa; }
.manager-table tbody tr.is-selected td { background-color: #e6f7ff; }
.manager-table tbody tr.is-current td {
  background-color: #eff6ff;
  box-shadow: inset 3px 0 0 var(--edu-primary, #2563eb);
}
.manager-table tbody tr.is-current.is-selected td { background-color: #dbeafe; }

.current-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,0.18);
  margin-right: 4px; vertical-align: middle;
}
.current-tag {
  display: inline-block; margin-left: 6px; padding: 1px 7px;
  background: var(--edu-primary, #2563eb); color: #fff;
  font-size: 10px; font-weight: 800; border-radius: 999px; letter-spacing: 0.5px;
}

.empty-text { text-align: center; color: #909399; padding: 60px !important; font-size: 14px; }
.font-bold { font-weight: 600; color: #1f1f1f; }
.font-mono { font-family: monospace; color: #666; background: #f4f4f5; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.date-text { color: #8c8c8c; font-size: 12px; }

.subject-tag { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 6px; }
.owner-name { font-size: 12px; color: #888; }

.badge-pinned { background: #e6f7ff; color: #1890ff; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #91d5ff; }
.badge-unpinned { background: #f4f4f5; color: #909399; padding: 4px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #dcdfe6; }
.badge-pinned-sm { font-size: 14px; }

.action-cells { display: flex; gap: 6px; }
.btn-icon {
  background: #fff; border: 1px solid #dcdfe6; cursor: pointer;
  font-size: 13px; padding: 6px; border-radius: 4px; transition: 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.btn-icon:hover:not(:disabled) {
  background: #e6f7ff; border-color: #1890ff; transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
.btn-icon:disabled { opacity: 0.35; cursor: not-allowed; }
.text-danger:hover { color: #f5222d; background: #fff1f0; border-color: #ffa39e; }

/* 🌟 卡片视图 */
.card-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.empty-card {
  grid-column: 1 / -1; padding: 60px;
  text-align: center; color: #909399; font-size: 14px;
  background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 12px;
}
.bitable-card {
  position: relative;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 16px; display: flex; flex-direction: column; gap: 10px;
  transition: 0.2s; box-shadow: 0 2px 8px rgba(15,23,42,0.04);
}
.bitable-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15,23,42,0.08); border-color: #cbd5e1; }
.bitable-card.is-selected { background: #f0f9ff; border-color: #93c5fd; }
.bitable-card.is-current {
  background: linear-gradient(135deg, #eff6ff 0%, #f5f3ff 100%);
  border: 2px solid var(--edu-primary, #2563eb);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.16);
}
.card-top { display: flex; align-items: center; gap: 8px; }
.card-title {
  flex: 1; font-size: 14px; font-weight: 800; color: #0f172a;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-meta { display: flex; align-items: center; gap: 6px; }
.card-token { padding: 4px 0; }
.card-time {
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px;
  padding: 8px 0; border-top: 1px dashed #e2e8f0;
  font-size: 11px; color: #64748b;
}
.card-time .lbl { color: #94a3b8; font-weight: 700; margin-right: 4px; }
.card-current-tag {
  position: absolute; top: -10px; right: 12px;
  background: var(--edu-primary, #2563eb); color: #fff;
  font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 999px;
  box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3);
}
.card-actions {
  display: flex; gap: 6px; justify-content: flex-end;
  padding-top: 8px; border-top: 1px solid #f1f5f9;
}
</style>
