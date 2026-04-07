import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import { createRouter, createMemoryHistory } from 'vue-router'
import { usePageBreadcrumbs } from './usePageBreadcrumbs'

vi.mock('@/navigation/projectLabelCache', () => ({
  fetchProjectLabel: vi.fn().mockResolvedValue('Test Project'),
}))

const Harness = defineComponent({
  props: {
    requestTitle: { type: String, default: '' },
  },
  setup(props) {
    const { breadcrumbItems } = usePageBreadcrumbs({
      requestTitle: () => props.requestTitle,
    })
    return { breadcrumbItems }
  },
  template: '<span>{{ breadcrumbItems.map(i => i.label).join(",") }}</span>',
})

describe('usePageBreadcrumbs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('includes request title for RequestDetail route', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/projects/:projectId/requests/:id',
          name: 'RequestDetail',
          component: { template: '<div/>' },
        },
      ],
    })

    await router.push({ name: 'RequestDetail', params: { projectId: 'p1', id: '42' } })

    const wrapper = mount(Harness, {
      props: { requestTitle: 'My upload' },
      global: { plugins: [router] },
    })

    await flushPromises()
    await nextTick()

    const labels = wrapper.vm.breadcrumbItems.map((i: { label: string }) => i.label)
    expect(labels).toContain('My upload')
  })
})
