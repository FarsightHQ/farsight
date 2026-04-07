import { describe, expect, it } from 'vitest'
import { formatPortRanges } from './portUtils'

describe('formatPortRanges', () => {
  it('returns empty for missing input', () => {
    expect(formatPortRanges(null)).toBe('')
    expect(formatPortRanges(undefined)).toBe('')
  })

  it('formats single port', () => {
    expect(formatPortRanges('{[10334,10334]}')).toBe('10334')
  })

  it('formats range and multiple ranges', () => {
    expect(formatPortRanges('{[8001,8010]}')).toBe('8001-8010')
    expect(formatPortRanges('{[8001,8010],[9000,9000]}')).toBe('8001-8010, 9000')
  })

  it('returns empty for empty multirange', () => {
    expect(formatPortRanges('{}')).toBe('')
  })
})
