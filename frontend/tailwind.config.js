/** @type {import('tailwindcss').Config} */

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
        
        // Semantic Theme Colors - Change these 4-5 colors to change entire theme
        // Flattened structure for Tailwind compatibility
        theme: {
          // Base theme colors (4-5 colors to change entire theme)
          header: 'hsl(217, 91%, 12%)',      // Darker, more visible
          sidebar: 'hsl(217, 91%, 88%)',     // Noticeably light blue (was 97% - too light)
          footer: 'hsl(217, 91%, 92%)',     // Slightly lighter than sidebar
          content: 'hsl(220, 13%, 98%)',     // Very light grey
          active: 'hsl(217, 91%, 82%)',      // Clearly visible active state (was 94% - too light)
          card: 'hsl(220, 13%, 96%)',        // Slightly darker than content for contrast
          
          // Text colors for different areas (flattened from theme.text.*)
          'text-header': 'hsl(0, 0%, 100%)',      // White text for dark header
          'text-sidebar': 'hsl(220, 13%, 25%)',   // Dark grey for light sidebar
          'text-footer': 'hsl(220, 13%, 30%)',   // Slightly darker for footer
          'text-content': 'hsl(220, 13%, 15%)',   // Dark for content area
          'text-muted': 'hsl(220, 13%, 45%)',     // Muted/secondary text
          
          // Border colors for different areas (flattened from theme.border.*)
          'border-header': 'hsl(217, 91%, 18%)',   // Slightly lighter than header
          'border-sidebar': 'hsl(217, 91%, 80%)',   // More visible border (was 87%)
          'border-footer': 'hsl(217, 91%, 85%)',   // Lighter border
          'border-default': 'hsl(220, 13%, 85%)',   // Default border color
          'border-card': 'hsl(220, 13%, 88%)',     // Card border color
        },
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

