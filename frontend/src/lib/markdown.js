import DOMPurify from 'dompurify'
import { marked } from 'marked'

marked.setOptions({
  gfm: true,
  breaks: true,
})

let hookInstalled = false
if (!hookInstalled) {
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    if (node.tagName === 'A') {
      node.setAttribute('target', '_blank')
      node.setAttribute('rel', 'noopener noreferrer')
    }
  })
  hookInstalled = true
}

export function renderMarkdown(markdown) {
  if (!markdown) return ''
  const html = marked.parse(markdown, { async: false })
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['target'],
    USE_PROFILES: { html: true },
  })
}

export function plainText(markdown) {
  if (!markdown) return ''
  const div = document.createElement('div')
  div.innerHTML = renderMarkdown(markdown)
  return div.textContent || ''
}
