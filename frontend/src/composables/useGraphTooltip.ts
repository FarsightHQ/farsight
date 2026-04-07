import { ref } from 'vue'

/**
 * Screen-space tooltip for SVG graph hover (client coords → relative to container).
 * @param {import('vue').Ref<HTMLElement | null>} containerRef
 */
export function useGraphTooltip(containerRef) {
  const tooltip = ref({ visible: false, x: 0, y: 0, text: '' })

  function updateClientPosition(event) {
    const el = containerRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    tooltip.value.x = event.clientX - rect.left
    tooltip.value.y = event.clientY - rect.top
  }

  function show(text, event) {
    updateClientPosition(event)
    tooltip.value.visible = true
    tooltip.value.text = text
  }

  function move(event) {
    if (!tooltip.value.visible) return
    updateClientPosition(event)
  }

  function hide() {
    tooltip.value.visible = false
  }

  return { tooltip, show, move, hide }
}
