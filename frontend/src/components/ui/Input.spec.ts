import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Input from './Input.vue'

describe('Input', () => {
  it('associates label with input id', () => {
    const w = mount(Input, {
      props: { label: 'Name', modelValue: '' },
    })
    const input = w.find('input')
    const label = w.find('label')
    expect(label.attributes('for')).toBe(input.attributes('id'))
  })

  it('emits update:modelValue on input', async () => {
    const w = mount(Input, {
      props: { modelValue: '' },
    })
    await w.find('input').setValue('hello')
    expect(w.emitted('update:modelValue')?.[0]).toEqual(['hello'])
  })

  it('shows error message and error border class when error set', () => {
    const w = mount(Input, {
      props: { modelValue: '', error: 'Required' },
    })
    expect(w.text()).toContain('Required')
    expect(w.find('input').classes()).toContain('border-error-300')
  })
})
