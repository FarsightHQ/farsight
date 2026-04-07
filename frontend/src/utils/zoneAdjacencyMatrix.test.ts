import { describe, expect, it } from 'vitest'
import { buildZoneAdjacencyMatrix, pickZone } from './zoneAdjacencyMatrix.js'

describe('pickZone', () => {
  it('returns Unknown for missing or empty fields', () => {
    expect(pickZone(null, 'segment')).toBe('Unknown')
    expect(pickZone({}, 'segment')).toBe('Unknown')
    expect(pickZone({ segment: '  ' }, 'segment')).toBe('Unknown')
    expect(pickZone({ location: null }, 'location')).toBe('Unknown')
    expect(pickZone({ vlan: '' }, 'vlan')).toBe('Unknown')
  })

  it('returns string values for each groupBy', () => {
    expect(pickZone({ segment: 'DMZ' }, 'segment')).toBe('DMZ')
    expect(pickZone({ location: 'NYC' }, 'location')).toBe('NYC')
    expect(pickZone({ vlan: '100' }, 'vlan')).toBe('100')
  })
})

describe('buildZoneAdjacencyMatrix', () => {
  const graph = {
    nodes: [
      { id: 'a', segment: 'A', location: 'L1', vlan: '10' },
      { id: 'b', segment: 'B', location: 'L2', vlan: '20' },
      { id: 'c', segment: 'A', location: 'L1', vlan: '10' },
    ],
    links: [
      {
        source: 'a',
        target: 'b',
        rule_ids: [1, 2],
        services: [
          { protocol: 'tcp', port_ranges: '443' },
          { protocol: 'udp', port_ranges: '53' },
        ],
      },
      {
        source: 'a',
        target: 'c',
        rule_ids: [2],
        services: [{ protocol: 'tcp', port_ranges: '443' }],
      },
    ],
  }

  it('aggregates rule count per directed cell (segment)', () => {
    const r = buildZoneAdjacencyMatrix(graph, { groupBy: 'segment', metric: 'rules' })
    expect(r.rowLabels).toEqual(['A', 'B'])
    expect(r.colLabels).toEqual(['A', 'B'])
    const iA = r.rowLabels.indexOf('A')
    const iB = r.rowLabels.indexOf('B')
    expect(r.matrix[iA][iB]).toBe(2)
    expect(r.matrix[iA][iA]).toBe(1)
    expect(r.cellDetail[iA][iB].ruleIds).toEqual([1, 2])
    expect(r.cellDetail[iA][iA].ruleIds).toEqual([2])
    expect(r.maxValue).toBe(2)
    expect(r.nonEmptyCellCount).toBe(2)
  })

  it('counts distinct services per cell', () => {
    const r = buildZoneAdjacencyMatrix(graph, { groupBy: 'segment', metric: 'services' })
    const iA = r.rowLabels.indexOf('A')
    const iB = r.rowLabels.indexOf('B')
    expect(r.matrix[iA][iB]).toBe(2)
    expect(r.matrix[iA][iA]).toBe(1)
    expect(r.cellDetail[iA][iB].services).toHaveLength(2)
  })

  it('binary metric is 1 for non-empty cells', () => {
    const r = buildZoneAdjacencyMatrix(graph, { groupBy: 'segment', metric: 'binary' })
    const iA = r.rowLabels.indexOf('A')
    const iB = r.rowLabels.indexOf('B')
    expect(r.matrix[iA][iB]).toBe(1)
    expect(r.matrix[iA][iA]).toBe(1)
    expect(r.maxValue).toBe(1)
  })

  it('skips links when source or target node is missing', () => {
    const g = {
      nodes: [{ id: 'x', segment: 'X' }],
      links: [{ source: 'x', target: 'missing', rule_ids: [9] }],
    }
    const r = buildZoneAdjacencyMatrix(g, { metric: 'rules' })
    expect(r.rowLabels).toEqual([])
    expect(r.nonEmptyCellCount).toBe(0)
  })

  it('merges multiple links into the same cell', () => {
    const g = {
      nodes: [
        { id: '1', segment: 'S1' },
        { id: '2', segment: 'S2' },
      ],
      links: [
        { source: '1', target: '2', rule_ids: [1] },
        { source: '1', target: '2', rule_ids: [2, 1] },
      ],
    }
    const r = buildZoneAdjacencyMatrix(g, { metric: 'rules' })
    const i1 = r.rowLabels.indexOf('S1')
    const i2 = r.rowLabels.indexOf('S2')
    expect(r.matrix[i1][i2]).toBe(2)
    expect(r.cellDetail[i1][i2].linkCount).toBe(2)
  })
})
