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
} from '@/store/types/sales'

export const useSales = defineStore('sales', () => {
  // ── 대행사 ─────────────────────────────────────────────
  const agencyList = ref<SalesAgency[]>([])

  const fetchAgencyList = (projectId?: number) => {
    const params = new URLSearchParams()
    if (projectId) params.append('project', String(projectId))
    return api
      .get(`/sales-agency/?${params}`)
      .then(res => (agencyList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchAgencyList failed:', err?.message || err)
      })
  }

  const createAgency = (payload: Partial<SalesAgency>) =>
    api
      .post('/sales-agency/', payload)
      .then(res => {
        message('success', '알림!', '분양 대행사가 등록되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const updateAgency = (id: number, payload: Partial<SalesAgency>) =>
    api
      .patch(`/sales-agency/${id}/`, payload)
      .then(res => {
        message('success', '알림!', '분양 대행사 정보가 수정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deleteAgency = (id: number) =>
    api
      .delete(`/sales-agency/${id}/`)
      .then(() => {
        message('warning', '알림!', '분양 대행사가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // ── 영업 팀 ───────────────────────────────────────────
  const teamList = ref<SalesTeam[]>([])

  const fetchTeamList = (agencyId?: number, projectId?: number) => {
    const params = new URLSearchParams()
    if (agencyId) params.append('agency', String(agencyId))
    if (projectId) params.append('agency__project', String(projectId))
    return api
      .get(`/sales-team/?${params}`)
      .then(res => (teamList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchTeamList failed:', err?.message || err)
      })
  }

  const createTeam = (payload: Partial<SalesTeam>) =>
    api
      .post('/sales-team/', payload)
      .then(res => {
        message('success', '알림!', '영업 조직/팀이 등록되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const updateTeam = (id: number, payload: Partial<SalesTeam>) =>
    api
      .patch(`/sales-team/${id}/`, payload)
      .then(res => {
        message('success', '알림!', '영업 조직/팀 정보가 수정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deleteTeam = (id: number) =>
    api
      .delete(`/sales-team/${id}/`)
      .then(() => {
        message('warning', '알림!', '영업 조직/팀이 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // ── 영업 인력 (분양상담사 등) ─────────────────────────
  const personList = ref<SalesPerson[]>([])

  const fetchPersonList = (teamId?: number, projectId?: number) => {
    const params = new URLSearchParams()
    if (teamId) params.append('team', String(teamId))
    if (projectId) params.append('team__agency__project', String(projectId))
    return api
      .get(`/sales-person/?${params}`)
      .then(res => (personList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchPersonList failed:', err?.message || err)
      })
  }

  const createPerson = (payload: Partial<SalesPerson>) =>
    api
      .post('/sales-person/', payload)
      .then(res => {
        message('success', '알림!', '영업 인력이 등록되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const updatePerson = (id: number, payload: Partial<SalesPerson>) =>
    api
      .patch(`/sales-person/${id}/`, payload)
      .then(res => {
        message('success', '알림!', '영업 인력 정보가 수정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deletePerson = (id: number) =>
    api
      .delete(`/sales-person/${id}/`)
      .then(() => {
        message('warning', '알림!', '영업 인력이 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // ── 영업 인력 제출 증빙 서류 ──────────────────────────
  const personDocumentList = ref<SalesPersonDocument[]>([])

  const fetchPersonDocuments = (salesPersonId: number) => {
    return api
      .get(`/sales-person-document/?sales_person=${salesPersonId}`)
      .then(res => (personDocumentList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchPersonDocuments failed:', err?.message || err)
      })
  }

  const uploadPersonDocument = (formData: FormData) =>
    api
      .post('/sales-person-document/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then(res => {
        message('success', '알림!', '서류가 등록되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const verifyPersonDocument = (docId: number, isVerified: boolean) =>
    api
      .post(`/sales-person-document/${docId}/verify/`, { is_verified: isVerified })
      .then(res => {
        message('success', '알림!', res.data?.detail || '서류 검증 상태가 변경되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deletePersonDocument = (docId: number) =>
    api
      .delete(`/sales-person-document/${docId}/`)
      .then(() => {
        message('warning', '알림!', '서류가 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // ── 수수료 정책 ───────────────────────────────────────
  const policyList = ref<CommissionPolicy[]>([])

  const fetchPolicyList = (projectId?: number) => {
    const params = new URLSearchParams()
    if (projectId) params.append('project', String(projectId))
    return api
      .get(`/sales-policy/?${params}`)
      .then(res => (policyList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchPolicyList failed:', err?.message || err)
      })
  }

  const createPolicy = (payload: Partial<CommissionPolicy>) =>
    api
      .post('/sales-policy/', payload)
      .then(res => {
        message('success', '알림!', '수수료 정책이 등록되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const updatePolicy = (id: number, payload: Partial<CommissionPolicy>) =>
    api
      .patch(`/sales-policy/${id}/`, payload)
      .then(res => {
        message('success', '알림!', '수수료 정책이 수정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deletePolicy = (id: number) =>
    api
      .delete(`/sales-policy/${id}/`)
      .then(() => {
        message('warning', '알림!', '수수료 정책이 삭제되었습니다.')
      })
      .catch(err => errorHandle(err))

  // ── 계약 영업 매핑 ─────────────────────────────────────
  const contractAgentList = ref<ContractSalesAgent[]>([])

  const fetchContractAgentList = (projectId?: number, search?: string) => {
    const params = new URLSearchParams()
    if (projectId) params.append('team__agency__project', String(projectId))
    if (search) params.append('search', search)
    return api
      .get(`/sales-contract-agent/?${params}`)
      .then(res => (contractAgentList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchContractAgentList failed:', err?.message || err)
      })
  }

  const createContractAgent = (payload: Partial<ContractSalesAgent>) =>
    api
      .post('/sales-contract-agent/', payload)
      .then(res => {
        message('success', '알림!', '계약 영업 담당자가 지정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const updateContractAgent = (id: number, payload: Partial<ContractSalesAgent>) =>
    api
      .patch(`/sales-contract-agent/${id}/`, payload)
      .then(res => {
        message('success', '알림!', '계약 영업 매핑이 수정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const deleteContractAgent = (id: number) =>
    api
      .delete(`/sales-contract-agent/${id}/`)
      .then(() => {
        message('warning', '알림!', '계약 영업 담당자 지정이 해제되었습니다.')
      })
      .catch(err => errorHandle(err))

  const toggleSettlementApproval = (id: number, approvalNote?: string) =>
    api
      .post(`/sales-contract-agent/${id}/toggle-approval/`, { approval_note: approvalNote })
      .then(res => {
        message('success', '알림!', res.data.detail || '정산 승인 상태가 변경되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  // ── 정산 회차 ─────────────────────────────────────────
  const periodList = ref<SettlementPeriod[]>([])

  const fetchPeriodList = (projectId?: number) => {
    const params = new URLSearchParams()
    if (projectId) params.append('project', String(projectId))
    params.append('limit', '500')
    return api
      .get(`/sales-settlement-period/?${params}`)
      .then(res => (periodList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchPeriodList failed:', err?.message || err)
      })
  }

  const createPeriod = (payload: Partial<SettlementPeriod>) =>
    api
      .post('/sales-settlement-period/', payload)
      .then(res => {
        message('success', '알림!', '정산 회차가 생성되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const generatePayouts = (periodId: number) =>
    api
      .post(`/sales-settlement-period/${periodId}/generate-payouts/`)
      .then(res => {
        message('success', '알림!', res.data.detail ?? '수수료 정산이 완료되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  const confirmSettlement = (periodId: number) =>
    api
      .post(`/sales-settlement-period/${periodId}/confirm-settlement/`)
      .then(res => {
        message('success', '알림!', res.data.detail ?? '정산이 확정되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  // ── 지급 명세 ─────────────────────────────────────────
  const payoutList = ref<CommissionPayout[]>([])

  const fetchPayoutList = (periodId?: number, payStatus?: string) => {
    const params = new URLSearchParams()
    if (periodId) params.append('period', String(periodId))
    if (payStatus) params.append('pay_status', payStatus)
    params.append('limit', '1000')
    return api
      .get(`/sales-payout/?${params}`)
      .then(res => (payoutList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchPayoutList failed:', err?.message || err)
      })
  }

  const updatePayStatus = (payoutId: number, payStatus: string) =>
    api
      .post(`/sales-payout/${payoutId}/update-pay-status/`, { pay_status: payStatus })
      .then(res => {
        message('success', '알림!', '지급 상태가 변경되었습니다.')
        return res.data
      })
      .catch(err => errorHandle(err))

  // ── 수수료 환수 ───────────────────────────────────────
  const clawbackList = ref<CommissionClawback[]>([])

  const fetchClawbackList = (salesPersonId?: number) => {
    const params = new URLSearchParams()
    if (salesPersonId) params.append('sales_person', String(salesPersonId))
    return api
      .get(`/sales-clawback/?${params}`)
      .then(res => (clawbackList.value = res.data.results ?? res.data))
      .catch(err => {
        console.warn('fetchClawbackList failed:', err?.message || err)
      })
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
    generatePayouts,
    confirmSettlement,

    payoutList,
    fetchPayoutList,
    updatePayStatus,

    clawbackList,
    fetchClawbackList,
  }
})
