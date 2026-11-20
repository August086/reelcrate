function triggerDataUrl(dataUrl, filename) {
  const anchor = document.createElement('a')
  anchor.href = dataUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  triggerDataUrl(url, filename)
  setTimeout(() => URL.revokeObjectURL(url), 1500)
}

export function exportMindmapSvg(svgElement, filename = 'mindmap.svg') {
  if (!svgElement) throw new Error('思维导图还没有准备好')
  const clone = svgElement.cloneNode(true)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink')

  let viewBox = svgElement.viewBox?.baseVal
  if (!viewBox || !viewBox.width || !viewBox.height) {
    const rect = svgElement.getBoundingClientRect()
    clone.setAttribute('viewBox', `0 0 ${Math.max(1, rect.width)} ${Math.max(1, rect.height)}`)
    viewBox = { x: 0, y: 0, width: rect.width, height: rect.height }
  }
  clone.setAttribute('width', String(Math.round(viewBox.width)))
  clone.setAttribute('height', String(Math.round(viewBox.height)))

  const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
  background.setAttribute('x', String(viewBox.x))
  background.setAttribute('y', String(viewBox.y))
  background.setAttribute('width', String(viewBox.width))
  background.setAttribute('height', String(viewBox.height))
  background.setAttribute('fill', '#ffffff')
  clone.insertBefore(background, clone.firstChild)

  const source = new XMLSerializer().serializeToString(clone)
  downloadBlob(new Blob([source], { type: 'image/svg+xml;charset=utf-8' }), filename)
}

export async function exportMindmapPng(hostElement, filename = 'mindmap.png') {
  if (!hostElement) throw new Error('思维导图还没有准备好')
  const rect = hostElement.getBoundingClientRect()
  const width = Math.max(640, Math.round(rect.width || 960))
  const pixelRatio = Math.min(12, Math.max(2, 3840 / width))
  const { toPng } = await import('html-to-image')
  const dataUrl = await toPng(hostElement, {
    backgroundColor: '#ffffff',
    pixelRatio,
    cacheBust: true,
    width: Math.round(rect.width || width),
    height: Math.round(rect.height || 540),
    style: { background: '#ffffff' },
  })
  triggerDataUrl(dataUrl, filename)
}

export function safeExportName(title, ext) {
  const base = String(title || 'ReelCrate思维导图')
    .replace(/[\\/:*?"<>|\u0000-\u001f]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 60)
  return `${base || 'ReelCrate思维导图'}.${ext}`
}
