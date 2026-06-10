// 🌟 统一同步中心：所有飞书多维表格的数据请求都从这里走。
// - 集中维护 globalStore.sync 状态机（loading / lastSyncAt / error）
// - 集中写入 globalStore.tableDataCache，并附带 lastSyncAt 字段
// - 用 inflight Map 去重同一 token 的并发请求
// - 所有清缓存动作都用 clearTableCache，避免散落 delete cache[token + '_grades']

import axios from 'axios';
import { globalStore, clearTableCache as _clearTableCache } from '../store';

const API = '/api/homework';

const buildPayload = (token) => ({
  feishu_app_id: globalStore.config.feishuAppId,
  feishu_app_secret: globalStore.config.feishuAppSecret,
  app_token: token,
});

const beginSync = (token) => {
  globalStore.sync.loading = true;
  globalStore.sync.currentToken = token;
  globalStore.sync.error = '';
};

const endSync = (token, success, errMsg = '') => {
  globalStore.sync.loading = false;
  if (success) {
    globalStore.sync.lastSyncAt = new Date().toISOString();
    globalStore.sync.error = '';
  } else {
    globalStore.sync.error = errMsg || '同步失败';
  }
};

// 把一次实际请求包装为带 inflight 去重 + 状态记录的 promise
const runOnce = (key, token, requestFn) => {
  const inflight = globalStore.sync.inflight;
  if (inflight[key]) return inflight[key];

  beginSync(token);
  const p = (async () => {
    try {
      const data = await requestFn();
      endSync(token, true);
      return data;
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || String(e);
      endSync(token, false, msg);
      throw e;
    } finally {
      delete inflight[key];
    }
  })();
  inflight[key] = p;
  return p;
};

// ─── 公共 API ───

/**
 * 拉取批改工作区数据（待批改 / 已批改 两列）。
 * 命中缓存条件：缓存存在且未指定 force。
 * @returns {Promise<{pending_list:Array, graded_list:Array, lastSyncAt:string}>}
 */
export const loadWorkspaceData = async (token, force = false) => {
  if (!token) return null;
  const cache = globalStore.tableDataCache[token];
  if (cache?.workspace && !force) return cache.workspace;

  return runOnce(`workspace:${token}`, token, async () => {
    const res = await axios.post(`${API}/get_workspace_data`, buildPayload(token));
    if (res.data?.status !== 'success') throw new Error(res.data?.detail || '工作区数据返回异常');
    const payload = {
      pending_list: res.data.pending_list || [],
      graded_list: res.data.graded_list || [],
      lastSyncAt: new Date().toISOString(),
    };
    globalStore.tableDataCache[token] = {
      ...(globalStore.tableDataCache[token] || {}),
      workspace: payload,
      lastSyncAt: payload.lastSyncAt,
    };
    return payload;
  });
};

/**
 * 拉取仪表盘统计（包含 raw_records）。Dashboard / Analytics 共用。
 * @returns {Promise<{raw_records:Array, lastSyncAt:string}>}
 */
export const loadDashboardStats = async (token, force = false) => {
  if (!token) return null;
  const cache = globalStore.tableDataCache[token];
  if (cache?.rawRecords && !force) {
    return { raw_records: cache.rawRecords, lastSyncAt: cache.lastSyncAt };
  }

  return runOnce(`stats:${token}`, token, async () => {
    const res = await axios.post(`${API}/get_dashboard_stats`, buildPayload(token));
    if (res.data?.status !== 'success') throw new Error(res.data?.detail || '仪表盘统计返回异常');
    const records = res.data.stats?.raw_records || [];
    const stamp = new Date().toISOString();
    globalStore.tableDataCache[token] = {
      ...(globalStore.tableDataCache[token] || {}),
      rawRecords: records,
      lastSyncAt: stamp,
    };
    return { raw_records: records, lastSyncAt: stamp };
  });
};

/**
 * 成绩档案中心需要的合并视图：dashboard_stats + workspace_data 并发拉。
 * 缓存键固定为 `${token}_grades`。
 * @returns {Promise<{rawRecords:Array, workspace:Array, lastSyncAt:string}>}
 */
export const loadGradesData = async (token, force = false) => {
  if (!token) return null;
  const cacheKey = token + '_grades';
  const cache = globalStore.tableDataCache[cacheKey];
  if (cache && !force) return cache;

  return runOnce(`grades:${token}`, token, async () => {
    const payload = buildPayload(token);
    const [dashRes, workRes] = await Promise.all([
      axios.post(`${API}/get_dashboard_stats`, payload),
      axios.post(`${API}/get_workspace_data`, payload),
    ]);
    const rawRecords = dashRes.data?.status === 'success' ? (dashRes.data.stats?.raw_records || []) : [];
    const workspace = workRes.data?.status === 'success' ? (workRes.data.graded_list || []) : [];
    const stamp = new Date().toISOString();
    const entry = { rawRecords, workspace, lastSyncAt: stamp };
    globalStore.tableDataCache[cacheKey] = entry;
    // 同时把 rawRecords 写到基础键，避免 Dashboard 读不到
    globalStore.tableDataCache[token] = {
      ...(globalStore.tableDataCache[token] || {}),
      rawRecords,
      lastSyncAt: stamp,
    };
    return entry;
  });
};

/**
 * 清当前表的所有缓存（基础键 + _grades 键）。批改完成后调用。
 */
export const clearTableCache = (token) => {
  _clearTableCache(token);
};

/**
 * 切换顶栏 tab 时调用：重置 currentToken、若该表无缓存则触发后台静默拉取。
 * 不抛错；用户只会在徽章上看到 loading→success/error。
 */
export const onTableSwitch = async (token) => {
  if (!token) return;
  globalStore.sync.currentToken = token;
  const cached = globalStore.tableDataCache[token];
  if (cached?.lastSyncAt) {
    // 已有缓存就只更新 lastSyncAt 展示，不再发请求
    globalStore.sync.lastSyncAt = cached.lastSyncAt;
    return;
  }
  try {
    await loadDashboardStats(token, false);
  } catch (e) {
    // 错误已写入 sync.error，吞掉异常即可
  }
};

/**
 * 强制刷新当前 token 的所有数据（徽章点击行为）。
 */
export const forceRefreshCurrent = async () => {
  const token = globalStore.config.feishuToken;
  if (!token) return;
  clearTableCache(token);
  try {
    await loadDashboardStats(token, true);
  } catch (e) { /* 状态已记录 */ }
};

export default {
  loadWorkspaceData,
  loadDashboardStats,
  loadGradesData,
  clearTableCache,
  onTableSwitch,
  forceRefreshCurrent,
};
