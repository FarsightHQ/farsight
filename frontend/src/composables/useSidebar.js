import { ref } from 'vue'

// Load initial state from localStorage
const getInitialState = () => {
  if (typeof window !== 'undefined') {
    const savedState = localStorage.getItem('sidebarCollapsed')
    if (savedState !== null) {
      return savedState === 'true'
    }
  }
  return false
}

const isCollapsed = ref(getInitialState())

export function useSidebar() {
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
    // Persist state to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarCollapsed', isCollapsed.value.toString())
    }
  }

  return {
    isCollapsed,
    toggleSidebar,
  }
}

