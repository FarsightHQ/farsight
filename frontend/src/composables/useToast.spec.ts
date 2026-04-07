import { beforeEach, describe, expect, it } from 'vitest'
import { useToast } from './useToast'

beforeEach(() => {
  const { toasts } = useToast()
  toasts.value = []
})

describe('useToast', () => {
  it('success appends a success toast', () => {
    const { success, toasts } = useToast()
    success('Saved')
    expect(toasts.value).toHaveLength(1)
    expect(toasts.value[0].message).toBe('Saved')
    expect(toasts.value[0].type).toBe('success')
  })

  it('error appends an error toast', () => {
    const { error, toasts } = useToast()
    error('Failed')
    expect(toasts.value[0].type).toBe('error')
  })
})
