/**
 * Export service for exporting data to CSV and JSON formats
 */

/**
 * Convert array of objects to CSV format
 * @param {Array} data - Array of objects to export
 * @param {Array} columns - Array of column definitions [{key: 'id', label: 'ID'}, ...]
 * @returns {string} CSV string
 */
function convertToCSV(data, columns) {
  if (!data || data.length === 0) {
    return ''
  }

  // If columns not provided, use all keys from first object
  if (!columns || columns.length === 0) {
    const firstItem = data[0]
    columns = Object.keys(firstItem).map((key) => ({
      key,
      label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
    }))
  }

  // Create header row
  const headers = columns.map((col) => col.label).join(',')
  
  // Create data rows
  const rows = data.map((item) => {
    return columns
      .map((col) => {
        let value = item[col.key]
        
        // Handle nested objects/arrays
        if (value && typeof value === 'object') {
          if (Array.isArray(value)) {
            value = value.map((v) => (typeof v === 'object' ? JSON.stringify(v) : v)).join('; ')
          } else {
            value = JSON.stringify(value)
          }
        }
        
        // Escape commas and quotes
        if (typeof value === 'string') {
          value = value.replace(/"/g, '""') // Escape quotes
          if (value.includes(',') || value.includes('"') || value.includes('\n')) {
            value = `"${value}"` // Wrap in quotes if needed
          }
        }
        
        return value ?? ''
      })
      .join(',')
  })

  return [headers, ...rows].join('\n')
}

/**
 * Export data to CSV file
 * @param {Array} data - Data to export
 * @param {string} filename - Filename (without extension)
 * @param {Array} columns - Optional column definitions
 */
export function exportToCSV(data, filename = 'export', columns = null) {
  const csv = convertToCSV(data, columns)
  
  if (!csv) {
    throw new Error('No data to export')
  }

  // Create blob and download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.csv`)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

/**
 * Export data to JSON file
 * @param {Array|Object} data - Data to export
 * @param {string} filename - Filename (without extension)
 * @param {boolean} pretty - Whether to format JSON with indentation
 */
export function exportToJSON(data, filename = 'export', pretty = true) {
  if (!data) {
    throw new Error('No data to export')
  }

  const json = pretty ? JSON.stringify(data, null, 2) : JSON.stringify(data)
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.json`)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  URL.revokeObjectURL(url)
}

/**
 * Export rules to CSV with proper formatting
 * @param {Array} rules - Array of rule objects
 * @param {string} filename - Filename (without extension)
 */
export function exportRulesToCSV(rules, filename = 'rules') {
  const columns = [
    { key: 'id', label: 'Rule ID' },
    { key: 'action', label: 'Action' },
    { key: 'direction', label: 'Direction' },
    { key: 'source_networks', label: 'Source Networks' },
    { key: 'destination_networks', label: 'Destination Networks' },
    { key: 'protocols', label: 'Protocols' },
    { key: 'port_ranges', label: 'Port Ranges' },
    { key: 'service_count', label: 'Service Count' },
    { key: 'tuple_estimate', label: 'Tuple Estimate' },
    { key: 'created_at', label: 'Created At' },
  ]

  // Transform rules data for CSV
  const csvData = rules.map((rule) => {
    const sourceNetworks = rule.endpoints
      ?.filter((ep) => ep.endpoint_type === 'source' || ep.type === 'source')
      .map((ep) => ep.network_cidr || ep.cidr)
      .join('; ') || ''
    
    const destNetworks = rule.endpoints
      ?.filter((ep) => ep.endpoint_type === 'destination' || ep.type === 'destination')
      .map((ep) => ep.network_cidr || ep.cidr)
      .join('; ') || ''
    
    const protocols = rule.services?.map((svc) => svc.protocol).join('; ') || ''
    const portRanges = rule.services?.map((svc) => svc.port_ranges || svc.ports).join('; ') || ''

    return {
      id: rule.id,
      action: rule.action || '',
      direction: rule.direction || '',
      source_networks: sourceNetworks,
      destination_networks: destNetworks,
      protocols,
      port_ranges: portRanges,
      service_count: rule.service_count || rule.services?.length || 0,
      tuple_estimate: rule.tuple_estimate || 0,
      created_at: rule.created_at || '',
    }
  })

  exportToCSV(csvData, filename, columns)
}

/**
 * Export rules to JSON
 * @param {Array} rules - Array of rule objects
 * @param {string} filename - Filename (without extension)
 */
export function exportRulesToJSON(rules, filename = 'rules') {
  exportToJSON(rules, filename, true)
}

