<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { navMenu, pageTitle } from '@/views/contracts/_menu/headermixin'
import { useContract } from '@/store/pinia/contract'
import { useProject } from '@/store/pinia/project'
import type { Project } from '@/store/types/project'
import type { Contract, Contractor } from '@/store/types/contract'
import Loading from '@/components/Loading/Index.vue'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import ContractAuthGuard from '@/components/AuthGuard/ContractAuthGuard.vue'
import ContractManage from './components/ContractManage.vue'
import ContNavigation from './components/ContNavigation.vue'
import ContController from './components/ContController.vue'
import ContractorAlert from './components/ContractorAlert.vue'

const route = useRoute()
const projStore = useProject()
const contStore = useContract()

const loading = ref(true)

// 안전한 정수 파싱 헬퍼 (NaN 방어)
const parseNumber = (val: unknown): number | null => {
  if (!val) return null
  const parsed = parseInt(String(val), 10)
  return Number.isNaN(parsed) ? null : parsed
}

// URL 파라미터 안전 바인딩
const contractorId = computed(() => parseNumber(route.params.contractorId))
const fromPage = computed(() => parseNumber(route.query.from_page))
const project = computed<number | null>(() => (projStore.project as Project)?.pk ?? null)

const contract = computed(() => contStore.contract as Contract | null)
const contractor = computed(() => contStore.contractor as Contractor | null)

// 전체 계약 데이터 리셋
const resetContractData = () => {
  contStore.removeContract()
  contStore.removeContractor()
  contStore.contAddressList = []
}

// 계약 및 계약자 정보 로드 (병렬화 및 중복 호출 제거)
const loadContractData = async (contorId: number) => {
  try {
    // 계약자 정보와 주소 이력 목록을 병렬로 동시 요청 (Waterfall 제거)
    await Promise.all([
      contStore.fetchContractor(contorId, project.value ?? undefined),
      contStore.fetchContAddressList(contorId),
    ])

    // 계약자 레코드에 연관된 계약 pk가 유효한 경우에만 계약 정보 요청
    const contractPk = contStore.contractor?.contract
    if (contractPk) {
      await contStore.fetchContract(contractPk)
    } else {
      contStore.removeContract()
    }
  } catch (error) {
    console.error('계약 정보를 불러오는 중 오류가 발생했습니다:', error)
    resetContractData()
  }
}

// 기초 메타 데이터 세팅 (Promise 대기 보장)
const dataSetup = async (projId: number) => {
  await contStore.fetchRequiredDocsList(projId)
}

const dataReset = () => {
  contStore.requiredDocsList = []
}

const projSelect = async (target: number | null) => {
  dataReset()
  if (target) await dataSetup(target)
}

// 라우트 파라미터 감시 (상태 잔류 버그 해결)
watch(
  contractorId,
  async newId => {
    if (newId) {
      await loadContractData(newId)
    } else {
      // 계약자가 선택 해제되면 이전 계약 정보 및 주소 목록 완전 초기화
      resetContractData()
    }
  },
)

onBeforeMount(async () => {
  const projId = project.value || projStore.currentProject
  if (projId) {
    await dataSetup(projId)

    if (contractorId.value) {
      await loadContractData(contractorId.value)
    } else {
      resetContractData()
    }
  }
  loading.value = false
})
</script>

<template>
  <ContractAuthGuard>
    <Loading v-model:active="loading" />
    <ContentHeader
      :page-title="pageTitle"
      :nav-menu="navMenu"
      selector="ProjectSelect"
      :selectable="false"
      @proj-select="projSelect"
    />

    <ContentBody>
      <CCardBody class="pb-5">
        <ContNavigation :cont-on="!!contract" :contractor="contractor?.pk" />
        <ContController :project="project ?? undefined" />
        <ContractorAlert
          v-if="contractor"
          :is-blank="!contract"
          :contractor="contractor"
          clear-route="계약 상세 관리"
        />

        <ContractManage
          :project="project ?? undefined"
          :contract="contract ?? undefined"
          :contractor="contractor ?? undefined"
          :from-page="fromPage"
        />
      </CCardBody>
    </ContentBody>
  </ContractAuthGuard>
</template>
