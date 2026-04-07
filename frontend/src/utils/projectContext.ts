const STORAGE_KEY = 'farsight_project_id'

export function getActiveProjectId() {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(STORAGE_KEY)
}

export function setActiveProjectId(id) {
  if (typeof window === 'undefined') return
  if (id == null || id === '') {
    window.localStorage.removeItem(STORAGE_KEY)
    return
  }
  window.localStorage.setItem(STORAGE_KEY, String(id))
}
