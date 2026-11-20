export function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return '大小未知'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = Number(bytes)
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  const digits = value >= 100 || index === 0 ? 0 : value >= 10 ? 1 : 2
  return `${value.toFixed(digits)} ${units[index]}`
}

export function formatCount(value) {
  const number = Number(value || 0)
  if (!number) return ''
  if (number >= 100_000_000) return `${(number / 100_000_000).toFixed(1).replace(/\.0$/, '')} 亿`
  if (number >= 10_000) return `${(number / 10_000).toFixed(1).replace(/\.0$/, '')} 万`
  return new Intl.NumberFormat('zh-CN').format(number)
}

export function formatClock(seconds, withMillis = false) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0))
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const secs = total % 60
  const base = hours
    ? `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    : `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  if (!withMillis) return base
  const millis = Math.round((Number(seconds) % 1) * 1000)
  return `${base}.${String(millis).padStart(3, '0')}`
}

export function formatDuration(seconds) {
  return formatClock(seconds)
}

export function shortDate(value) {
  if (!value) return ''
  return String(value).replace(/-/g, '.')
}
