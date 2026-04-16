/** 将字节数格式化为可读字符串，例如 1024 -> "1 KB" */
export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let v = bytes
  let i = 0
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024
    i += 1
  }
  const digits = i === 0 ? 0 : v < 10 ? 2 : v < 100 ? 1 : 0
  return `${v.toFixed(digits)} ${units[i]}`
}
