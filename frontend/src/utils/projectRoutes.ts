import { getActiveProjectId } from './projectContext'

/**
 * Build a path under /projects/:projectId/...
 * @param {string} suffix - e.g. 'requests', '/requests/new'
 * @param {string|number|null} projectId - defaults to localStorage active project
 */
export function projectPath(suffix, projectId = null) {
  const pid = projectId ?? getActiveProjectId()
  if (!pid) return '/projects'
  const s = suffix.startsWith('/') ? suffix : `/${suffix}`
  return `/projects/${pid}${s}`
}
