/** Placeholder when node has no VLAN from asset data */
export const VLAN_NONE_KEY = '__no_vlan__'

/** Separates vlan id and segment in layout / hull keys */
export const LAYOUT_SEP = '\x1f'

export function vlanGroupKey(d) {
  const v = d.vlan
  if (v == null) return VLAN_NONE_KEY
  const s = String(v).trim()
  return s === '' ? VLAN_NONE_KEY : s
}

export function nodeLayoutKey(d) {
  return `${vlanGroupKey(d)}${LAYOUT_SEP}${d.segment || 'Unknown'}`
}

/** Stable ordering: real VLAN ids first, "no VLAN" last */
export function sortVlanIds(a, b) {
  if (a === VLAN_NONE_KEY) return 1
  if (b === VLAN_NONE_KEY) return -1
  return a.localeCompare(b, undefined, { sensitivity: 'base' })
}
