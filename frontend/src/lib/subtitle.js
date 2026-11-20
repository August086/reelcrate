function clockParts(value) {
  const totalMs = Math.max(0, Math.round(Number(value || 0) * 1000))
  const hours = Math.floor(totalMs / 3_600_000)
  const minutes = Math.floor((totalMs % 3_600_000) / 60_000)
  const seconds = Math.floor((totalMs % 60_000) / 1000)
  const millis = totalMs % 1000
  return { hours, minutes, seconds, millis }
}

function srtTime(value) {
  const part = clockParts(value)
  return `${String(part.hours).padStart(2, '0')}:${String(part.minutes).padStart(2, '0')}:${String(part.seconds).padStart(2, '0')},${String(part.millis).padStart(3, '0')}`
}

function vttTime(value) {
  const part = clockParts(value)
  return `${String(part.hours).padStart(2, '0')}:${String(part.minutes).padStart(2, '0')}:${String(part.seconds).padStart(2, '0')}.${String(part.millis).padStart(3, '0')}`
}

export function toSrt(segments) {
  return `\ufeff${(segments || [])
    .map((segment, index) => {
      const start = srtTime(segment.start)
      const end = srtTime(segment.end)
      return `${index + 1}\n${start} --> ${end}\n${segment.text}`
    })
    .join('\n\n')}\n`
}

export function toVtt(segments) {
  const body = (segments || [])
    .map((segment) => `${vttTime(segment.start)} --> ${vttTime(segment.end)}\n${segment.text}`)
    .join('\n\n')
  return `WEBVTT\n\n${body}\n`
}

export function toTxt(segments, withTimestamps = true) {
  return (segments || [])
    .map((segment) =>
      withTimestamps ? `[${formatClock(segment.start)}] ${segment.text}` : segment.text,
    )
    .join('\n')
}

export function buildSubtitleFile(segments, format) {
  if (format === 'srt') return { text: toSrt(segments), ext: 'srt', mime: 'application/x-subrip' }
  if (format === 'vtt') return { text: toVtt(segments), ext: 'vtt', mime: 'text/vtt' }
  return { text: toTxt(segments), ext: 'txt', mime: 'text/plain' }
}

export function safeFileBase(title) {
  return String(title || '字幕')
    .replace(/[\\/:*?"<>|\u0000-\u001f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 80) || '字幕'
}

export function downloadText(text, filename, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([text], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1500)
}

export function exportSubtitles(segments, format, title) {
  const { text, ext, mime } = buildSubtitleFile(segments, format)
  downloadText(text, `${safeFileBase(title)}.${ext}`, `${mime};charset=utf-8`)
}
