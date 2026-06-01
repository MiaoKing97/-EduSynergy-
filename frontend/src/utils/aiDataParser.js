export const extractJson = (str) => {
  const s = str.trim();
  const firstObj = s.indexOf('{');
  const firstArr = s.indexOf('[');
  let first = -1;
  if (firstObj !== -1 && firstArr !== -1) first = Math.min(firstObj, firstArr);
  else if (firstObj !== -1) first = firstObj;
  else if (firstArr !== -1) first = firstArr;

  const lastObj = s.lastIndexOf('}');
  const lastArr = s.lastIndexOf(']');
  let last = Math.max(lastObj, lastArr);

  if (first !== -1 && last !== -1 && last >= first) {
    return s.substring(first, last + 1);
  }
  return s;
};

export const parseAIContent = (rawText) => {
  let text = rawText;
  let echartsData = null, mermaidCode = null, wordCloudData = null, graphData = null;

  // 1. Graph 图谱
  const graphMatch = text.match(/```json_graph\s*([\s\S]*?)\s*```/);
  if (graphMatch) {
    try {
      graphData = JSON.parse(extractJson(graphMatch[1]));
      text = text.replace(graphMatch[0], '\n\n🕸️ [演化图谱渲染区]');
    } catch (e) {
      text = text.replace(graphMatch[0], '\n\n⚠️ [图谱JSON损坏，无法解析]');
    }
  }

  // 2. 词云
  const wcMatch = text.match(/```json_wordcloud\s*([\s\S]*?)\s*```/);
  if (wcMatch) {
    try {
      wordCloudData = JSON.parse(extractJson(wcMatch[1]));
      text = text.replace(wcMatch[0], '\n\n☁️ [多维词云渲染区]');
    } catch(e) {}
  }

  // 3. 兜底与嗅探
  const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    try {
      let parsed = JSON.parse(extractJson(jsonMatch[1]));
      if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].name !== undefined) {
        if (!wordCloudData) wordCloudData = parsed;
        text = text.replace(jsonMatch[0], '\n\n☁️ [多维词云渲染区 (自动纠正标签)]');
      } else if (parsed.nodes && parsed.links) {
        if (!graphData) graphData = parsed;
        text = text.replace(jsonMatch[0], '\n\n🕸️ [演化图谱渲染区 (自动纠正标签)]');
      } else {
        echartsData = parsed;
        text = text.replace(jsonMatch[0], '\n\n📊 [数据图表渲染区]');
      }
    } catch (e) {}
  }

  // 4. Mermaid
  const mermaidMatch = text.match(/```mermaid\s*([\s\S]*?)\s*```/);
  if (mermaidMatch) {
    mermaidCode = mermaidMatch[1];
    text = text.replace(mermaidMatch[0], '\n\n🧠 [结构导图渲染区]');
  }

  return { text, echartsData, mermaidCode, wordCloudData, graphData };
};