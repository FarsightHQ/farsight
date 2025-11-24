/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      colors: {
        theme: {
          'text-content': '#1f2937',
          'text-sidebar': '#ffffff',
          'text-muted': '#6b7280',
          'text-header': '#ffffff',
          'active': '#003566',
          'card': '#ffffff',
          'content': '#f9fafb',
          'sidebar': '#003566',
          'header': '#000814',
          'hover': '#FFD60A',
          'selected': '#FFC300',
          'nav-selected': '#001D3D',
          'border-default': '#e5e7eb',
          'border-card': '#e5e7eb',
          'border-sidebar': '#374151',
          'border-header': '#374151',
        },
        // Semantic color palette for UI components
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
        },
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
        },
        secondary: {
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          500: '#6b7280',
          900: '#111827',
        },
      },
    },
  },
  plugins: [],
}
