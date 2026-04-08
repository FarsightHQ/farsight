/**
 * Breadcrumb trails follow URL hierarchy: /projects → /projects/:projectId → …
 * Links use route names + params (not string paths).
 *
 * @param {import('vue-router').RouteLocationNormalizedLoaded} route
 * @param {object} ctx
 * @param {string} [ctx.projectName]
 * @param {string} [ctx.requestTitle]
 * @param {string|number} [ctx.requestId] — for linking to request from rule nested route
 * @param {string} [ctx.ruleLabel] — e.g. Rule #42
 * @param {string} [ctx.assetLabel] — IP for asset detail
 * @param {string} [ctx.registryIp] — decoded IP for registry asset detail
 */
export function resolveBreadcrumbs(route, ctx = {}) {
  const name = route.name
  const p = route.params
  const pid = p.projectId
  const projectLabel = ctx.projectName || (pid ? `Project ${pid}` : 'Project')

  const items = []
  const link = (label, to) => items.push({ label, to })
  const current = label => items.push({ label, current: true })

  const projectParams = pid ? { projectId: pid } : {}

  switch (name) {
    case 'Projects':
      current('Projects')
      break
    case 'ProjectCreate':
      link('Projects', { name: 'Projects' })
      current('New project')
      break
    case 'ProjectOverview':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      current('Details')
      break
    case 'Requests':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      current('Requests')
      break
    case 'RequestNew':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('Requests', { name: 'Requests', params: projectParams })
      current('New request')
      break
    case 'RequestDetail': {
      const rid = p.id
      const reqLabel = ctx.requestTitle || (rid ? `Request ${rid}` : 'Request')
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('Requests', { name: 'Requests', params: projectParams })
      current(reqLabel)
      break
    }
    case 'RequestRuleDetail': {
      const rid = p.requestId
      const ruleId = p.ruleId
      const reqLabel = ctx.requestTitle || (rid ? `Request ${rid}` : 'Request')
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('Requests', { name: 'Requests', params: projectParams })
      if (rid) {
        link(reqLabel, { name: 'RequestDetail', params: { ...projectParams, id: rid } })
      }
      current(ctx.ruleLabel || (ruleId ? `Rule ${ruleId}` : 'Rule'))
      break
    }
    case 'AllRules':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      current('All rules')
      break
    case 'RuleDetail': {
      const ruleId = p.id
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('All rules', { name: 'AllRules', params: projectParams })
      current(ctx.ruleLabel || (ruleId ? `Rule ${ruleId}` : 'Rule'))
      break
    }
    case 'ProjectAssets':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      current('Project assets')
      break
    case 'AssetUpload':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('Project assets', { name: 'ProjectAssets', params: projectParams })
      current('Upload')
      break
    case 'AssetDetail': {
      const ip = ctx.assetLabel || (p.id ? decodeURIComponent(String(p.id)) : 'Asset')
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      link('Project assets', { name: 'ProjectAssets', params: projectParams })
      current(ip)
      break
    }
    case 'UnifiedGraph':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      items.push({ label: 'Visualize' })
      current('Unified topology')
      break
    case 'ClassicRuleTopology':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      items.push({ label: 'Visualize' })
      current('Classic topology')
      break
    case 'ZoneAdjacency':
      link('Projects', { name: 'Projects' })
      link(projectLabel, { name: 'ProjectOverview', params: projectParams })
      items.push({ label: 'Visualize' })
      current('Zone adjacency')
      break
    case 'RegistryAssets':
      current('Global assets')
      break
    case 'RegistryAssetDetail': {
      const ip = ctx.registryIp || (p.ip ? safeDecodeIp(p.ip) : 'Asset')
      link('Global assets', { name: 'RegistryAssets' })
      current(ip)
      break
    }
    case 'SettingsAppearance':
      items.push({ label: 'Settings' })
      current('Appearance')
      break
    case 'SettingsRiskyPortPolicy':
      items.push({ label: 'Settings' })
      current('Risky port policy')
      break
    default:
      current(String(name || 'Page'))
  }

  return items
}

function safeDecodeIp(raw) {
  const s = Array.isArray(raw) ? raw.join('/') : String(raw)
  try {
    return decodeURIComponent(s)
  } catch {
    return s
  }
}
