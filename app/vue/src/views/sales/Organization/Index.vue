<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { usePerms } from '@/composables/usePerms'
import { useProject } from '@/store/pinia/project'
import { useSales } from '@/store/pinia/sales'
import type { Project } from '@/store/types/project'
import type { SalesAgency, SalesPerson, SalesTeam } from '@/store/types/sales'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SalesAuthGuard from '@/components/AuthGuard/SalesAuthGuard.vue'
import AgencyTeamTree from './components/AgencyTeamTree.vue'
import PersonList from './components/PersonList.vue'
import AgencyFormModal from './components/AgencyFormModal.vue'
import TeamFormModal from './components/TeamFormModal.vue'
import PersonFormModal from './components/PersonFormModal.vue'
import PersonDocumentModal from './components/PersonDocumentModal.vue'

const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)
const navMenu = useSalesNavMenu(project)
const canSalesManage = computed(() =>
  project.value ? can(PERM.SALES_MANAGE, project.value) : can(PERM.SALES_MANAGE),
)

const salesStore = useSales()

// 선택된 대행사 및 팀
const selectedAgencyId = ref<number | null>(null)
const selectedTeamId = ref<number | null>(null)

// 모달 Refs
const agencyModalRef = ref()
const teamModalRef = ref()
const personModalRef = ref()
const docModalRef = ref()

const resetState = () => {
  selectedAgencyId.value = null
  selectedTeamId.value = null
  salesStore.agencyList = []
  salesStore.teamList = []
  salesStore.personList = []
}

const loadData = async (projId: number) => {
  await Promise.all([
    salesStore.fetchAgencyList(projId),
    salesStore.fetchTeamList(undefined, projId),
    salesStore.fetchPersonList(undefined, projId),
  ])
}

watch(
  project,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      resetState()
    }
    if (newVal && canSalesManage.value) {
      loadData(newVal)
    } else if (!newVal) {
      resetState()
    }
  },
  { immediate: true },
)

// 이벤트 핸들러
const onSelectAgency = (agencyId: number | null) => {
  selectedAgencyId.value = agencyId
  selectedTeamId.value = null
}

const onSelectTeam = (teamId: number | null, agencyId?: number | null) => {
  selectedTeamId.value = teamId
  if (teamId) {
    if (agencyId) {
      selectedAgencyId.value = agencyId
    } else {
      const team = salesStore.teamList.find(t => t.id === teamId)
      if (team) selectedAgencyId.value = team.agency
    }
  } else {
    selectedAgencyId.value = null
  }
}

// 모달 오픈
const openAddAgency = () => {
  if (!canSalesManage.value) return
  agencyModalRef.value?.open()
}
const openEditAgency = (agency: SalesAgency) => {
  if (!canSalesManage.value) return
  agencyModalRef.value?.open(agency)
}

const openAddTeam = (agencyId?: number) => {
  if (!canSalesManage.value) return
  teamModalRef.value?.open(undefined, agencyId)
}
const openEditTeam = (team: SalesTeam) => {
  if (!canSalesManage.value) return
  teamModalRef.value?.open(team)
}

const openAddPerson = () => {
  if (!canSalesManage.value) return
  personModalRef.value?.open(undefined, selectedTeamId.value ?? undefined)
}
const openEditPerson = (person: SalesPerson) => {
  if (!canSalesManage.value) return
  personModalRef.value?.open(person)
}
const openDocModal = (person: SalesPerson) => docModalRef.value?.open(person)

const onDataChanged = async () => {
  if (project.value) {
    await loadData(project.value)
  }
}
</script>

<template>
  <SalesAuthGuard :project="project" :required-perm="PERM.SALES_MANAGE">
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="p-3 p-md-4 pb-5">
        <div v-if="!project" class="py-5 text-center text-muted">
          <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
          <h5>프로젝트를 먼저 선택해 주세요.</h5>
          <p class="mb-0 text-secondary">
            상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 분양 대행 조직 및 인력을
            관리할 수 있습니다.
          </p>
        </div>

        <CRow v-else>
          <!-- 좌측: 영업 조직 (대행사 및 팀 트리) -->
          <CCol lg="4" xl="3">
            <AgencyTeamTree
              :project="project"
              :selected-agency-id="selectedAgencyId"
              :selected-team-id="selectedTeamId"
              @select-agency="onSelectAgency"
              @select-team="onSelectTeam"
              @add-agency="openAddAgency"
              @edit-agency="openEditAgency"
              @add-team="openAddTeam"
              @edit-team="openEditTeam"
            />
          </CCol>

          <!-- 우측: 영업 인력 목록 -->
          <CCol lg="8" xl="9">
            <PersonList
              :project="project"
              :selected-agency-id="selectedAgencyId"
              :selected-team-id="selectedTeamId"
              @add-person="openAddPerson"
              @edit-person="openEditPerson"
              @open-docs="openDocModal"
            />
          </CCol>
        </CRow>
      </CCardBody>

      <!-- 모달 다이얼로그들 -->
      <AgencyFormModal
        v-if="project"
        ref="agencyModalRef"
        :project="project"
        @saved="onDataChanged"
      />
      <TeamFormModal
        ref="teamModalRef"
        :agency-id="selectedAgencyId ?? undefined"
        @saved="onDataChanged"
      />
      <PersonFormModal
        ref="personModalRef"
        :default-team-id="selectedTeamId ?? undefined"
        @saved="onDataChanged"
        @open-docs="openDocModal"
      />
      <PersonDocumentModal ref="docModalRef" :project="project" @updated="onDataChanged" />
    </ContentBody>
  </SalesAuthGuard>
</template>
