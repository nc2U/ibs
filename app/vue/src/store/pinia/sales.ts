import api from '@/api'
import { ref } from 'vue'
import { defineStore } from 'pinia'
import { message, errorHandle } from '@/utils/helper'
import type {
  SalesAgency,
  SalesTeam,
  SalesPerson,
  SalesPersonDocument,
  CommissionPolicy,
  ContractSalesAgent,
  SettlementPeriod,
  CommissionPayout,
  CommissionClawback,
  AgencyPayout,
  OrgHealthCheckResult,
} from '@/store/types/sales'

const buildQuery = (params: Record<string, string | number | undefined | null>) => {
  const sp = new URLSearchParams()
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      sp.append(key, String(val))
    }
  })
  return sp.toString()
}

const runMutation = async (
  requestFn: () => Promise<{ data?: { detail?: string } } | unknown>,
  fallbackMessage: string,
  toastType: 'success' | 'warning' = 'success',
  preferDetail = false,
): Promise<boolean> => {
  try {
    const res = (await requestFn()) as { data?: { detail?: string } } | undefined
    const msg = preferDetail && res?.data?.detail ? res.data.detail : fallbackMessage
    message(toastType, '알림!', msg)
    return true
  } catch (err) {
    errorHandle(err)
    return false
  }
}

export const useSales = defineStore('sales', () => {
  // ── 대행사 ─────────────────────────────────────────────
  const agencyList = ref<SalesAgency[]>([])

  const fetchAgencyList = async (projectId?: number) => {
    const q = buildQuery({ project: projectId, limit: 500 })
    try {
      const res = await api.get(`/sales-agency/?${q}`)
      agencyList.value = res.data.results ?? res.data
    } catch (err) {
      agencyList.value = []
      console.warn('fetchAgencyList failed:', (err as Error)?.message || err)
    }
  }

  const createAgency = (payload: Partial<SalesAgency>): Promise<boolean> =>
    runMutation(() => api.post('/sales-agency/', payload), '분양 대행사가 등록되었습니다.')

  const updateAgency = (id: number, payload: Partial<SalesAgency>): Promise<boolean> =>
    runMutation(() => api.patch(`/sales-agency/${id}/`, payload), '분양 대행사 정보가 수정되었습니다.')

  const deleteAgency = (id: number): Promise<boolean> =>
    runMutation(() => api.delete(`/sales-agency/${id}/`), '분양 대행사가 삭제되었습니다.', 'warning')

  // ── 영업 팀 ───────────────────────────────────────────
  const teamList = ref<SalesTeam[]>([])

  const fetchTeamList = async (agencyId?: number, projectId?: number) => {
    const q = buildQuery({ agency: agencyId, agency__project: projectId, limit: 500 })
    try {
      const res = await api.get(`/sales-team/?${q}`)
      teamList.value = res.data.results ?? res.data
    } catch (err) {
      teamList.value = []
      console.warn('fetchTeamList failed:', (err as Error)?.message || err)
    }
  }

  const createTeam = (payload: Partial<SalesTeam>): Promise<boolean> =>
    runMutation(() => api.post('/sales-team/', payload), '영업 조직/팀이 등록되었습니다.')

  const updateTeam = (id: number, payload: Partial<SalesTeam>): Promise<boolean> =>
    runMutation(() => api.patch(`/sales-team/${id}/`, payload), '영업 조직/팀 정보가 수정되었습니다.')

  const deleteTeam = (id: number): Promise<boolean> =>
    runMutation(() => api.delete(`/sales-team/${id}/`), '영업 조직/팀이 삭제되었습니다.', 'warning')

  // ── 영업 인력 (분양상담사 등) ─────────────────────────
  const personList = ref<SalesPerson[]>([])

  const fetchPersonList = async (teamId?: number, projectId?: number) => {
    const q = buildQuery({ team: teamId, team__agency__project: projectId, limit: 500 })
    try {
      const res = await api.get(`/sales-person/?${q}`)
      personList.value = res.data.results ?? res.data
    } catch (err) {
      personList.value = []
      console.warn('fetchPersonList failed:', (err as Error)?.message || err)
    }
  }

  const createPerson = (payload: Partial<SalesPerson>): Promise<boolean> =>
    runMutation(() => api.post('/sales-person/', payload), '영업 인력이 등록되었습니다.')

  const updatePerson = (id: number, payload: Partial<SalesPerson>): Promise<boolean> =>
    runMutation(() => api.patch(`/sales-person/${id}/`, payload), '영업 인력 정보가 수정되었습니다.')

  const deletePerson = (id: number): Promise<boolean> =>
    runMutation(() => api.delete(`/sales-person/${id}/`), '영업 인력이 삭제되었습니다.', 'warning')

  // ── 영업 인력 제출 증빙 서류 ──────────────────────────
  const personDocumentList = ref<SalesPersonDocument[]>([])

  const fetchPersonDocuments = async (salesPersonId: number) => {
    const q = buildQuery({ sales_person: salesPersonId, limit: 500 })
    try {
      const res = await api.get(`/sales-person-document/?${q}`)
      personDocumentList.value = res.data.results ?? res.data
    } catch (err) {
      personDocumentList.value = []
      console.warn('fetchPersonDocuments failed:', (err as Error)?.message || err)
    }
  }

  const uploadPersonDocument = (formData: FormData): Promise<boolean> =>
    runMutation(
      () =>
        api.post('/sales-person-document/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        }),
      '서류가 등록되었습니다.',
    )

  const verifyPersonDocument = (docId: number, isVerified: boolean): Promise<boolean> =>
    runMutation(
      () => api.post(`/sales-person-document/${docId}/verify/`, { is_verified: isVerified }),
      '서류 검증 상태가 변경되었습니다.',
      'success',
      true,
    )

  const deletePersonDocument = (docId: number): Promise<boolean> =>
    runMutation(
      () => api.delete(`/sales-person-document/${docId}/`),
      '서류가 삭제되었습니다.',
      'warning',
    )

  // ── 수수료 정책 ───────────────────────────────────────
  const policyList = ref<CommissionPolicy[]>([])

  const fetchPolicyList = async (projectId?: number) => {
    const q = buildQuery({ project: projectId, limit: 500 })
    try {
      const res = await api.get(`/sales-policy/?${q}`)
      policyList.value = res.data.results ?? res.data
    } catch (err) {
      policyList.value = []
      console.warn('fetchPolicyList failed:', (err as Error)?.message || err)
    }
  }

  const createPolicy = (payload: Partial<CommissionPolicy>): Promise<boolean> =>
    runMutation(() => api.post('/sales-policy/', payload), '수수료 정책이 등록되었습니다.')

  const updatePolicy = (id: number, payload: Partial<CommissionPolicy>): Promise<boolean> =>
    runMutation(() => api.patch(`/sales-policy/${id}/`, payload), '수수료 정책이 수정되었습니다.')

  const deletePolicy = (id: number): Promise<boolean> =>
    runMutation(() => api.delete(`/sales-policy/${id}/`), '수수료 정책이 삭제되었습니다.', 'warning')

  // ── 계약 영업 매핑 ─────────────────────────────────────
  const contractAgentList = ref<ContractSalesAgent[]>([])

  const fetchContractAgentList = async (projectId?: number, search?: string) => {
    const q = buildQuery({
      contract__project: projectId,
      search,
      limit: 3000,
    })
    try {
      const res = await api.get(`/sales-contract-agent/?${q}`)
      contractAgentList.value = res.data.results ?? res.data
    } catch (err) {
      contractAgentList.value = []
      console.warn('fetchContractAgentList failed:', (err as Error)?.message || err)
    }
  }

  const createContractAgent = (payload: Partial<ContractSalesAgent>): Promise<boolean> =>
    runMutation(
      () => api.post('/sales-contract-agent/', payload),
      '계약 영업 담당자가 지정되었습니다.',
    )

  const updateContractAgent = (id: number, payload: Partial<ContractSalesAgent>): Promise<boolean> =>
    runMutation(
      () => api.patch(`/sales-contract-agent/${id}/`, payload),
      '계약 영업 매핑이 수정되었습니다.',
    )

  const deleteContractAgent = (id: number): Promise<boolean> =>
    runMutation(
      () => api.delete(`/sales-contract-agent/${id}/`),
      '계약 영업 담당자 지정이 해제되었습니다.',
      'warning',
    )

  const toggleSettlementApproval = (
    id: number,
    approvalNote?: string,
    isApproved?: boolean,
  ): Promise<boolean> =>
    runMutation(
      () =>
        api.post(`/sales-contract-agent/${id}/toggle-approval/`, {
          approval_note: approvalNote,
          is_settlement_approved: isApproved,
        }),
      '정산 승인 상태가 변경되었습니다.',
      'success',
      true,
    )

  // ── 정산 회차 ─────────────────────────────────────────
  const periodList = ref<SettlementPeriod[]>([])

  const fetchPeriodList = async (projectId?: number) => {
    const q = buildQuery({ project: projectId, limit: 500 })
    try {
      const res = await api.get(`/sales-settlement-period/?${q}`)
      periodList.value = res.data.results ?? res.data
    } catch (err) {
      periodList.value = []
      console.warn('fetchPeriodList failed:', (err as Error)?.message || err)
    }
  }

  const createPeriod = (payload: Partial<SettlementPeriod>): Promise<boolean> =>
    runMutation(() => api.post('/sales-settlement-period/', payload), '정산 회차가 생성되었습니다.')

  const updatePeriod = (id: number, payload: Partial<SettlementPeriod>): Promise<boolean> =>
    runMutation(
      () => api.patch(`/sales-settlement-period/${id}/`, payload),
      '정산 회차가 수정되었습니다.',
    )

  const deletePeriod = (id: number): Promise<boolean> =>
    runMutation(
      () => api.delete(`/sales-settlement-period/${id}/`),
      '정산 회차가 삭제되었습니다.',
      'warning',
    )

  const generatePayouts = (periodId: number): Promise<boolean> =>
    runMutation(
      () => api.post(`/sales-settlement-period/${periodId}/generate-payouts/`),
      '수수료 정산이 완료되었습니다.',
      'success',
      true,
    )

  const confirmSettlement = (periodId: number): Promise<boolean> =>
    runMutation(
      () => api.post(`/sales-settlement-period/${periodId}/confirm-settlement/`),
      '정산이 확정되었습니다.',
      'success',
      true,
    )

  // ── 지급 명세 ─────────────────────────────────────────
  const payoutList = ref<CommissionPayout[]>([])
  const personPayoutHistoryList = ref<CommissionPayout[]>([])

  const fetchPayoutList = async (periodId?: number, payStatus?: string) => {
    const q = buildQuery({ period: periodId, pay_status: payStatus, limit: 1000 })
    try {
      const res = await api.get(`/sales-payout/?${q}`)
      payoutList.value = res.data.results ?? res.data
    } catch (err) {
      payoutList.value = []
      console.warn('fetchPayoutList failed:', (err as Error)?.message || err)
    }
  }

  const fetchPersonPayoutHistory = async (salesPersonId: number): Promise<boolean> => {
    const q = buildQuery({ sales_person: salesPersonId, limit: 500 })
    try {
      const res = await api.get(`/sales-payout/?${q}`)
      personPayoutHistoryList.value = res.data.results ?? res.data
      return true
    } catch (err) {
      personPayoutHistoryList.value = []
      errorHandle(err)
      return false
    }
  }

  const updatePayStatus = (payoutId: number, payStatus: string): Promise<boolean> =>
    runMutation(
      () => api.post(`/sales-payout/${payoutId}/update-pay-status/`, { pay_status: payStatus }),
      '지급 상태가 변경되었습니다.',
    )

  // ── 대행사 지급 명세 ─────────────────────────────────────
  const agencyPayoutList = ref<AgencyPayout[]>([])

  const fetchAgencyPayoutList = async (periodId?: number, agencyId?: number) => {
    const q = buildQuery({ period: periodId, agency: agencyId, limit: 500 })
    try {
      const res = await api.get(`/sales-agency-payout/?${q}`)
      agencyPayoutList.value = res.data.results ?? res.data
    } catch (err) {
      agencyPayoutList.value = []
      console.warn('fetchAgencyPayoutList failed:', (err as Error)?.message || err)
    }
  }

  const updateAgencyPayStatus = (payoutId: number, payStatus: string): Promise<boolean> =>
    runMutation(
      () =>
        api.post(`/sales-agency-payout/${payoutId}/update-pay-status/`, {
          pay_status: payStatus,
        }),
      '대행사 지급 상태가 변경되었습니다.',
    )

  // ── 조직 건강성 사전 진단 ─────────────────────────────────
  const validateOrgHealth = (projectId: number): Promise<OrgHealthCheckResult | void> =>
    api
      .get(`/sales-settlement-period/validate-org/?project=${projectId}`)
      .then(res => res.data as OrgHealthCheckResult)
      .catch(err => {
        errorHandle(err)
      })

  // ── 수수료 환수 ───────────────────────────────────────
  const clawbackList = ref<CommissionClawback[]>([])
  const personClawbackList = ref<CommissionClawback[]>([])

  const fetchClawbackList = async (salesPersonId?: number, projectId?: number) => {
    const q = buildQuery({
      sales_person: salesPersonId,
      contract__project: projectId,
      limit: 500,
    })
    try {
      const res = await api.get(`/sales-clawback/?${q}`)
      clawbackList.value = res.data.results ?? res.data
    } catch (err) {
      clawbackList.value = []
      console.warn('fetchClawbackList failed:', (err as Error)?.message || err)
    }
  }

  const fetchPersonClawbacks = async (salesPersonId: number): Promise<boolean> => {
    const q = buildQuery({ sales_person: salesPersonId, limit: 500 })
    try {
      const res = await api.get(`/sales-clawback/?${q}`)
      personClawbackList.value = res.data.results ?? res.data
      return true
    } catch (err) {
      personClawbackList.value = []
      errorHandle(err)
      return false
    }
  }

  return {
    agencyList,
    fetchAgencyList,
    createAgency,
    updateAgency,
    deleteAgency,

    teamList,
    fetchTeamList,
    createTeam,
    updateTeam,
    deleteTeam,

    personList,
    fetchPersonList,
    createPerson,
    updatePerson,
    deletePerson,

    personDocumentList,
    fetchPersonDocuments,
    uploadPersonDocument,
    verifyPersonDocument,
    deletePersonDocument,

    policyList,
    fetchPolicyList,
    createPolicy,
    updatePolicy,
    deletePolicy,

    contractAgentList,
    fetchContractAgentList,
    createContractAgent,
    updateContractAgent,
    deleteContractAgent,
    toggleSettlementApproval,

    periodList,
    fetchPeriodList,
    createPeriod,
    updatePeriod,
    deletePeriod,
    generatePayouts,
    confirmSettlement,

    payoutList,
    personPayoutHistoryList,
    fetchPayoutList,
    fetchPersonPayoutHistory,
    updatePayStatus,

    agencyPayoutList,
    fetchAgencyPayoutList,
    updateAgencyPayStatus,

    validateOrgHealth,

    clawbackList,
    personClawbackList,
    fetchClawbackList,
    fetchPersonClawbacks,
  }
})
