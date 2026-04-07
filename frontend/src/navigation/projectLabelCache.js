import { projectsService } from '@/services/projects'

const cache = new Map()

/**
 * Load display name for a project (cached). Used for breadcrumbs.
 */
export async function fetchProjectLabel(projectId) {
  if (projectId == null || projectId === '') return ''
  const key = String(projectId)
  if (cache.has(key)) return cache.get(key)
  try {
    const res = await projectsService.get(projectId)
    const data = res?.data ?? res
    const name = data?.name ?? `Project ${key}`
    cache.set(key, name)
    return name
  } catch {
    const fallback = `Project ${key}`
    cache.set(key, fallback)
    return fallback
  }
}

export function invalidateProjectLabel(projectId) {
  if (projectId != null) cache.delete(String(projectId))
}
