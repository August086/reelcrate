import { streamSSE } from '../lib/sse'
import { apiUrl } from './client'

export function summarizeVideo(url, { signal, onEvent, allowAsr = false }) {
  return streamSSE(
    apiUrl('/api/summarize'),
    { url, allow_asr: Boolean(allowAsr) },
    { signal, onEvent },
  )
}

export function chatWithVideo(payload, { signal, onEvent }) {
  return streamSSE(apiUrl('/api/chat'), payload, { signal, onEvent })
}
