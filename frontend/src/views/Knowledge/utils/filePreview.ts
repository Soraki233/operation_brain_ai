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
import type { FilePreviewType, PreviewSheet } from '@/types/knowledge'
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
  /** Excel 工作簿的全部 sheet（仅 excel 分支返回） */
  sheets?: PreviewSheet[]
  /** 默认展示的 sheet 名 */
  activeSheetName?: string
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
      // 1) blob 为空 = 后端物理文件已丢失 / 代理断流；丢给 XLSX.read 会抛
      //    "Cannot read properties of undefined (reading 'indexOf')"，这里提前拦掉。
      if (!blob || blob.size === 0) {
        return {
          previewType,
          errorMessage: '文件内容为空或已丢失，无法预览。请重新上传。',
        }
      }
      // 2) blob 其实是后端错误 JSON（被 responseType: 'blob' 包起来了），
      //    解析出 detail / message 给出准确提示。
      if (blob.type && blob.type.includes('application/json')) {
        let detail = ''
        try {
          const text = await blob.text()
          const obj = JSON.parse(text)
          detail = obj?.detail || obj?.message || text
        } catch {
          // ignore
        }
        return {
          previewType,
          errorMessage: `预览失败：${detail || '服务端返回的不是文件内容'}`,
        }
      }

      const buf = await blob.arrayBuffer()
      const bytes = new Uint8Array(buf)

      // 读魔数：xlsx 是 zip（PK\x03\x04），xls / 加密 OOXML 是 CFB（D0 CF 11 E0）。
      // 把魔数打到 console，方便在"indexOf undefined"这类报错时一眼看出文件到底是什么。
      const magic = Array.from(bytes.slice(0, 8))
        .map((b) => b.toString(16).padStart(2, '0'))
        .join(' ')
      const head4 = bytes.slice(0, 4)
      const isZip =
        head4[0] === 0x50 && head4[1] === 0x4b && head4[2] === 0x03 && head4[3] === 0x04
      const isCfb =
        head4[0] === 0xd0 && head4[1] === 0xcf && head4[2] === 0x11 && head4[3] === 0xe0

      if (!isZip && !isCfb) {
        // 常见为 html/pdf/txt 被误标扩展名，或 nginx/axios 把错包透传进来。
        console.warn('[filePreview] 非标准 Excel 文件魔数', { fileName, magic })
        const head = new TextDecoder('utf-8', { fatal: false }).decode(bytes.slice(0, 16))
        return {
          previewType,
          errorMessage: `该文件不是标准 Excel 格式（魔数：${magic}，开头："${head.trim()}"），请确认文件未被加密且扩展名与实际内容一致。`,
        }
      }

      // 不开 cellStyles：避免源文件里的隐藏行/列样式（display:none）被搬进
      // 预览 HTML 导致表头/数据行神秘消失。
      // cellDates: true 让日期列直接读成 JS Date，避免拿到 44927 这种 Excel 序列号。
      // 部分 SheetJS 版本的 'array' 分支需要真正的 Uint8Array，不能是原始 ArrayBuffer。
      const wb = XLSX.read(bytes, { type: 'array', cellDates: true })
      const sheetNames = wb.SheetNames || []
      if (!sheetNames.length) {
        return { previewType, errorMessage: '表格中没有可用的工作表。' }
      }

      // 每个 sheet 解析成 { columns, rows } 二维结构，交给 NDataTable 做虚拟滚动。
      // 统计非空单元格数量选出"最有料"的 sheet 作为默认打开项。
      let bestName = ''
      let bestSize = -1
      const sheets: PreviewSheet[] = sheetNames
        .map((name): PreviewSheet | null => {
          const ws = wb.Sheets[name]
          if (!ws) return null

          const ref = ws['!ref']
          // 空 sheet：!ref 是 undefined，给占位保留 tab
          if (!ref) {
            return { name, columns: [], rows: [], placeholder: '（此工作表没有数据）' }
          }

          try {
            const parsed = parseSheetToGrid(ws)
            if (!parsed.rows.length && !parsed.columns.length) {
              return {
                name,
                columns: [],
                rows: [],
                placeholder: '（此工作表没有数据）',
              }
            }
            const size = parsed.columns.length * parsed.rows.length
            if (size > bestSize) {
              bestSize = size
              bestName = name
            }
            return { name, columns: parsed.columns, rows: parsed.rows }
          } catch (err) {
            console.warn('[filePreview] 解析 sheet 失败', { name, ref, err })
            return {
              name,
              columns: [],
              rows: [],
              placeholder: `（工作表 "${name}" 渲染失败：${
                err instanceof Error ? err.message : String(err)
              }）`,
            }
          }
        })
        .filter((v): v is PreviewSheet => !!v)

      if (!sheets.length) {
        return { previewType, errorMessage: '表格中没有可用的工作表。' }
      }

      return {
        previewType,
        sheets,
        activeSheetName: bestName || sheets[0].name,
      }
    } catch (err) {
      // 把真实异常打到 console，避免被 catch 吞掉；同时把 message 透传给 UI，
      // 方便一眼看出到底是损坏、加密，还是 xlsx 库不支持的格式。
      console.error('[filePreview] xlsx 解析失败', { fileName, err })
      const reason = err instanceof Error ? err.message : String(err)
      return {
        previewType,
        errorMessage: `无法解析该表格文件，可能已损坏或受密码保护。${
          reason ? `（${reason}）` : ''
        }`,
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
    } catch (err) {
      console.error('[filePreview] word 解析失败', { fileName, err })
      const reason = err instanceof Error ? err.message : String(err)
      return {
        previewType,
        errorMessage: `无法解析该 Word 文件，可能已损坏或包含不兼容的内容。${
          reason ? `（${reason}）` : ''
        }`,
      }
    }
  }

  return { previewType, errorMessage: '暂不支持该文件类型的在线预览。' }
}

/** 把单个 SheetJS worksheet 扁平成 { columns, rows } 二维结构。
 *
 * - 展开合并单元格：把合并块左上角的值广播到整个 merge 区域，
 *   避免虚拟滚动到下半部分时一列全空；
 * - 自动识别表头行：在前 5 行里挑非空单元格最多的那一行当表头，
 *   兼容"第一行是大标题 / 第二行才是真实列名"的 Excel；
 * - Date 单元格格式化成 yyyy-MM-dd(HH:mm:ss)，避免 44927 这种序列号或 ISO 长串。
 */
function parseSheetToGrid(
  ws: XLSX.WorkSheet,
): { columns: string[]; rows: string[][] } {
  const aoa = XLSX.utils.sheet_to_json<unknown[]>(ws, {
    header: 1,
    raw: true,
    defval: null,
    blankrows: false,
  })
  if (!aoa.length) return { columns: [], rows: [] }

  // 1) 展开合并单元格
  const merges = ws['!merges']
  if (merges && merges.length) {
    for (const m of merges) {
      const srcRow = aoa[m.s.r]
      if (!srcRow) continue
      const srcVal = srcRow[m.s.c]
      for (let r = m.s.r; r <= m.e.r; r++) {
        if (!aoa[r]) aoa[r] = []
        for (let c = m.s.c; c <= m.e.c; c++) {
          if (r === m.s.r && c === m.s.c) continue
          const row = aoa[r] as unknown[]
          if (row[c] === null || row[c] === undefined || row[c] === '') {
            row[c] = srcVal
          }
        }
      }
    }
  }

  const maxCols = aoa.reduce((m, row) => Math.max(m, row?.length || 0), 0)
  if (!maxCols) return { columns: [], rows: [] }

  // 2) 选表头：前 5 行里非空单元格最多的行
  const probe = Math.min(5, aoa.length)
  let headerIdx = 0
  let headerFill = -1
  for (let i = 0; i < probe; i++) {
    const r = aoa[i] || []
    let fill = 0
    for (let c = 0; c < maxCols; c++) {
      const v = r[c]
      if (v !== null && v !== undefined && String(v).trim() !== '') fill++
    }
    if (fill > headerFill) {
      headerFill = fill
      headerIdx = i
    }
  }

  // 3) 生成 columns（保持原始表头名，允许重复）
  const headerRow = aoa[headerIdx] || []
  const columns: string[] = []
  for (let c = 0; c < maxCols; c++) {
    const label = formatCellValue(headerRow[c])
    columns.push(label || `列${c + 1}`)
  }

  // 4) 生成 rows：表头之后的所有行
  const rows: string[][] = []
  for (let i = headerIdx + 1; i < aoa.length; i++) {
    const src = aoa[i] || []
    const row: string[] = new Array(maxCols)
    let anyFilled = false
    for (let c = 0; c < maxCols; c++) {
      const s = formatCellValue(src[c])
      row[c] = s
      if (s) anyFilled = true
    }
    if (anyFilled) rows.push(row)
  }

  return { columns, rows }
}

/** 单元格值统一成字符串（日期 / 数字做可读化处理） */
function formatCellValue(v: unknown): string {
  if (v === null || v === undefined) return ''
  if (v instanceof Date) {
    const y = v.getFullYear()
    const mo = String(v.getMonth() + 1).padStart(2, '0')
    const d = String(v.getDate()).padStart(2, '0')
    const hh = v.getHours()
    const mm = v.getMinutes()
    const ss = v.getSeconds()
    if (hh === 0 && mm === 0 && ss === 0) return `${y}-${mo}-${d}`
    return `${y}-${mo}-${d} ${String(hh).padStart(2, '0')}:${String(mm).padStart(
      2,
      '0',
    )}:${String(ss).padStart(2, '0')}`
  }
  if (typeof v === 'number') {
    if (Number.isInteger(v)) return String(v)
    // 去掉无意义的长尾 0，又不破坏精度
    return Number(v.toFixed(6)).toString()
  }
  return String(v).trim()
}
