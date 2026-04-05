import { ref } from 'vue'
import { requestsService } from '@/services/requests'
import { mergeRuleGraphResponses } from '@/utils/ruleGraphMerge'
import { normalizeRuleGraphApiResponse } from '@/utils/ruleGraphNormalize'

/**
 * Load classic (D3) rule graph data for one or more rules.
 * @param {import('vue').Ref<number[]>} ruleIdsRef
 */
export function useClassicRuleTopology(ruleIdsRef) {
  const loading = ref(false)
  const error = ref(null)
  const graphData = ref(null)
  const summary = ref(null)
  const emptyStateMessage = ref('This rule has no network topology data to visualize.')

  let loadGeneration = 0

  async function load() {
    const gen = ++loadGeneration
    loading.value = true
    error.value = null
    graphData.value = null
    summary.value = null
    emptyStateMessage.value = 'This rule has no network topology data to visualize.'

    const ids = ruleIdsRef.value || []

    try {
      if (ids.length === 0) {
        if (gen !== loadGeneration) return
        emptyStateMessage.value =
          'No rules in the URL. Open this page from the app with ?ruleIds=… (comma-separated rule IDs), same as unified view.'
        return
      }

      if (ids.length === 1) {
        const response = await requestsService.getRuleGraph(ids[0])
        if (gen !== loadGeneration) return
        const n = normalizeRuleGraphApiResponse(response, ids[0])
        error.value = n.error
        graphData.value = n.graphData
        summary.value = n.summary
        emptyStateMessage.value = n.emptyStateMessage
      } else {
        const responses = await Promise.all(ids.map(id => requestsService.getRuleGraph(id)))
        if (gen !== loadGeneration) return
        const merged = mergeRuleGraphResponses(responses, { ruleCount: ids.length })
        graphData.value = merged
        const svc = merged.connections?.reduce((sum, c) => sum + (c.port_count || 0), 0) || 0
        summary.value = {
          rule_count: merged.metadata.rule_count,
          source_count: merged.metadata.source_count,
          destination_count: merged.metadata.destination_count,
          service_count: svc,
        }
        error.value = null
        if (!merged.sources.length || !merged.destinations.length) {
          emptyStateMessage.value =
            'No mergeable graph data for the selected rules (missing sources or destinations).'
        }
      }
    } catch (e) {
      if (gen === loadGeneration) {
        error.value = e.message || 'Failed to load network topology'
        graphData.value = null
        summary.value = null
      }
    } finally {
      if (gen === loadGeneration) {
        loading.value = false
      }
    }
  }

  return { loading, error, graphData, summary, emptyStateMessage, load }
}
