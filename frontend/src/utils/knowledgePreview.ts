import mammoth from 'mammoth'
import * as XLSX from 'xlsx'
import type { ExcelSheetHtml } from './knowledgePreview.types'

export type { ExcelSheetHtml } from './knowledgePreview.types'

export async function docxArrayBufferToHtml(buffer: ArrayBuffer): Promise<string> {
  const { value } = await mammoth.convertToHtml({ arrayBuffer: buffer })
  return value
}

export function excelArrayBufferToSheetHtmlList(buffer: ArrayBuffer): ExcelSheetHtml[] {
  const wb = XLSX.read(buffer, { type: 'array' })
  return wb.SheetNames.map((name) => {
    const sheet = wb.Sheets[name]
    if (!sheet) return { name, html: '<p>（空工作表）</p>' }
    return {
      name,
      html: XLSX.utils.sheet_to_html(sheet, { id: `sheet-preview-${name.replace(/\W/g, '_')}` }),
    }
  })
}
