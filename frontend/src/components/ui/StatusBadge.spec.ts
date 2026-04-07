import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusBadge from './StatusBadge.vue'

describe('StatusBadge', () => {
  it('shows label over status text when label is set', () => {
    const w = mount(StatusBadge, {
      props: { status: 'success', label: 'Active' },
    })
    expect(w.text()).toContain('Active')
  })

  it('falls back to status when no label', () => {
    const w = mount(StatusBadge, {
      props: { status: 'processing' },
    })
    expect(w.text()).toContain('processing')
  })

  it('applies sm size classes', () => {
    const w = mount(StatusBadge, {
      props: { status: 'completed', size: 'sm' },
    })
    expect(w.find('span').classes()).toContain('text-[10px]')
  })
})
