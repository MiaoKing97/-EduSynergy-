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

    <div class="table-content">
      <table class="manager-table">
        <thead>
          <tr>
            <th width="5%"><input type="checkbox" @change="toggleAll" :checked="isAllSelected" /></th>
            <th width="20%">作业/考试名称</th>
            <th width="15%">所属科目 (创建人)</th>
            <th width="20%">多维表格 Token</th>
            <th width="15%">创建/入库时间</th>
            <th width="12%">顶栏状态</th>
            <th width="13%">快捷操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="displayedTables.length === 0">
            <td colspan="7" class="empty-text">📭 暂无您权限下的表格数据，请前往「运行仪表盘」或「模板设置」创建。</td>
          </tr>
          <tr v-for="(item, index) in displayedTables" :key="item.token" :class="{ 'is-selected': selectedTokens.includes(item.token) }">
            <td><input type="checkbox" :value="item.token" v-model="selectedTokens" /></td>
            <td class="font-bold">📊 {{ item.name }}</td>
            <td>
              <span class="subject-tag">{{ item.subject || '通用' }}</span>
              <span class="owner-name">{{ item.ownerName || '未知' }}</span>
            </td>
            <td><span class="font-mono">{{ item.token }}</span></td>
            <td class="date-text">{{ item.date || '系统初始记录' }}</td>
            <td>
              <span v-if="item.isPinned !== false" class="badge-pinned">📌 已固定</span>
              <span v-else class="badge-unpinned">未固定</span>
            </td>
            <td class="action-cells">
              <button class="btn-icon" @click="toggleSinglePin(item)" :title="item.isPinned !== false ? '从顶栏取消固定' : '固定到网页顶栏'">
                {{ item.isPinned !== false ? '❌' : '📌' }}
              </button>
              <button class="btn-icon" @click="openLink(item)" title="在浏览器打开飞书原生文档">🌐</button>
              <button class="btn-icon text-danger" @click="deleteSingle(item)" title="删除此条记录">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { globalStore } from '../../store';

// 记录复选框选中的 token 数组
const selectedTokens = ref([]);

// 🌟 核心隔离引擎：计算出当前角色有权看到的表格列表
const displayedTables = computed(() => {
  const list = globalStore.config.bitableList || [];
  if (globalStore.auth.role === 'admin') return list; // 上帝视角：管理员看全部
  return list.filter(t => t.ownerId === globalStore.auth.userId); // 凡人视角：老师只看自己的
});

// 判断是否全选
const isAllSelected = computed(() => {
  return displayedTables.value.length > 0 && selectedTokens.value.length === displayedTables.value.length;
});

// 全选/取消全选操作
const toggleAll = (e) => {
  if (e.target.checked) {
    selectedTokens.value = displayedTables.value.map(i => i.token);
  } else {
    selectedTokens.value = [];
  }
};

// 单个固定/取消固定
const toggleSinglePin = (item) => {
  item.isPinned = item.isPinned === false ? true : false;
};

// 批量固定/取消固定
const batchPin = (pinStatus) => {
  globalStore.config.bitableList.forEach(item => {
    if (selectedTokens.value.includes(item.token)) {
      item.isPinned = pinStatus;
    }
  });
  selectedTokens.value = []; // 操作后清空选中状态
};

// 批量删除
const batchDelete = () => {
  if (!confirm(`⚠️ 确定要删除选中的 ${selectedTokens.value.length} 个表格记录吗？\n(注意：这仅会清除本系统的关联记录，不会删除飞书云端的真实文件)`)) return;

  globalStore.config.bitableList = globalStore.config.bitableList.filter(
    item => !selectedTokens.value.includes(item.token)
  );
  selectedTokens.value = [];
};

// 单个删除 (🌟 修复索引映射安全问题)
const deleteSingle = (item) => {
  if (confirm(`⚠️ 确定要从记录中移除「${item.name}」吗？`)) {
    // 必须去全局真实列表中查找索引进行切割，不能用当前视图列表的 index
    const realIndex = globalStore.config.bitableList.findIndex(t => t.token === item.token);
    if (realIndex > -1) {
      globalStore.config.bitableList.splice(realIndex, 1);
    }
    selectedTokens.value = selectedTokens.value.filter(t => t !== item.token);
  }
};

// 外部链接打开
const openLink = (item) => {
  window.open(`https://www.feishu.cn/base/${item.token}`, '_blank');
};
</script>

<style scoped>
.table-manager-container { display: flex; flex-direction: column; height: 100%; box-sizing: border-box; }
.action-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #ebeef5; margin-bottom: 20px; }
.header-left h3 { margin: 0 0 8px 0; font-size: 18px; color: #303133; }
.sub-title { margin: 0; font-size: 13px; color: #909399; }
.header-right { display: flex; gap: 10px; }

.btn-batch { padding: 8px 16px; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; cursor: pointer; font-size: 13px; font-weight: 500; transition: 0.2s; color: #606266;}
.btn-batch:hover:not(:disabled) { border-color: #1890ff; color: #1890ff; background: #e6f7ff; }
.btn-batch:disabled { opacity: 0.5; cursor: not-allowed; background: #f5f7fa; }
.btn-danger:hover:not(:disabled) { border-color: #ff4d4f; color: #ff4d4f; background: #fff1f0; }

.table-content { background: #fff; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.02);}
.manager-table { width: 100%; border-collapse: collapse; text-align: left; }
.manager-table th { background: #f9fafc; padding: 14px 16px; font-size: 13px; color: #606266; font-weight: 600; border-bottom: 1px solid #ebeef5; }
.manager-table td { padding: 14px 16px; font-size: 13px; border-bottom: 1px solid #ebeef5; color: #333; transition: background-color 0.2s; }
.manager-table tbody tr:hover td { background-color: #f5f7fa; }
.manager-table tbody tr.is-selected td { background-color: #e6f7ff; }

.empty-text { text-align: center; color: #909399; padding: 60px !important; font-size: 14px; }
.font-bold { font-weight: 600; color: #1f1f1f; }
.font-mono { font-family: monospace; color: #666; background: #f4f4f5; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.date-text { color: #8c8c8c; font-size: 12px; }

/* 🌟 新增科目与物主样式 */
.subject-tag { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; padding: 2px 6px; border-radius: 4px; font-size: 12px; margin-right: 6px; }
.owner-name { font-size: 12px; color: #888; }

.badge-pinned { background: #e6f7ff; color: #1890ff; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #91d5ff;}
.badge-unpinned { background: #f4f4f5; color: #909399; padding: 4px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #dcdfe6;}

.action-cells { display: flex; gap: 8px; }
.btn-icon { background: #fff; border: 1px solid #dcdfe6; cursor: pointer; font-size: 13px; padding: 6px; border-radius: 4px; transition: 0.2s; display: flex; align-items: center; justify-content: center;}
.btn-icon:hover { background: #e6f7ff; border-color: #1890ff; transform: translateY(-1px); box-shadow: 0 2px 4px rgba(0,0,0,0.05);}
.text-danger:hover { color: #f5222d; background: #fff1f0; border-color: #ffa39e; }
</style>