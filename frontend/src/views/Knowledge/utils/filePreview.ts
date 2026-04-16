/**
 * 文件预览工具
 *
 * - 图片：ObjectURL 直接展示
 * - txt / md：读取为文本后原样展示（md 以源码显示；若需渲染可接入 markdown-it）
 * - excel (xlsx/xls/csv)：xlsx -> sheet_to_html，兼容大多数工作簿
 * - word：.docx 通过 mammoth 转 HTML；.doc 旧格式浏览器侧无法稳定预览，给出提示
 */

import * as mammoth from 'mammoth'
import * as XLSX from 'xlsx'
import type { FilePreviewType } from '@/types/knowledge'
import { getExtensionLower } from './fileAccept'

/** 根据文件名推断预览类型 */
export function inferPreviewType(fileName: string): FilePreviewType {
  const ext = getExtensionLower(fileName)
  if (['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) return 'image'
  if (ext === 'txt') return 'text'
  if (ext === 'md' || ext === 'markdown') return 'markdown'
  if (['xlsx', 'xls', 'csv'].includes(ext)) return 'excel'
  if (ext === 'docx' || ext === 'doc') return 'word'
  return 'unsupported'
}

/** 释放 ObjectURL（避免内存泄漏） */
export function revokeIfObjectUrl(url?: string) {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url)
  }
}

export interface BuildPreviewContentResult {
  previewType: FilePreviewType
  imageUrl?: string
  textContent?: string
  htmlContent?: string
  errorMessage?: string
}

/** 浏览器端根据 Blob 构建预览内容 */
export async function buildPreviewFromBlob(
  fileName: string,
  blob: Blob,
): Promise<BuildPreviewContentResult> {
  const previewType = inferPreviewType(fileName)

  if (previewType === 'image') {
    return { previewType, imageUrl: URL.createObjectURL(blob) }
  }

  if (previewType === 'text' || previewType === 'markdown') {
    return { previewType, textContent: await blob.text() }
  }

  if (previewType === 'excel') {
    try {
      const buf = await blob.arrayBuffer()
      const wb = XLSX.read(buf, { type: 'array' })
      const firstName = wb.SheetNames[0]
      if (!firstName) {
        return { previewType, errorMessage: '表格中没有可用的工作表。' }
      }
      const html = XLSX.utils.sheet_to_html(wb.Sheets[firstName], {
        id: 'knowledge-xlsx-preview',
        editable: false,
      })
      return { previewType, htmlContent: html }
    } catch {
      return {
        previewType,
        errorMessage: '无法解析该表格文件，可能已损坏或受密码保护。',
      }
    }
  }

  if (previewType === 'word') {
    const ext = getExtensionLower(fileName)
    if (ext === 'doc') {
      return {
        previewType,
        errorMessage: '旧版 .doc 在浏览器中无法稳定预览，请下载后使用 Word 打开。',
      }
    }
    try {
      const arrayBuffer = await blob.arrayBuffer()
      const { value: html } = await mammoth.convertToHtml({ arrayBuffer })
      return { previewType, htmlContent: html }
    } catch {
      return {
        previewType,
        errorMessage: '无法解析该 Word 文件，可能已损坏或包含不兼容的内容。',
      }
    }
  }

  return { previewType, errorMessage: '暂不支持该文件类型的在线预览。' }
}
