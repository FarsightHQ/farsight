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
      },
    },
  },
  plugins: [],
}
