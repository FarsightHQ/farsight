/** Plain-text lines for node / link detail (tooltips and side panel). */

export function formatNodeDetailLines(d) {
  const lines = [d.label || d.network_cidr]
  if (d.network_cidr) lines.push(`CIDR: ${d.network_cidr}`)
  if (d.segment) lines.push(`Segment: ${d.segment}`)
  if (d.vlan != null && d.vlan !== '') lines.push(`VLAN: ${d.vlan}`)
  if (d.environment) lines.push(`Env: ${d.environment}`)
  if (d.location) lines.push(`Location: ${d.location}`)
  if (d.asset?.hostname) lines.push(`Hostname: ${d.asset.hostname}`)
  return lines
}

export function formatLinkDetailLines(d) {
  const lines = [d.label || 'Connection']
  if (d.rule_ids?.length) lines.push(`Rules: ${d.rule_ids.join(', ')}`)
  if (d.services?.length) {
    const svc = d.services
      .map(s => `${s.protocol}/${s.formatted_ports || s.port_ranges}`)
      .join(', ')
    lines.push(`Services: ${svc}`)
  }
  return lines
}
