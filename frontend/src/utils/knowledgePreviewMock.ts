import type { ExcelSheetHtml } from './knowledgePreview.types'

/** 无真实文件时的 Word 演示 HTML（与列表中示例 id=4 对应） */
export function getDemoWordHtml(fileId: string): string | null {
  if (fileId !== '4') return null
  return `
<div class="demo-docx-preview">
  <h2>系统架构说明</h2>
  <p>本文为知识库内置演示。上传真实的 <strong>.docx</strong> 后，将按文档结构转换为 HTML 预览（复杂排版可能与 Word 略有差异）。</p>
  <h3>1. 总体架构</h3>
  <p>运行智脑 AI 采用前后端分离架构，知识库文档解析后进入向量检索（RAG）流程。</p>
  <h3>2. 模块划分</h3>
  <ul>
    <li>前端：Vue 3 + Naive UI</li>
    <li>后端：API 与文档存储</li>
    <li>检索：嵌入模型与向量库</li>
  </ul>
</div>`
}

/** 无真实文件时的 Excel 演示（与列表中示例 id=2 对应） */
export function getMockExcelSheetsForDemo(): ExcelSheetHtml[] {
  return [
    {
      name: '巡检记录',
      html: `
<table>
  <thead><tr><th>巡检项</th><th>结果</th><th>备注</th><th>巡检时间</th></tr></thead>
  <tbody>
    <tr><td>CPU 负载</td><td>正常</td><td>峰值 72%</td><td>2026-04-12 09:15</td></tr>
    <tr><td>磁盘空间</td><td>正常</td><td>剩余 120GB</td><td>2026-04-12 09:15</td></tr>
    <tr><td>网络连通</td><td>正常</td><td>—</td><td>2026-04-12 09:15</td></tr>
  </tbody>
</table>`,
    },
  ]
}
