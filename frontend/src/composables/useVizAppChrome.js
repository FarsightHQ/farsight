import { ref } from 'vue'

/**
 * When true, AppLayout hides header, sidebar, and footer so visualization routes can use
 * the full viewport (two-column viz workspace only). Used with VizWorkspaceLayout fullscreen control.
 */
const hideAppChrome = ref(false)

export function useVizAppChrome() {
  function setVizFullscreen(enabled) {
    hideAppChrome.value = Boolean(enabled)
  }

  function toggleVizFullscreen() {
    hideAppChrome.value = !hideAppChrome.value
  }

  /** Clears fullscreen chrome override (e.g. on route leave); idempotent. */
  function resetVizChrome() {
    hideAppChrome.value = false
  }

  return {
    hideAppChrome,
    setVizFullscreen,
    toggleVizFullscreen,
    resetVizChrome,
  }
}
