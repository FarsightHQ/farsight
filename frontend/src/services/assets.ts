import apiClient from './api'
import { getActiveProjectId } from '../utils/projectContext'

function projectAssetsBase() {
  const id = getActiveProjectId()
  if (!id) {
    throw new Error('No project selected. Choose a project in the header or open Projects.')
  }
  return `/api/v1/projects/${id}/assets`
}

export const assetsService = {
  getAssetByIp(ipAddress) {
    return apiClient.get(`${projectAssetsBase()}/${encodeURIComponent(ipAddress)}`)
  },

  searchAssets(params = {}) {
    return apiClient.get(projectAssetsBase(), { params })
  },

  getAnalytics(params = {}) {
    return apiClient.get(`${projectAssetsBase()}/analytics`, { params })
  },

  getFilterOptions() {
    return apiClient.get(`${projectAssetsBase()}/filter-options`).catch(error => {
      if (error.response?.status === 404) {
        console.warn('Filter options endpoint not available, returning empty options')
        return {
          data: { segments: [], vlans: [], os_names: [], environments: [] },
        }
      }
      throw error
    })
  },

  uploadCSV(file) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post(`${projectAssetsBase()}/upload-csv`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** Remove this project's link to the IP; other projects keep the asset. */
  unlinkByIp(ipAddress) {
    const enc = encodeURIComponent(ipAddress)
    return apiClient.delete(`${projectAssetsBase()}/${enc}/link`)
  },

  /** Soft-delete the asset org-wide (hides from all projects). */
  deactivateByIp(ipAddress) {
    const enc = encodeURIComponent(ipAddress)
    return apiClient.post(`${projectAssetsBase()}/${enc}/deactivate`)
  },
}
