import { computed, unref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getActiveProjectId } from '@/utils/projectContext'

/**
 * Open-in-new-tab graph routes for a loaded rule. ruleRef may be a ref or computed ref.
 */
export function useRuleGraphNavigation(ruleRef) {
  const router = useRouter()
  const route = useRoute()

  const projectIdForNav = computed(() => route.params.projectId || getActiveProjectId() || '')

  const hasNetworkData = computed(() => {
    const rule = unref(ruleRef)
    if (!rule) return false
    return Boolean(rule.endpoints && Array.isArray(rule.endpoints) && rule.endpoints.length > 0)
  })

  function openUnifiedTab() {
    const rule = unref(ruleRef)
    const pid = projectIdForNav.value
    if (!rule?.id || !pid) return
    const href = router.resolve({
      name: 'UnifiedGraph',
      params: { projectId: String(pid) },
      query: {
        ruleIds: String(rule.id),
        title: `Rule #${rule.id}`,
      },
    }).href
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  function openClassicTab() {
    const rule = unref(ruleRef)
    const pid = projectIdForNav.value
    if (!rule?.id || !pid) return
    const href = router.resolve({
      name: 'ClassicRuleTopology',
      params: { projectId: String(pid) },
      query: {
        ruleIds: String(rule.id),
        title: `Rule #${rule.id}`,
      },
    }).href
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  function openZoneTab() {
    const rule = unref(ruleRef)
    const pid = projectIdForNav.value
    if (!rule?.id || !pid) return
    const href = router.resolve({
      name: 'ZoneAdjacency',
      params: { projectId: String(pid) },
      query: {
        ruleIds: String(rule.id),
        title: `Rule #${rule.id}`,
      },
    }).href
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  return {
    hasNetworkData,
    openUnifiedTab,
    openClassicTab,
    openZoneTab,
  }
}
