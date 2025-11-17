/**
 * Parse PostgreSQL multirange format and convert to human-readable port ranges
 * 
 * Examples:
 * - {[10334,10334]} → "10334"
 * - {[8001,8010]} → "8001-8010"
 * - {[8001,8010],[9000,9000]} → "8001-8010, 9000"
 * - {} → "" (empty)
 * 
 * @param {string} portRanges - PostgreSQL multirange format string
 * @returns {string} Human-readable port range string
 */
export function formatPortRanges(portRanges) {
  if (!portRanges || typeof portRanges !== 'string') return ''
  
  // Handle empty ranges
  if (portRanges.trim() === '{}' || portRanges.trim() === '') return ''
  
  // Remove outer braces
  if (!portRanges.startsWith('{') || !portRanges.endsWith('}')) {
    // If not in multirange format, return as-is (might be already formatted)
    return portRanges
  }
  
  const rangesStr = portRanges.slice(1, -1) // Remove { }
  if (!rangesStr) return ''
  
  // Use regex to match all [start,end] patterns
  const rangePattern = /\[(\d+),(\d+)\]/g
  const matches = [...rangesStr.matchAll(rangePattern)]
  
  if (matches.length === 0) {
    // If no matches, return as-is (might be malformed)
    return portRanges
  }
  
  const formattedRanges = matches.map((match) => {
    const startNum = parseInt(match[1], 10)
    const endNum = parseInt(match[2], 10)
    
    // Validate numbers
    if (isNaN(startNum) || isNaN(endNum)) {
      return ''
    }
    
    // If start and end are the same, return single port
    if (startNum === endNum) {
      return String(startNum)
    }
    
    // Return range format
    return `${startNum}-${endNum}`
  }).filter(Boolean)
  
  return formattedRanges.join(', ')
}

