import { computed, reactive, ref } from 'vue'
import { fileUrl } from '../api/client'
import { createDownload, getConfig, getDirectUrl, getDownload, parseVideo } from '../api/video'
import { chatWithVideo, summarizeVideo } from '../api/summarize'
import { useToast } from './useToast'

const emptySummary = () => ({
  status: 'idle',
  segments: [],
  language: '',
  languageName: '',
  source: '',
  fullText: '',
  truncated: false,
  text: '',
  mindmap: '',
  message: '',
  error: null,
  done: false,
  asr: false,
  asrStage: '',
  asrInfo: null,
  progress: 0,
})

const emptyDownload = () => ({
  status: 'idle',
  progress: 0,
  stage: '',
  filename: '',
  filesize: null,
  error: null,
  errorCode: null,
  jobId: null,
})

const emptyChat = () => ({
  messages: [],
  streaming: false,
  error: null,
})

export function useWorkbench() {
  const toast = useToast()

  const config = reactive({
    loaded: false,
    ai_enabled: false,
    ai_model: null,
    bilibili_logged_in: false,
    max_file_size_mb: 2048,
    asr: null,
  })

  const phase = ref('idle')
  const url = ref('')
  const error = ref('')
  const video = ref(null)
  const selectedId = ref('')

  const summary = reactive(emptySummary())
  const download = reactive(emptyDownload())
  const chat = reactive(emptyChat())
  const direct = reactive({ status: 'idle', url: '', filename: '', error: '' })

  const selectedFormat = computed(
    () => video.value?.formats.find((item) => item.id === selectedId.value) || null,
  )
  const videoFormats = computed(
    () => video.value?.formats.filter((item) => item.kind === 'video') || [],
  )
  const audioFormats = computed(
    () => video.value?.formats.filter((item) => item.kind === 'audio') || [],
  )
  const aiEnabled = computed(() => Boolean(config.ai_enabled))
  const canChat = computed(() => summary.segments.length > 0)

  let configPromise = null
  let parseSeq = 0
  let summarySeq = 0
  let summaryController = null
  let chatController = null
  let pollSeq = 0

  async function loadConfig(force = false) {
    if (config.loaded && !force) return config
    if (!configPromise) {
      configPromise = getConfig()
        .then((data) => {
          Object.assign(config, data, { loaded: true })
          return config
        })
        .catch(() => config)
        .finally(() => {
          configPromise = null
        })
    }
    return configPromise
  }

  function resetSummary() {
    Object.assign(summary, emptySummary())
  }

  function resetDownload() {
    Object.assign(download, emptyDownload())
  }

  function resetChat() {
    chatController?.abort()
    chatController = null
    Object.assign(chat, emptyChat())
  }

  function stopSummary() {
    summarySeq += 1
    summaryController?.abort()
    summaryController = null
  }

  function stopPolling() {
    pollSeq += 1
  }

  function setError(message) {
    error.value = message || '请求失败，请稍后重试。'
  }

  async function parse(input) {
    const text = String(input ?? url.value ?? '').trim()
    if (!text) {
      setError('请先粘贴一个视频链接。')
      return
    }
    const seq = ++parseSeq
    stopSummary()
    stopPolling()
    resetSummary()
    resetDownload()
    resetChat()
    direct.status = 'idle'
    direct.url = ''
    direct.error = ''
    phase.value = 'parsing'
    error.value = ''
    video.value = null
    url.value = text

    try {
      const data = await parseVideo(text)
      if (seq !== parseSeq) return
      video.value = data
      const recommended =
        data.formats.find((item) => item.recommended) ||
        data.formats.find((item) => item.kind === 'video') ||
        data.formats[0]
      selectedId.value = recommended?.id || ''
      phase.value = 'ready'
      await loadConfig()
      if (seq !== parseSeq) return
      runSummary()
    } catch (exc) {
      if (seq !== parseSeq) return
      phase.value = 'error'
      setError(exc?.message)
    }
  }

  async function runSummary(options = {}) {
    if (!video.value) return
    const allowAsr = Boolean(options.allowAsr)
    const previousAsrInfo = allowAsr && summary.asrInfo ? { ...summary.asrInfo } : null
    stopSummary()
    const seq = summarySeq
    resetSummary()
    if (previousAsrInfo) summary.asrInfo = previousAsrInfo
    summary.status = 'running'
    summary.message = '正在提取字幕…'
    const controller = new AbortController()
    summaryController = controller

    try {
      await summarizeVideo(video.value.webpage_url || url.value, {
        signal: controller.signal,
        allowAsr,
        onEvent(event, data) {
          if (seq !== summarySeq) return
          if (event === 'status') {
            summary.message = data?.message || summary.message
            summary.asrStage = data?.stage === 'asr' ? 'asr' : ''
            if (typeof data?.progress === 'number') summary.progress = data.progress
          } else if (event === 'subtitle') {
            summary.segments = data?.segments || []
            summary.language = data?.language || ''
            summary.languageName = data?.language_name || ''
            summary.source = data?.source || ''
            summary.fullText = data?.full_text || ''
            summary.truncated = Boolean(data?.truncated)
            summary.asr = Boolean(data?.asr)
            summary.asrStage = ''
            summary.asrInfo = null
            summary.progress = 100
            summary.message = '字幕已提取，正在生成总结…'
          } else if (event === 'summary') {
            summary.text += data?.delta || ''
          } else if (event === 'mindmap') {
            summary.mindmap = data?.markdown || ''
          } else if (event === 'error') {
            summary.error = {
              code: data?.code || 'summary_error',
              message: data?.message || 'AI 总结失败，请稍后重试。',
            }
            if (data?.code === 'no_subtitles') {
              summary.asrInfo = data
            }
          } else if (event === 'done') {
            summary.done = true
          }
        },
      })
      if (seq !== summarySeq) return
      summary.status = summary.error ? 'error' : 'ready'
      if (summary.error && !summary.segments.length) {
        summary.message = ''
      }
    } catch (exc) {
      if (exc?.name === 'AbortError' || seq !== summarySeq) return
      summary.status = 'error'
      summary.error = {
        code: exc?.code || 'network',
        message: exc?.message || 'AI 服务连接失败，请稍后重试。',
      }
    } finally {
      if (seq === summarySeq) summaryController = null
    }
  }

  function startAsr() {
    return runSummary({ allowAsr: true })
  }

  async function startDownload() {
    if (!video.value || !selectedId.value) return
    stopPolling()
    const seq = pollSeq
    resetDownload()
    download.status = 'preparing'
    download.stage = '正在创建下载任务…'
    download.progress = 1

    try {
      const created = await createDownload(video.value.webpage_url || url.value, selectedId.value)
      if (seq !== pollSeq) return
      download.jobId = created.job_id
      for (let attempt = 0; attempt < 900; attempt += 1) {
        if (seq !== pollSeq) return
        const job = await getDownload(created.job_id)
        if (seq !== pollSeq) return
        download.status = job.status
        download.progress = job.progress || 0
        download.stage = job.stage || ''
        download.filename = job.filename || ''
        download.filesize = job.filesize || null
        download.error = job.error || null
        download.errorCode = job.error_code || null
        if (job.status === 'ready') {
          if (job.mode === 'direct' && job.direct_url) {
            triggerUrl(job.direct_url)
          } else {
            triggerFile(job.id, job.filename)
          }
          download.status = 'done'
          download.progress = 100
          download.stage = '已交给浏览器下载'
          return
        }
        if (job.status === 'error') {
          throw new Error(job.error || '下载失败，请稍后重试。')
        }
        await sleep(800)
      }
      throw new Error('下载准备超时，请稍后重试。')
    } catch (exc) {
      if (seq !== pollSeq) return
      download.status = 'error'
      download.error = exc?.message || '下载失败，请稍后重试。'
      download.stage = ''
      toast.error(download.error)
    }
  }

  async function ask(question) {
    const text = String(question || '').trim()
    if (!text || !video.value || chat.streaming) return
    const history = chat.messages
      .filter((message) => !message.pending && message.content)
      .slice(-8)
      .map((message) => ({ role: message.role, content: message.content }))
    chat.messages.push({ role: 'user', content: text })
    const assistant = reactive({ role: 'assistant', content: '', pending: true })
    chat.messages.push(assistant)
    chat.error = null
    chat.streaming = true
    const controller = new AbortController()
    chatController = controller

    try {
      await chatWithVideo(
        {
          url: video.value.webpage_url || url.value,
          question: text,
          subtitle_text: summary.fullText,
          history,
        },
        {
          signal: controller.signal,
          onEvent(event, data) {
            if (event === 'answer') {
              assistant.content += data?.delta || ''
            } else if (event === 'error') {
              chat.error = data?.message || 'AI 问答失败，请稍后重试。'
            }
          },
        },
      )
      if (!assistant.content && chat.error) {
        const index = chat.messages.indexOf(assistant)
        if (index >= 0) chat.messages.splice(index, 1)
      }
    } catch (exc) {
      if (exc?.name !== 'AbortError') {
        chat.error = exc?.message || 'AI 问答失败，请稍后重试。'
      }
      if (!assistant.content) {
        const index = chat.messages.indexOf(assistant)
        if (index >= 0) chat.messages.splice(index, 1)
      }
    } finally {
      assistant.pending = false
      chat.streaming = false
      if (chatController === controller) chatController = null
    }
  }

  async function copyDirect() {
    if (!video.value || !selectedId.value) return
    direct.status = 'loading'
    direct.error = ''
    try {
      const data = await getDirectUrl(video.value.webpage_url || url.value, selectedId.value)
      direct.url = data.direct_url
      direct.filename = data.filename
      const copied = await copyText(data.direct_url)
      direct.status = 'ready'
      if (copied) {
        toast.success('直链已复制到剪贴板')
      } else {
        toast.info('直链已生成，请在下方手动复制')
      }
    } catch (exc) {
      direct.status = 'error'
      direct.error = exc?.message || '直链暂不可用'
      toast.error(direct.error)
    }
  }

  function selectFormat(id) {
    selectedId.value = id
    resetDownload()
    direct.status = 'idle'
    direct.url = ''
    direct.error = ''
  }

  function reset() {
    parseSeq += 1
    stopSummary()
    stopPolling()
    resetChat()
    resetSummary()
    resetDownload()
    video.value = null
    selectedId.value = ''
    url.value = ''
    error.value = ''
    phase.value = 'idle'
    direct.status = 'idle'
    direct.url = ''
    direct.error = ''
  }

  function clearError() {
    error.value = ''
  }

  return {
    config,
    phase,
    url,
    error,
    video,
    selectedId,
    selectedFormat,
    videoFormats,
    audioFormats,
    summary,
    download,
    chat,
    direct,
    aiEnabled,
    canChat,
    loadConfig,
    parse,
    runSummary,
    startAsr,
    startDownload,
    copyDirect,
    ask,
    selectFormat,
    reset,
    clearError,
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    let ok = false
    try {
      ok = document.execCommand('copy')
    } catch {
      ok = false
    }
    textarea.remove()
    return ok
  }
}

function triggerFile(jobId, filename) {
  const anchor = document.createElement('a')
  anchor.href = fileUrl(jobId)
  if (filename) anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

function triggerUrl(url) {
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
