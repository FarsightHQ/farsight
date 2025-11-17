import { computed } from 'vue'

/**
 * Composable for extracting filter options and counts from rules data
 */
export function useRuleFilters(rules) {
  /**
   * Extract unique protocols from rules with counts
   */
  const extractProtocols = (rulesData) => {
    if (!rulesData || !Array.isArray(rulesData)) return []
    
    const protocolCounts = {}
    
    rulesData.forEach((rule) => {
      if (rule.services && Array.isArray(rule.services)) {
        rule.services.forEach((service) => {
          const protocol = (service.protocol || '').toLowerCase()
          if (protocol) {
            protocolCounts[protocol] = (protocolCounts[protocol] || 0) + 1
          }
        })
      }
    })
    
    // Convert to array and sort by count (descending)
    return Object.entries(protocolCounts)
      .map(([protocol, count]) => ({
        value: protocol,
        label: protocol.toUpperCase(),
        count,
      }))
      .sort((a, b) => b.count - a.count)
  }

  /**
   * Extract unique directions from rules with counts
   */
  const extractDirections = (rulesData) => {
    if (!rulesData || !Array.isArray(rulesData)) return []
    
    const directionCounts = {}
    
    rulesData.forEach((rule) => {
      const direction = (rule.direction || 'bidirectional').toLowerCase()
      directionCounts[direction] = (directionCounts[direction] || 0) + 1
    })
    
    // Convert to array and sort by count (descending)
    return Object.entries(directionCounts)
      .map(([direction, count]) => ({
        value: direction,
        label: direction.charAt(0).toUpperCase() + direction.slice(1),
        count,
      }))
      .sort((a, b) => b.count - a.count)
  }

  /**
   * Calculate filter option counts for a given filter type
   */
  const calculateFilterCounts = (rulesData, filterType) => {
    if (!rulesData || !Array.isArray(rulesData)) return {}
    
    const counts = {}
    
    switch (filterType) {
      case 'action':
        rulesData.forEach((rule) => {
          const action = (rule.action || '').toLowerCase()
          if (action) {
            counts[action] = (counts[action] || 0) + 1
          }
        })
        break
      
      case 'protocol':
        return extractProtocols(rulesData).reduce((acc, item) => {
          acc[item.value] = item.count
          return acc
        }, {})
      
      case 'direction':
        return extractDirections(rulesData).reduce((acc, item) => {
          acc[item.value] = item.count
          return acc
        }, {})
      
      case 'hasFacts':
        rulesData.forEach((rule) => {
          const hasFacts = rule.facts && Object.keys(rule.facts).length > 0
          const key = hasFacts ? 'yes' : 'no'
          counts[key] = (counts[key] || 0) + 1
        })
        break
      
      case 'selfFlow':
        rulesData.forEach((rule) => {
          const isSelfFlow = rule.facts?.is_self_flow === true
          const key = isSelfFlow ? 'yes' : 'no'
          counts[key] = (counts[key] || 0) + 1
        })
        break
      
      case 'anyAny':
        rulesData.forEach((rule) => {
          const facts = rule.facts || {}
          const srcAny = facts.src_is_any === true
          const dstAny = facts.dst_is_any === true
          
          let key = 'none'
          if (srcAny && dstAny) {
            key = 'both'
          } else if (srcAny) {
            key = 'source'
          } else if (dstAny) {
            key = 'destination'
          }
          
          counts[key] = (counts[key] || 0) + 1
        })
        break
      
      case 'publicIP':
        rulesData.forEach((rule) => {
          const facts = rule.facts || {}
          const srcPublic = facts.src_has_public === true
          const dstPublic = facts.dst_has_public === true
          
          // Count each category
          if (srcPublic) {
            counts['src'] = (counts['src'] || 0) + 1
          }
          if (dstPublic) {
            counts['dst'] = (counts['dst'] || 0) + 1
          }
          if (srcPublic || dstPublic) {
            counts['either'] = (counts['either'] || 0) + 1
          }
          if (!srcPublic && !dstPublic) {
            counts['none'] = (counts['none'] || 0) + 1
          }
        })
        break
      
      case 'hasIssues':
        rulesData.forEach((rule) => {
          const facts = rule.facts || {}
          const hasIssues = 
            facts.is_self_flow ||
            facts.src_is_any ||
            facts.dst_is_any ||
            facts.src_has_public ||
            facts.dst_has_public
          
          const key = hasIssues ? 'yes' : 'no'
          counts[key] = (counts[key] || 0) + 1
        })
        break
    }
    
    return counts
  }

  /**
   * Get all available filter options with metadata
   */
  const getAvailableFilters = (rulesData) => {
    if (!rulesData || !Array.isArray(rulesData)) {
      return {
        protocols: [],
        directions: [],
        actionCounts: {},
        hasFactsCounts: {},
        selfFlowCounts: {},
        anyAnyCounts: {},
        publicIPCounts: {},
        hasIssuesCounts: {},
      }
    }
    
    return {
      protocols: extractProtocols(rulesData),
      directions: extractDirections(rulesData),
      actionCounts: calculateFilterCounts(rulesData, 'action'),
      hasFactsCounts: calculateFilterCounts(rulesData, 'hasFacts'),
      selfFlowCounts: calculateFilterCounts(rulesData, 'selfFlow'),
      anyAnyCounts: calculateFilterCounts(rulesData, 'anyAny'),
      publicIPCounts: calculateFilterCounts(rulesData, 'publicIP'),
      hasIssuesCounts: calculateFilterCounts(rulesData, 'hasIssues'),
    }
  }

  // Computed values for reactive updates
  const protocols = computed(() => extractProtocols(rules.value))
  const directions = computed(() => extractDirections(rules.value))
  const filterMetadata = computed(() => getAvailableFilters(rules.value))

  return {
    extractProtocols,
    extractDirections,
    calculateFilterCounts,
    getAvailableFilters,
    protocols,
    directions,
    filterMetadata,
  }
}

