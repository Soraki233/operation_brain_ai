/**
 * 文本预处理 / Markdown 渲染
 *
 * 共享单例 markdown-it 实例：
 * - html: false，禁止写入裸 HTML，避免 XSS
 * - linkify: true，自动把 URL 识别成链接
 * - breaks: true，在流式 token 到来时也能按单换行符换行
 * - highlight: 通过 highlight.js 做代码块高亮
 *
 * 统一用 md.render(...) 把 LLM 返回的 Markdown 文本预处理为 HTML。
 */
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        const { value } = hljs.highlight(str, { language: lang, ignoreIllegals: true })
        return `<pre class="hljs"><code class="language-${lang}">${value}</code></pre>`
      } catch {
        // fallthrough
      }
    }
    try {
      const { value } = hljs.highlightAuto(str)
      return `<pre class="hljs"><code>${value}</code></pre>`
    } catch {
      return `<pre class="hljs"><code>${escapeHtml(str)}</code></pre>`
    }
  },
})

/** 所有外链默认新窗口打开 */
const defaultLinkOpen = md.renderer.rules.link_open
md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')
  const href = hrefIndex >= 0 ? token.attrs![hrefIndex][1] : ''
  if (/^https?:\/\//.test(href)) {
    token.attrSet('target', '_blank')
    token.attrSet('rel', 'noopener noreferrer')
  }
  return defaultLinkOpen
    ? defaultLinkOpen(tokens, idx, options, env, self)
    : self.renderToken(tokens, idx, options)
}

/** 便捷渲染方法 */
export function renderMarkdown(text: string): string {
  if (!text) return ''
  return md.render(text)
}
