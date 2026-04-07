import { computed, ref, toValue, watch, type Ref, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { resolveBreadcrumbs } from '@/navigation/breadcrumbResolve'
import { fetchProjectLabel } from '@/navigation/projectLabelCache'

type MaybeRefOrGetter<T> = T | Ref<T> | ComputedRef<T> | (() => T)

export interface PageBreadcrumbExtras {
  requestTitle?: MaybeRefOrGetter<string | undefined>
  requestId?: MaybeRefOrGetter<string | number | undefined>
  ruleLabel?: MaybeRefOrGetter<string | undefined>
  assetLabel?: MaybeRefOrGetter<string | undefined>
  registryIp?: MaybeRefOrGetter<string | undefined>
}

/**
 * Reactive breadcrumbs for the current route. Fetches project display name when route has projectId.
 * Pass optional refs for async labels: requestTitle, ruleLabel, assetLabel, registryIp.
 */
export function usePageBreadcrumbs(extra: PageBreadcrumbExtras = {}) {
  const route = useRoute()
  const projectName = ref('')

  watch(
    () => route.params.projectId,
    async id => {
      if (id == null || id === '') {
        projectName.value = ''
        return
      }
      projectName.value = await fetchProjectLabel(id)
    },
    { immediate: true }
  )

  const breadcrumbItems = computed(() =>
    resolveBreadcrumbs(route, {
      projectName: projectName.value,
      requestTitle: extra.requestTitle != null ? toValue(extra.requestTitle) : undefined,
      requestId: extra.requestId != null ? toValue(extra.requestId) : undefined,
      ruleLabel: extra.ruleLabel != null ? toValue(extra.ruleLabel) : undefined,
      assetLabel: extra.assetLabel != null ? toValue(extra.assetLabel) : undefined,
      registryIp: extra.registryIp != null ? toValue(extra.registryIp) : undefined,
    })
  )

  return { breadcrumbItems, projectName }
}
