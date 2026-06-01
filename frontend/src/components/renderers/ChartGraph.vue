<template>
  <div class="w-full mt-6 bg-white rounded-xl border border-slate-200 shadow-sm p-4 relative group">
    <div class="text-xs text-slate-400 font-bold mb-2 uppercase tracking-widest border-b pb-2 flex justify-between items-center">
      <span>🕸️ 演化时间轴网络图谱</span>
      <div class="flex items-center gap-2">
        <span class="text-blue-500 bg-blue-50 px-2 py-0.5 rounded cursor-help hidden sm:inline">🖱️ 滚轮缩放 / 左键拖动调整</span>
        <button @click="resetGraph" class="text-white bg-indigo-500 hover:bg-indigo-600 px-3 py-1 rounded shadow-sm transition-all active:scale-95 flex items-center gap-1">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          重置排版
        </button>
      </div>
    </div>
    <div ref="graphRef" class="w-full h-[550px]"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({ data: Object });
const graphRef = ref(null);
let myChart = null, obs = null;

const renderGraph = () => {
  if (!graphRef.value || !props.data) return;
  if (!myChart) {
    myChart = echarts.init(graphRef.value);
    obs = new ResizeObserver(() => myChart?.resize());
    obs.observe(graphRef.value);
  }

  try {
    let rawNodes = props.data.series?.[0]?.data || props.data.series?.[0]?.nodes || props.data.nodes || props.data.data || [];
    let rawLinks = props.data.series?.[0]?.links || props.data.series?.[0]?.edges || props.data.links || props.data.edges || [];
    if (rawNodes.length === 0) return;

    const inDegree = {}; const outEdges = {};
    rawNodes.forEach(n => { const id = String(n.id ?? n.name); inDegree[id] = 0; outEdges[id] = []; });
    rawLinks.forEach(l => {
      const src = String(l.source), tgt = String(l.target);
      if (outEdges[src]) outEdges[src].push(tgt);
      if (inDegree[tgt] !== undefined) inDegree[tgt]++;
    });

    let queue = rawNodes.map(n => String(n.id ?? n.name)).filter(id => inDegree[id] === 0);
    if (queue.length === 0 && rawNodes.length > 0) queue.push(String(rawNodes[0].id ?? rawNodes[0].name));

    const depths = {}; queue.forEach(q => depths[q] = 0);
    let safety = 0;
    while(queue.length > 0 && safety++ < 10000) {
      const curr = queue.shift(), currDepth = depths[curr];
      (outEdges[curr] || []).forEach(neighbor => {
        if (depths[neighbor] === undefined || depths[neighbor] < currDepth + 1) {
          depths[neighbor] = currDepth + 1; queue.push(neighbor);
        }
      });
    }

    const depthGroups = {}; let maxDepth = 0;
    rawNodes.forEach(n => {
      const d = depths[String(n.id ?? n.name)] || 0;
      maxDepth = Math.max(maxDepth, d);
      if (!depthGroups[d]) depthGroups[d] = [];
      depthGroups[d].push(String(n.id ?? n.name));
    });

    const w = graphRef.value.clientWidth || 800, h = graphRef.value.clientHeight || 550;
    const dynamicZoom = (maxDepth * 160 > w) ? (maxDepth * 160) / w : 1;
    const xStep = maxDepth === 0 ? 0 : (w - 160) / maxDepth;
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];

    const timelineNodes = rawNodes.map((node, index) => {
      const d = depths[String(node.id ?? node.name)] || 0;
      const group = depthGroups[d];
      let staggerY = (group.length === 1 && d % 2 === 0) ? -40 : (group.length === 1 ? 40 : 0);
      return {
        ...node, name: node.name || `节点${index}`, symbolSize: node.symbolSize || 45,
        x: 80 + d * xStep, y: (h / (group.length + 1)) * (group.indexOf(String(node.id ?? node.name)) + 1) + staggerY,
        itemStyle: { color: node.itemStyle?.color || colors[(node.category || index) % colors.length], borderColor: '#ffffff', borderWidth: 2, shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.1)' }
      };
    });

    myChart.setOption({
      tooltip: { formatter: p => p.dataType === 'node' ? `实体: ${p.data.name}` : `关系: ${p.data.name || '关联'}` },
      animationDurationUpdate: 1000, animationEasingUpdate: 'quinticInOut',
      series: [{
         type: 'graph', layout: 'none', roam: true, draggable: true, zoom: dynamicZoom,
         emphasis: { focus: 'adjacency', lineStyle: { width: 4 } },
         label: { show: true, position: 'bottom', distance: 10, formatter: '{b}', fontSize: 13, color: '#1e293b', fontWeight: 'bold', textBorderColor: '#ffffff', textBorderWidth: 4 },
         edgeLabel: { show: true, fontSize: 11, color: '#475569', backgroundColor: 'rgba(255, 255, 255, 0.95)', padding: [3, 6], borderRadius: 4, formatter: x => x.data.name || x.data.value || '' },
         data: timelineNodes, links: rawLinks,
         edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [0, 10], lineStyle: { color: '#94a3b8', width: 2, curveness: 0.25 }
      }]
    }, true);
  } catch (err) { console.error("关系图谱渲染崩溃:", err); }
};

const resetGraph = () => { if (myChart) { myChart.clear(); renderGraph(); } };

onMounted(() => setTimeout(renderGraph, 150));
watch(() => props.data, renderGraph, { deep: true });
onBeforeUnmount(() => { obs?.disconnect(); myChart?.dispose(); });
</script>