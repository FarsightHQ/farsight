import apiClient from './api'

export type RiskyPortProtocol = 'tcp' | 'udp' | 'both'
export type RiskyPortSeverity = 'info' | 'warning' | 'high'

export interface RiskyPortPolicyEntry {
  id: number
  protocol: RiskyPortProtocol
  port_start: number
  port_end: number
  label: string
  recommendation: string | null
  severity: RiskyPortSeverity
  enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export type RiskyPortPolicyEntryInput = Omit<
  RiskyPortPolicyEntry,
  'id' | 'created_at' | 'updated_at'
>

export const riskyPortPolicyService = {
  async list(): Promise<RiskyPortPolicyEntry[]> {
    const { data } = await apiClient.get<RiskyPortPolicyEntry[]>('/api/v1/policy/risky-ports')
    return data
  },

  async replace(entries: RiskyPortPolicyEntryInput[]): Promise<RiskyPortPolicyEntry[]> {
    const { data } = await apiClient.put<RiskyPortPolicyEntry[]>('/api/v1/policy/risky-ports', {
      entries,
    })
    return data
  },
}
