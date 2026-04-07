import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from './Button.vue'

describe('Button', () => {
  it('renders default primary md classes', () => {
    const w = mount(Button, { slots: { default: 'Go' } })
    const el = w.find('button')
    expect(el.classes()).toContain('btn')
    expect(el.classes()).toContain('btn-primary')
    expect(el.text()).toBe('Go')
  })

  it('applies variant and size classes', () => {
    const w = mount(Button, {
      props: { variant: 'outline', size: 'sm' },
      slots: { default: 'X' },
    })
    const el = w.find('button')
    expect(el.classes()).toContain('btn-outline')
    expect(el.classes()).toContain('px-3')
    expect(el.classes()).toContain('text-xs')
  })

  it('disables the native button', () => {
    const w = mount(Button, { props: { disabled: true } })
    expect(w.find('button').element.disabled).toBe(true)
  })

  it('applies danger variant class', () => {
    const w = mount(Button, {
      props: { variant: 'danger' },
      slots: { default: 'Delete' },
    })
    expect(w.find('button').classes()).toContain('btn-danger')
  })
})
