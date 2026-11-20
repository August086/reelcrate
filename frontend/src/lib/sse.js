import { ApiError } from '../api/client'

function parseBlock(block, onEvent) {
  let event = 'message'
  const dataLines = []
  for (const line of block.split('\n')) {
    if (line.startsWith(':')) continue
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).replace(/^ /, ''))
    }
  }
  if (!dataLines.length) return
  const raw = dataLines.join('\n')
  let data = raw
  try {
    data = JSON.parse(raw)
  } catch {
    // Keep raw text for unknown event payloads.
  }
  onEvent(event, data)
}

export async function streamSSE(path, payload, { signal, onEvent }) {
  const response = await fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`
    let code = 'request_failed'
    try {
      const data = await response.json()
      message = data?.error || message
      code = data?.code || code
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(message, code, response.status)
  }
  if (!response.body) {
    throw new ApiError('当前浏览器不支持流式响应。', 'stream_unsupported')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
      let boundary = buffer.indexOf('\n\n')
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        if (block.trim()) parseBlock(block, onEvent)
        boundary = buffer.indexOf('\n\n')
      }
    }
    buffer += decoder.decode()
    if (buffer.trim()) parseBlock(buffer.replace(/\r\n/g, '\n'), onEvent)
  } finally {
    try {
      reader.releaseLock()
    } catch {
      // ignore
    }
  }
}
