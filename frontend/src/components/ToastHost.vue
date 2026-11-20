<script setup>
import { CheckCircle2, AlertCircle, Info, X } from '@lucide/vue'
import { useToast } from '../composables/useToast'

const { items, dismiss } = useToast()
const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
}
</script>

<template>
  <div class="pointer-events-none fixed bottom-5 right-4 z-[90] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2 sm:right-6">
    <TransitionGroup
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-y-3 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="translate-y-2 opacity-0"
    >
      <div
        v-for="item in items"
        :key="item.id"
        class="pointer-events-auto flex items-start gap-3 rounded-2xl border border-line bg-white/95 p-3.5 shadow-soft backdrop-blur"
        role="status"
        aria-live="polite"
      >
        <span
          class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
          :class="{
            'bg-emerald-50 text-emerald-600': item.type === 'success',
            'bg-rose-50 text-rose-600': item.type === 'error',
            'bg-cobalt-50 text-cobalt-600': item.type === 'info',
          }"
        >
          <component :is="icons[item.type] || Info" :size="15" :stroke-width="2.2" />
        </span>
        <p class="flex-1 pt-1 text-[13px] font-medium leading-5 text-slate-700">{{ item.message }}</p>
        <button
          class="rounded-full p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          type="button"
          aria-label="关闭提示"
          @click="dismiss(item.id)"
        >
          <X :size="14" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
