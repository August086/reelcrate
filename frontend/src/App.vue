<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import AppFooter from './components/AppFooter.vue'
import AppHeader from './components/AppHeader.vue'
import FeatureBento from './components/FeatureBento.vue'
import HeroSection from './components/HeroSection.vue'
import PlatformMarquee from './components/PlatformMarquee.vue'
import PricingSection from './components/PricingSection.vue'
import ToastHost from './components/ToastHost.vue'
import WorkbenchSection from './components/WorkbenchSection.vue'
import { useWorkbench } from './composables/useWorkbench'

const workbench = useWorkbench()
const heroRef = ref(null)

const {
  config,
  phase,
  url,
  error,
  video,
  selectedId,
  selectedFormat,
  summary,
  chat,
  download,
  direct,
  aiEnabled,
  canChat,
  loadConfig,
  parse,
  runSummary,
  startDownload,
  startAsr,
  copyDirect,
  ask,
  selectFormat,
  reset,
} = workbench

const compact = computed(() => Boolean(video.value) || phase.value === 'parsing')

onMounted(() => {
  loadConfig()
})

watch(
  () => video.value,
  async (value) => {
    if (!value) return
    await nextTick()
    document.getElementById('workbench')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  },
)

function focusSearch() {
  heroRef.value?.focus()
}

function handleReset() {
  reset()
  nextTick(focusSearch)
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader @search="focusSearch" />

    <main>
      <HeroSection
        ref="heroRef"
        :compact="compact"
        :busy="phase === 'parsing'"
        :error="error"
        :initial-url="url"
        @parse="parse"
      />

      <WorkbenchSection
        v-if="video"
        :video="video"
        :selected-id="selectedId"
        :selected-format="selectedFormat"
        :summary="summary"
        :chat="chat"
        :download="download"
        :direct="direct"
        :ai-enabled="aiEnabled"
        :can-chat="canChat"
        :asr="config.asr || {}"
        @select="selectFormat"
        @download="startDownload"
        @direct="copyDirect"
        @summarize="runSummary"
        @asr="startAsr"
        @ask="ask"
        @reset="handleReset"
      />

      <FeatureBento />
      <PlatformMarquee />
      <PricingSection @search="focusSearch" />
    </main>

    <AppFooter />
    <ToastHost />
  </div>
</template>
