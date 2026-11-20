<script setup>
import { computed } from 'vue'
import { AudioLines, Check, Info, Layers } from '@lucide/vue'
import { formatBytes } from '../lib/format'

const props = defineProps({
  formats: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
  notes: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const videoFormats = computed(() => props.formats.filter((item) => item.kind === 'video'))
const audioFormats = computed(() => props.formats.filter((item) => item.kind === 'audio'))
const selected = computed(() => props.formats.find((item) => item.id === props.modelValue))

function choose(id) {
  emit('update:modelValue', id)
}
</script>

<template>
  <div class="card p-4 sm:p-5">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-cobalt-50 text-cobalt-600">
          <Layers :size="15" />
        </span>
        <h3 class="text-[13px] font-bold text-ink">选择清晰度</h3>
      </div>
      <span class="text-[11px] font-medium text-slate-400">
        {{ videoFormats.length }} 档可下载
      </span>
    </div>

    <div v-if="videoFormats.length" class="mt-3 grid grid-cols-2 gap-2">
      <button
        v-for="format in videoFormats"
        :key="format.id"
        type="button"
        class="group relative flex min-h-[65px] flex-col justify-between rounded-xl border px-3 py-2.5 text-left transition duration-200"
        :class="
          modelValue === format.id
            ? 'border-cobalt-400 bg-cobalt-50/70 shadow-[0_0_0_3px_rgba(23,119,255,.08)]'
            : 'border-line bg-white hover:border-cobalt-200 hover:bg-cobalt-50/30'
        "
        :aria-pressed="modelValue === format.id"
        @click="choose(format.id)"
      >
        <span class="flex items-start justify-between gap-1">
          <span class="text-[14px] font-black tracking-tight text-ink">{{ format.label }}</span>
          <span
            v-if="format.recommended"
            class="rounded-full bg-cobalt-500 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-wider text-white"
          >
            推荐
          </span>
          <span
            v-else-if="modelValue === format.id"
            class="flex h-4 w-4 items-center justify-center rounded-full bg-cobalt-500 text-white"
          >
            <Check :size="10" :stroke-width="3" />
          </span>
        </span>
        <span class="mt-1 line-clamp-1 text-[10px] font-medium text-slate-400">{{ format.quality }}</span>
        <span class="mt-0.5 text-[10px] font-semibold text-slate-500">
          {{ format.filesize ? `约 ${formatBytes(format.filesize)}` : '大小待计算' }}
        </span>
      </button>
    </div>

    <button
      v-for="format in audioFormats"
      :key="format.id"
      type="button"
      class="mt-2 flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left transition"
      :class="
        modelValue === format.id
          ? 'border-cobalt-400 bg-cobalt-50/70'
          : 'border-line bg-white hover:border-cobalt-200 hover:bg-cobalt-50/30'
      "
      :aria-pressed="modelValue === format.id"
      @click="choose(format.id)"
    >
      <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
        <AudioLines :size="16" />
      </span>
      <span class="min-w-0 flex-1">
        <span class="flex items-center gap-2 text-[12px] font-bold text-ink">
          {{ format.label }}
          <span v-if="format.note" class="truncate text-[9px] font-medium text-slate-400">{{ format.note }}</span>
        </span>
        <span class="mt-0.5 block text-[10px] text-slate-400">
          {{ format.quality }} · {{ format.filesize ? formatBytes(format.filesize) : '大小待计算' }}
        </span>
      </span>
      <span
        class="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border"
        :class="modelValue === format.id ? 'border-cobalt-500 bg-cobalt-500 text-white' : 'border-slate-200 text-transparent'"
      >
        <Check :size="11" :stroke-width="3" />
      </span>
    </button>

    <div class="mt-3 flex items-start gap-2 rounded-xl bg-paper px-3 py-2.5 text-[10px] leading-4 text-slate-400">
      <Info class="mt-0.5 shrink-0" :size="12" />
      <span>
        {{ selected?.needs_merge ? '该清晰度为视频与音频分离流，服务端会自动合并为 MP4。' : '下载文件会以原视频标题命名，中文文件名已做兼容处理。' }}
      </span>
    </div>

    <div v-if="notes.length" class="mt-2 space-y-1.5">
      <p v-for="(note, index) in notes.slice(0, 2)" :key="index" class="flex items-start gap-1.5 text-[10px] leading-4 text-slate-400">
        <span class="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-gold" />
        {{ note }}
      </p>
    </div>
  </div>
</template>
