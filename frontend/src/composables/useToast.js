import { ref } from 'vue'

const items = ref([])
let nextId = 1

function push(message, type = 'info', ttl = 3600) {
  if (!message) return
  const id = nextId++
  items.value.push({ id, message, type })
  setTimeout(() => dismiss(id), ttl)
}

function dismiss(id) {
  items.value = items.value.filter((item) => item.id !== id)
}

export function useToast() {
  return {
    items,
    push,
    dismiss,
    success: (message) => push(message, 'success'),
    error: (message) => push(message, 'error', 5000),
    info: (message) => push(message, 'info'),
  }
}
