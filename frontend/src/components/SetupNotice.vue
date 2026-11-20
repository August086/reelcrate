<script setup>
import { Copy, KeyRound, ServerCog } from '@lucide/vue'
import { useToast } from '../composables/useToast'

const toast = useToast()

async function copyExample() {
  try {
    await navigator.clipboard.writeText('DEEPSEEK_API_KEY=sk-your-key')
    toast.success('配置示例已复制')
  } catch {
    toast.info('请手动复制配置示例')
  }
}
</script>

<template>
  <div class="rounded-2xl border border-amber-200/80 bg-[linear-gradient(135deg,#FFF9EC,#FFFFFF)] p-4 sm:p-5">
    <div class="flex items-start gap-3">
      <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700">
        <KeyRound :size="19" />
      </span>
      <div class="min-w-0">
        <p class="text-[13px] font-bold text-ink">字幕已就位，还差一把 AI 钥匙</p>
        <p class="mt-1 text-[11px] leading-5 text-slate-500">
          在 <code class="rounded bg-white px-1 py-0.5 font-mono text-[10px] text-amber-800">backend/.env</code>
          中设置 DeepSeek Key，重启后端后即可生成总结、导图与问答。
        </p>
        <div class="mt-3 flex items-start gap-2 rounded-xl border border-amber-100 bg-white/80 p-2.5">
          <ServerCog class="mt-0.5 shrink-0 text-slate-400" :size="13" />
          <code class="min-w-0 flex-1 break-all font-mono text-[10px] leading-4 text-slate-600">
            DEEPSEEK_API_KEY=sk-your-key
          </code>
          <button type="button" class="shrink-0 text-slate-400 transition hover:text-cobalt-600" aria-label="复制配置示例" @click="copyExample">
            <Copy :size="13" />
          </button>
        </div>
        <p class="mt-2 text-[10px] leading-4 text-slate-400">
          字幕提取不需要 Key；总结、导图、问答需要真实模型能力，不会用假数据兜底。
        </p>
      </div>
    </div>
  </div>
</template>
