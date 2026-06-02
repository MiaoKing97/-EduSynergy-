<template>
  <div class="teacher-view-container">

    <div class="setup-card">
      <div class="setup-info">
        <h4>🗂️ 第一步：为新班级/新考试创建专属数据表引擎</h4>
        <p>一键在飞书端自动生成带标准结构的【批改结果表】，并自动收录到右侧的全局下拉框大名单中。</p>
      </div>
      <div class="setup-actions">
        <input v-model="newTableName" placeholder="输入表格名称，如：初二3班期中考试" />
        <button class="btn-create" @click="createNewTable" :disabled="isCreatingTable">
          <span v-if="isCreatingTable" class="spin">🔄</span>
          {{ isCreatingTable ? '正在云端建表...' : '⚡ 一键生成全新表格' }}
        </button>
      </div>
    </div>

    <div class="action-header">
      <div class="header-left">
        <h3>📝 第二步：老师作业模板与高级批改标尺</h3>
        <p class="sub-title">上传空白试卷或标准卷，AI将自动提取【题号、题型、分值、答案、题目正文、深度解析】并建库</p>
      </div>
      <div class="header-right">
        <button class="btn-primary" @click="triggerUpload">
          <span class="icon">📤</span> 上传标准卷图片
        </button>
        <input type="file" ref="fileInput" @change="handleFileUpload" accept="image/*" style="display: none;" />
      </div>
    </div>

    <div class="split-workspace">

      <div class="panel-left">
        <div class="panel-title">标准卷面预览</div>
        <div class="image-viewer">
          <div v-if="!templateImage" class="empty-image">
            <div class="empty-icon">📄</div>
            <p>请点击右上角上传标准答案图片</p>
          </div>
          <img v-else :src="templateImage" alt="标准答案" />
        </div>
      </div>

      <div class="panel-right">
        <div class="panel-title flex-between">
          <span>⚙️ 结构化题库标尺 (AI 深度解析)</span>
          <button class="btn-extract" @click="extractTemplate" :disabled="!templateImage || isExtracting">
            <span v-if="isExtracting" class="spin">🔄</span>
            {{ isExtracting ? 'AI 正在分析并生成解析...' : '✨ 一键智能提取' }}
          </button>
        </div>

        <div class="rule-content">
          <div v-if="!extractedRules && !isExtracting" class="empty-rule">
            等待提取题目结构与深度解析内容...
          </div>

          <div v-else-if="extractedRules" class="rule-tree">
            <div class="total-score-box">
              卷面题目总数：<strong>{{ extractedRules.length }}</strong> 道 | 总分：<strong>{{ totalScore }}</strong> 分
            </div>

            <div class="question-list">
              <div class="question-item" v-for="(q, index) in extractedRules" :key="index">
                <div class="q-header">
                  <span class="q-num">第 {{ q.number }} 题</span>
                  <span class="q-type">{{ q.type }}</span>
                  <span class="q-score">{{ q.score }} 分</span>
                </div>
                <div class="q-body">
                  <div class="q-text"><strong>题目正文：</strong>{{ q.question || '暂无识别正文' }}</div>
                  <div class="q-answer"><strong>标准答案：</strong><span class="ans-badge">{{ q.answer }}</span></div>
                  <div class="q-analysis"><strong>💡 智能教学解析：</strong>{{ q.analysis || '暂无解析' }}</div>
                </div>
              </div>
            </div>

            <button class="btn-save-rule" :disabled="isSaving" @click="saveRulesToFeishu">
              {{ isSaving ? '正在批量导入飞书表格...' : '💾 保存并自动导入飞书表格数据库' }}
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { globalStore } from '../../store';

// 新建表格相关的状态变量
const newTableName = ref('');
const isCreatingTable = ref(false);

const fileInput = ref(null);
const fileForUpload = ref(null);
const templateImage = ref('');
const isExtracting = ref(false);
const isSaving = ref(false);
const extractedRules = ref(null);

const API_BASE_URL = '/api/homework';

const totalScore = computed(() => {
  if (!extractedRules.value) return 0;
  return extractedRules.value.reduce((sum, q) => sum + Number(q.score || 0), 0);
});

// 🌟 核心逻辑：一键建表并自动入库
const createNewTable = async () => {
  const cfg = globalStore.config;
  if (!cfg.feishuAppId || !cfg.feishuAppSecret) {
    alert("请先在右侧配置面板填写飞书的 App ID 和 App Secret！");
    return;
  }
  if (!newTableName.value.trim()) {
    alert("请输入要创建的表格名称！");
    return;
  }

  isCreatingTable.value = true;
  try {
    const response = await axios.post(`${API_BASE_URL}/create_table`, {
      table_name: newTableName.value.trim(),
      feishu_app_id: cfg.feishuAppId,
      feishu_app_secret: cfg.feishuAppSecret
    });

    if (response.data.status === 'success') {
      const appToken = response.data.app_token;

      // 1. 设置为系统的全局焦点 Token
      globalStore.config.feishuToken = appToken;

      // 2. 🌟 将建好的表格自动收录到全局列表中（实现自动进入下拉框的关键一步！）
      if (!globalStore.config.bitableList) {
        globalStore.config.bitableList = [];
      }
      // 🌟 补充物主标签以支持数据隔离
      globalStore.config.bitableList.unshift({
        name: newTableName.value.trim(),
        token: appToken,
        date: new Date().toLocaleString(),
        ownerId: globalStore.auth.userId,
        ownerName: globalStore.auth.username,
        subject: globalStore.auth.subject
      });

      alert(`🎉 班级多维表格创建成功！\n\n表名称：${newTableName.value}\nToken：${appToken}\n\n该表已被设为当前全局焦点，右侧列表和成绩档案页下拉框已自动更新！请继续进行第二步提规。`);
      newTableName.value = '';
    }
  } catch (error) {
    console.error("创建多维表格失败:", error);
    alert("❌ 创建失败，请检查飞书凭证权限或网络连接。\n原因：" + (error.response?.data?.detail || error.message));
  } finally {
    isCreatingTable.value = false;
  }
};

const triggerUpload = () => { fileInput.value.click(); };

const handleFileUpload = (event) => {
  const files = event.target.files;
  if (files.length === 0) return;

  fileForUpload.value = files[0];
  templateImage.value = URL.createObjectURL(files[0]);
  extractedRules.value = null;
  event.target.value = '';
};

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = (error) => reject(error);
  });
};

const extractTemplate = async () => {
  const cfg = globalStore.config;
  if (!cfg.apiKey) { alert("请先在右侧配置面板填写 AI 的 API Key！"); return; }
  if (!fileForUpload.value) { alert("请先上传试卷图片！"); return; }

  isExtracting.value = true;
  try {
    const base64Str = await fileToBase64(fileForUpload.value);
    const response = await axios.post(`${API_BASE_URL}/extract_template`, {
      image_base64: base64Str,
      ai_model: cfg.model,
      api_key: cfg.apiKey
    });

    if (response.data.status === 'success') {
      extractedRules.value = response.data.data;
    }
  } catch (error) {
    console.error("AI 提取失败:", error);
    alert("❌ 提取失败：" + (error.response?.data?.detail || error.message));
  } finally {
    isExtracting.value = false;
  }
};

const saveRulesToFeishu = async () => {
  const cfg = globalStore.config;
  if (!cfg.feishuAppId || !cfg.feishuToken) {
    alert("请确保右侧面板已配置好飞书的 App ID、Secret 以及表格 Token！\n(您可以点击上方的【一键生成全新表格】自动获取)");
    return;
  }

  isSaving.value = true;
  try {
    const response = await axios.post(`${API_BASE_URL}/save_template_rules`, {
      feishu_app_id: cfg.feishuAppId,
      feishu_app_secret: cfg.feishuAppSecret,
      app_token: cfg.feishuToken,
      rules: extractedRules.value
    });

    if (response.data.status === 'success') {
      const rulesString = JSON.stringify(extractedRules.value, null, 2);
      globalStore.config.systemPrompt = `你是一个严谨的老师。请严格根据以下【批改标尺】来批改这张学生作业图片：\n${rulesString}\n请详细指出学生的错误步骤并计算最终得分。`;

      alert('🎉 完美闭环！\n\n1. 题目、标准答案和高质量AI解析已成功大批量录入刚刚创建的飞书表格中！\n2. 该批改标准已自动动态同步至右侧配置面板的系统提示词（Prompt）中！');
    }
  } catch (error) {
    console.error("同步至飞书失败:", error);
    alert("❌ 同步飞书失败，请确认应用是否拥有多维表格读写权限。\n原因：" + (error.response?.data?.detail || error.message));
  } finally {
    isSaving.value = false;
  }
};
</script>

<style scoped>
.teacher-view-container { display: flex; flex-direction: column; height: 100%; box-sizing: border-box;}

/* 🌟 新建表格专属卡片样式 */
.setup-card { background: #fff; border: 1px solid #91d5ff; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 12px rgba(24,144,255,0.08); border-left: 5px solid #1890ff; }
.setup-info h4 { margin: 0 0 6px 0; font-size: 16px; color: #1f1f1f; }
.setup-info p { margin: 0; font-size: 13px; color: #8c8c8c; }
.setup-actions { display: flex; gap: 10px; align-items: center; }
.setup-actions input { padding: 9px 12px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 13px; width: 240px; outline: none; transition: 0.2s; }
.setup-actions input:focus { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
.btn-create { background: #fa8c16; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; transition: 0.2s;}
.btn-create:hover:not(:disabled) { background: #ff9c3a; }
.btn-create:disabled { background: #ffd591; cursor: not-allowed; }

.action-header { padding-bottom: 20px; border-bottom: 1px solid #ebeef5; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;}
.header-left h3 { margin: 0 0 8px 0; font-size: 18px; color: #303133; }
.sub-title { margin: 0; font-size: 13px; color: #909399; }

.btn-primary { background-color: #1890ff; color: white; border: none; padding: 10px 16px; border-radius: 6px; cursor: pointer; transition: 0.2s; font-weight: 500;}
.btn-primary:hover { background-color: #40a9ff; }

.split-workspace { display: flex; flex: 1; gap: 20px; overflow: hidden; }

.panel-left { flex: 45; display: flex; flex-direction: column; background: #f9fafc; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden;}
.panel-title { padding: 14px 16px; background: #fff; border-bottom: 1px solid #ebeef5; font-weight: 600; font-size: 14px; color: #333;}
.flex-between { display: flex; justify-content: space-between; align-items: center; }

.image-viewer { flex: 1; padding: 20px; display: flex; justify-content: center; overflow: auto; }
.image-viewer img { max-width: 100%; object-fit: contain; box-shadow: 0 2px 12px rgba(0,0,0,0.1); border-radius: 4px; background: #fff;}
.empty-image { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #c0c4cc; width: 100%; height: 100%; border: 2px dashed #dcdfe6; border-radius: 8px;}
.empty-icon { font-size: 48px; margin-bottom: 16px; }

.panel-right { flex: 55; display: flex; flex-direction: column; background: #fff; border: 1px solid #ebeef5; border-radius: 8px; overflow: hidden;}
.btn-extract { background-color: #722ed1; color: white; border: none; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: bold; transition: 0.2s;}
.btn-extract:hover:not(:disabled) { background-color: #9254de; }
.btn-extract:disabled { background-color: #d3adf7; cursor: not-allowed; }

.rule-content { flex: 1; padding: 20px; overflow-y: auto; background: #fafafa;}
.empty-rule { height: 100%; display: flex; align-items: center; justify-content: center; color: #909399; }

.total-score-box { background: #e6f7ff; border: 1px solid #91d5ff; padding: 12px; border-radius: 6px; color: #1890ff; text-align: center; margin-bottom: 20px; font-size: 14px; font-weight: 500;}
.total-score-box strong { font-size: 18px; color: #0050b3;}

.question-list { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;}
.question-item { background: #fff; border: 1px solid #e4e7ed; border-radius: 8px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.01); display: flex; flex-direction: column; gap: 12px;}
.q-header { display: flex; gap: 12px; align-items: center; border-bottom: 1px dashed #f0f0f0; padding-bottom: 8px; margin: 0;}
.q-num { font-weight: bold; color: #1f1f1f; font-size: 15px;}
.q-type { background: #f5f5f5; color: #555; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500;}
.q-score { color: #f5222d; font-weight: bold; margin-left: auto; font-size: 14px;}

.q-body { display: flex; flex-direction: column; gap: 8px; font-size: 13px; line-height: 1.5;}
.q-text { color: #262626; background: #fafafa; padding: 8px 12px; border-radius: 6px;}
.q-answer { color: #52c41a; font-weight: 500;}
.ans-badge { background: #f6ffed; border: 1px solid #b7eb8f; padding: 1px 8px; border-radius: 4px; margin-left: 4px;}
.q-analysis { color: #8c8c8c; background: #fffbe6; border: 1px solid #ffe58f; padding: 10px 12px; border-radius: 6px; white-space: pre-wrap;}

.btn-save-rule { width: 100%; background: #52c41a; color: white; border: none; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; transition: 0.2s;}
.btn-save-rule:hover:not(:disabled) { background: #73d13d; }
.btn-save-rule:disabled { background: #b7eb8f; cursor: not-allowed; }

.spin { animation: spin 1s linear infinite; display: inline-block; }
@keyframes spin { 100% { transform: rotate(360deg); } }
</style>