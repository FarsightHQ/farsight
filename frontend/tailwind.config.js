/** @type {import('tailwindcss').Config} */

// ============================================================================
// Color Utility Functions
// ============================================================================

/**
 * Convert hex color to HSL format
 * @param {string} hex - Hex color (e.g., '#21295C' or '21295C')
 * @returns {object} - { h, s, l } values (0-360 for h, 0-100 for s and l)
 */
function hexToHsl(hex) {
  // Remove # if present
  hex = hex.replace('#', '')
  
  // Parse RGB values
  const r = parseInt(hex.substring(0, 2), 16) / 255
  const g = parseInt(hex.substring(2, 4), 16) / 255
  const b = parseInt(hex.substring(4, 6), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s, l = (max + min) / 2

  if (max === min) {
    h = s = 0 // achromatic
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  }
}

/**
 * Adjust lightness of HSL color
 * @param {object} hsl - { h, s, l } object
 * @param {number} delta - Percentage change in lightness (-100 to 100)
 * @returns {object} - New HSL object with adjusted lightness
 */
function adjustLightness(hsl, delta) {
  return {
    h: hsl.h,
    s: hsl.s,
    l: Math.max(0, Math.min(100, hsl.l + delta))
  }
}

/**
 * Determine appropriate text color based on background lightness
 * @param {object} bgHsl - Background HSL color
 * @returns {string} - HSL string for text color (white for dark, dark for light)
 */
function getContrastText(bgHsl) {
  // Use white text for dark backgrounds (lightness < 50%)
  if (bgHsl.l < 50) {
    return 'hsl(0, 0%, 100%)'
  }
  // For light backgrounds, return null to derive from neutral color
  return null
}

/**
 * Generate border color from base color
 * @param {object} baseHsl - Base HSL color
 * @param {boolean} isDark - Whether the base color is dark
 * @returns {object} - HSL object for border color
 */
function deriveBorderColor(baseHsl, isDark) {
  if (isDark) {
    // For dark backgrounds, make border slightly lighter
    return adjustLightness(baseHsl, 6)
  } else {
    // For light backgrounds, make border slightly darker
    return adjustLightness(baseHsl, -7)
  }
}

/**
 * Format HSL object to CSS string
 * @param {object} hsl - { h, s, l } object
 * @returns {string} - CSS HSL string (e.g., 'hsl(217, 91%, 12%)')
 */
function hslToString(hsl) {
  return `hsl(${hsl.h}, ${hsl.s}%, ${hsl.l}%)`
}

// ============================================================================
// Theme Generation from Palette
// ============================================================================

/**
 * Generate complete theme from 5-color palette
 * @param {string[]} palette - Array of 5 hex colors (darkest to lightest)
 * @returns {object} - Complete theme object with all colors
 */
function generateThemeFromPalette(palette) {
  if (!palette || palette.length !== 5) {
    throw new Error('Palette must contain exactly 5 colors')
  }

  // Convert all colors to HSL and store with original index
  const colorsWithHsl = palette.map((hex, index) => ({
    hex,
    hsl: hexToHsl(hex),
    originalIndex: index
  }))

  // Sort by lightness (darkest to lightest)
  const sortedColors = [...colorsWithHsl].sort((a, b) => a.hsl.l - b.hsl.l)

  // Map to semantic roles
  const header = sortedColors[0].hsl      // Darkest
  const active = sortedColors[1].hsl    // 2nd darkest
  const sidebar = sortedColors[2].hsl  // Middle
  const footer = sortedColors[3].hsl    // 2nd lightest
  const content = sortedColors[4].hsl  // Lightest

  // Derive card color (slightly darker than content, ~4% less lightness)
  const card = adjustLightness(content, -2)

  // Get neutral color from lightest palette color (for text on light backgrounds)
  // Reduce saturation significantly for neutral tones
  const neutralHsl = {
    h: content.h,
    s: Math.max(5, Math.min(15, content.s * 0.2)), // Reduce saturation to 5-15%
    l: content.l
  }

  // Generate text colors
  const textHeader = getContrastText(header) || hslToString(adjustLightness(neutralHsl, -75))
  const textSidebar = getContrastText(sidebar) || hslToString(adjustLightness(neutralHsl, -60))
  const textFooter = getContrastText(footer) || hslToString(adjustLightness(neutralHsl, -55))
  const textContent = getContrastText(content) || hslToString(adjustLightness(neutralHsl, -70))
  const textMuted = hslToString(adjustLightness(neutralHsl, -30))

  // Generate border colors
  const borderHeader = hslToString(deriveBorderColor(header, header.l < 50))
  const borderSidebar = hslToString(deriveBorderColor(sidebar, sidebar.l < 50))
  const borderFooter = hslToString(deriveBorderColor(footer, footer.l < 50))
  const borderDefault = hslToString(adjustLightness(neutralHsl, -10))
  const borderCard = hslToString(adjustLightness(neutralHsl, -7))

  // Return complete theme object
  return {
    // Base theme colors
    header: hslToString(header),
    sidebar: hslToString(sidebar),
    footer: hslToString(footer),
    content: hslToString(content),
    active: hslToString(active),
    card: hslToString(card),
    
    // Text colors
    'text-header': textHeader,
    'text-sidebar': textSidebar,
    'text-footer': textFooter,
    'text-content': textContent,
    'text-muted': textMuted,
    
    // Border colors
    'border-header': borderHeader,
    'border-sidebar': borderSidebar,
    'border-footer': borderFooter,
    'border-default': borderDefault,
    'border-card': borderCard,
  }
}

// ============================================================================
// Color Scale Generation
// ============================================================================

// Helper function to generate color scale from HSL values
// Creates a consistent 50-950 scale with uniform lightness progression
function createColorScale(hue, saturation = 91) {
  return {
    50: `hsl(${hue}, ${saturation}%, 97%)`,
    100: `hsl(${hue}, ${saturation}%, 94%)`,
    200: `hsl(${hue}, ${saturation}%, 87%)`,
    300: `hsl(${hue}, ${saturation}%, 77%)`,
    400: `hsl(${hue}, ${saturation}%, 65%)`,
    500: `hsl(${hue}, ${saturation}%, 60%)`, // Base color
    600: `hsl(${hue}, ${saturation}%, 45%)`,
    700: `hsl(${hue}, ${saturation}%, 35%)`,
    800: `hsl(${hue}, ${saturation}%, 25%)`,
    900: `hsl(${hue}, ${saturation}%, 15%)`,
    950: `hsl(${hue}, ${saturation}%, 10%)`,
  }
}

// ============================================================================
// Theme Palette Configuration
// ============================================================================
// Define your 5-color palette here. Colors will be automatically sorted by
// lightness and mapped to semantic roles:
// - Darkest → header (dark top bar)
// - 2nd darkest → active (active states, buttons)
// - Middle → sidebar (side navigation)
// - 2nd lightest → footer (bottom bar)
// - Lightest → content (main content background)
const themePalette = [
  '#21295C', // Space Indigo (darkest)
  '#1B3B6F', // Regal Navy
  '#065A82', // Baltic Blue
  '#1C7293', // Cerulean
  '#9EB3C2'  // Powder Blue (lightest)
]

// Generate theme from palette
const generatedTheme = generateThemeFromPalette(themePalette)

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary - Blue (hue 217, high saturation for vibrancy)
        primary: createColorScale(217, 91),
        
        // Secondary - Purple/Violet (hue 260, same saturation for harmony)
        secondary: createColorScale(260, 91),
        
        // Tertiary - Teal/Cyan (hue 180, triadic harmony with primary)
        tertiary: createColorScale(180, 91),
        
        // Accent - Warm Amber (hue 45, for highlights and call-to-actions)
        accent: createColorScale(45, 91),
        
        // Neutral - Low saturation grey-blue (hue 220, sat 13% for subtle backgrounds)
        neutral: createColorScale(220, 13),
        
        // Success - Green (hue 142, appropriate saturation for positive states)
        success: createColorScale(142, 76),
        
        // Warning - Amber (hue 38, high saturation for visibility)
        warning: createColorScale(38, 92),
        
        // Error - Red (hue 0, high saturation for alert states)
        error: createColorScale(0, 84),
        
        // Info - Blue (same as primary for consistency)
        info: createColorScale(217, 91),
        
        // Semantic Theme Colors - Generated from 5-color palette
        // To change the theme, update the themePalette array above
        theme: generatedTheme,
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
    },
  },
  plugins: [],
}

