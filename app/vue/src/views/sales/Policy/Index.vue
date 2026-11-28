<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { usePerms } from '@/composables/usePerms'
import { useSales } from '@/store/pinia/sales'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { bgLight, TableSecondary } from '@/utils/cssMixins'
import { useProjectData } from '@/store/pinia/project_data'
import type { Project } from '@/store/types/project'
import type { CommissionPolicy } from '@/store/types/sales'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import SalesAuthGuard from '@/components/AuthGuard/SalesAuthGuard.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import PolicyFormModal from './components/PolicyFormModal.vue'

const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project | null)?.pk)
const navMenu = useSalesNavMenu(project)
const canSalesPolicy = computed(() =>
  project.value ? can(PERM.SALES_POLICY, project.value) : can(PERM.SALES_POLICY),
)

const pDataStore = useProjectData()
const unitTypeList = computed(() => pDataStore.unitTypeList)

const contStore = useContract()
const orderGroupList = computed(() => contStore.orderGroupList)

const salesStore = useSales()
const policyList = computed(() => salesStore.policyList)

// 필터 상태
const filterOrderGroup = ref<number | null>(null)
const filterUnitType = ref<number | null>(null)
const filterActive = ref<string>('true')
const search = ref('')

const policyModalRef = ref()
const confirmModalRef = ref()
const pendingDeletePolicy = ref<CommissionPolicy | null>(null)

const resetFiltersAndLists = () => {
  filterOrderGroup.value = null
  filterUnitType.value = null
  filterActive.value = 'true'
  search.value = ''
  salesStore.policyList = []
}

const loadData = async (projId: number) => {
  await Promise.all([
    salesStore.fetchPolicyList(projId),
    pDataStore.fetchTypeList(projId),
    contStore.fetchOrderGroupList(projId),
  ])
}

watch(
  project,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      resetFiltersAndLists()
    }
    if (newVal && canSalesPolicy.value) {
      loadData(newVal)
    } else if (!newVal) {
      resetFiltersAndLists()
    }
  },
  { immediate: true },
)

const filteredPolicies = computed(() => {
  return policyList.value.filter(p => {
    if (filterOrderGroup.value && p.order_group !== filterOrderGroup.value) return false
    if (filterUnitType.value && p.unit_type !== filterUnitType.value) return false
    if (filterActive.value !== '') {
      const isActive = filterActive.value === 'true'
      if (p.is_active !== isActive) return false
    }
    if (search.value.trim()) {
      const q = search.value.trim().toLowerCase()
      if (!p.name.toLowerCase().includes(q)) return false
    }
    return true
  })
})

const conditionBadgeColor: Record<string, string> = {
  '1': 'success',
  '2': 'primary',
  '3': 'warning',
  '4': 'info',
}

const parseNumberOrNull = (val: string | string[] | undefined): number | null =>
  val && !Array.isArray(val) ? Number(val) : null

const openAddPolicy = () => {
  if (!canSalesPolicy.value) return
  policyModalRef.value?.open()
}

const openEditPolicy = (policy: CommissionPolicy) => {
  if (!canSalesPolicy.value) return
  policyModalRef.value?.open(policy)
}

const deletePolicy = (policy: CommissionPolicy) => {
  if (!canSalesPolicy.value) return
  pendingDeletePolicy.value = policy
  confirmModalRef.value?.callModal()
}

const executeDeletePolicy = async () => {
  if (!pendingDeletePolicy.value) return
  confirmModalRef.value?.close()
  const ok = await salesStore.deletePolicy(pendingDeletePolicy.value.id)
  pendingDeletePolicy.value = null
  if (ok && project.value) {
    await salesStore.fetchPolicyList(project.value)
  }
}

const onSaved = async () => {
  if (project.value) {
    await salesStore.fetchPolicyList(project.value)
  }
}
</script>

<template>
  <SalesAuthGuard :project="project" :required-perm="PERM.SALES_POLICY">
    <ContentHeader :page-title="pageTitle" :nav-menu="navMenu" selector="ProjectSelect" />

    <ContentBody>
      <CCardBody class="p-3 p-md-4 pb-5">
        <div v-if="!project" class="py-5 text-center text-muted">
          <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
          <h5>프로젝트를 먼저 선택해 주세요.</h5>
          <p class="mb-0 text-secondary">
            상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 수수료 정책을 관리할 수
            있습니다.
          </p>
        </div>

        <div v-else>
          <CCard class="shadow-sm mb-4">
            <!-- 헤더 및 필터 컨트롤러 -->
            <CCardHeader
              :class="bgLight"
              class="d-flex flex-wrap justify-content-between align-items-center py-2"
            >
              <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
                <v-icon icon="mdi-cog-outline" size="small" class="me-1 text-primary" />
                수수료 정책 (R값 기준표)
                <v-chip color="info" class="ms-2" variant="flat" size="x-small">
                  {{ filteredPolicies.length }}개
                </v-chip>
              </div>

              <div class="d-flex flex-wrap align-items-center gap-2">
                <!-- 차수 필터 -->
                <CFormSelect
                  :model-value="filterOrderGroup ? String(filterOrderGroup) : ''"
                  style="width: 150px"
                  @update:model-value="val => (filterOrderGroup = parseNumberOrNull(val))"
                >
                  <option value="">전체 차수</option>
                  <option v-for="og in orderGroupList" :key="og.pk" :value="String(og.pk)">
                    {{ og.name }}
                  </option>
                </CFormSelect>

                <!-- 타입 필터 -->
                <CFormSelect
                  :model-value="filterUnitType ? String(filterUnitType) : ''"
                  style="width: 150px"
                  @update:model-value="val => (filterUnitType = parseNumberOrNull(val))"
                >
                  <option value="">전체 타입</option>
                  <option v-for="t in unitTypeList" :key="t.pk" :value="String(t.pk)">
                    {{ t.name }}
                  </option>
                </CFormSelect>

                <!-- 활성화 필터 -->
                <CFormSelect v-model="filterActive" style="width: 150px">
                  <option value="">전체 상태</option>
                  <option value="true">활성 정책</option>
                  <option value="false">비활성 정책</option>
                </CFormSelect>

                <!-- 검색창 -->
                <CFormInput v-model="search" placeholder="정책명 검색" style="width: 150px" />

                <!-- 신규 등록 버튼 -->
                <v-btn
                  v-if="canSalesPolicy"
                  color="primary"
                  size="small"
                  @click="openAddPolicy"
                >
                  <v-icon icon="mdi-plus" size="small" class="me-1" />
                  신규 정책 등록
                </v-btn>
              </div>
            </CCardHeader>

            <!-- 테이블 목록 -->
            <CCardBody class="p-0">
              <CTable
                hover
                responsive
                bordered
                align="middle"
                class="mb-0 text-center text-body small"
              >
                <colgroup>
                  <col style="width: 14%" />
                  <col style="width: 10%" />
                  <col style="width: 8%" />
                  <col style="width: 8%" />
                  <col style="width: 8%" />
                  <col style="width: 8%" />
                  <col style="width: 11%" />
                  <col style="width: 11%" />
                  <col style="width: 10%" />
                  <col style="width: 6%" />
                  <col style="width: 6%" />
                </colgroup>
                <CTableHead :color="TableSecondary">
                  <CTableRow>
                    <CTableHeaderCell>정책명</CTableHeaderCell>
                    <CTableHeaderCell>적용 대상 (차수/타입)</CTableHeaderCell>
                    <CTableHeaderCell>상담사 수수료</CTableHeaderCell>
                    <CTableHeaderCell>팀장 수수료</CTableHeaderCell>
                    <CTableHeaderCell>본부장 수수료</CTableHeaderCell>
                    <CTableHeaderCell>대행사 수수료</CTableHeaderCell>
                    <CTableHeaderCell>
                      건당 총 수수료
                      <span class="small text-warning fw-normal ms-2">VAT 별도</span>
                    </CTableHeaderCell>
                    <CTableHeaderCell class="table-warning">
                      VAT 포함 청구금액
                      <span class="small text-body fw-normal ms-2">공급가 + 부가세 10%</span>
                    </CTableHeaderCell>
                    <CTableHeaderCell>지급 조건</CTableHeaderCell>
                    <CTableHeaderCell>상태</CTableHeaderCell>
                    <CTableHeaderCell>관리</CTableHeaderCell>
                  </CTableRow>
                </CTableHead>

                <CTableBody>
                  <CTableRow v-for="policy in filteredPolicies" :key="policy.id">
                    <!-- 정책명 -->
                    <CTableDataCell class="fw-bold">
                      <a
                        v-if="canSalesPolicy"
                        href="#"
                        class="text-primary text-decoration-none"
                        @click.prevent="openEditPolicy(policy)"
                      >
                        {{ policy.name }}
                      </a>
                      <span v-else>{{ policy.name }}</span>
                      <span class="small text-muted font-monospace ms-2">
                        (적용일: {{ policy.start_date }} ~ {{ policy.end_date || '종료일 없음' }})
                      </span>
                    </CTableDataCell>

                    <!-- 차수 및 타입 -->
                    <CTableDataCell>
                      <span v-if="policy.order_group_name" class="badge bg-secondary me-1">
                        {{ policy.order_group_name }}
                      </span>
                      <span v-else class="text-muted">전체차수</span>
                      /
                      <span v-if="policy.unit_type_name" class="badge bg-info">
                        {{ policy.unit_type_name }}
                      </span>
                      <span v-else class="text-muted">전체타입</span>
                    </CTableDataCell>

                    <!-- 상담사 -->
                    <CTableDataCell class="text-end">
                      {{ policy.agent_fee.toLocaleString() }}원
                    </CTableDataCell>

                    <!-- 팀장 -->
                    <CTableDataCell class="text-end">
                      {{ policy.leader_fee.toLocaleString() }}원
                    </CTableDataCell>

                    <!-- 본부장 -->
                    <CTableDataCell class="text-end">
                      {{ policy.director_fee.toLocaleString() }}원
                    </CTableDataCell>

                    <!-- 대행사 -->
                    <CTableDataCell class="text-end">
                      {{ policy.agency_fee.toLocaleString() }}원
                    </CTableDataCell>

                    <!-- 건당 총 수수료 (VAT 별도) -->
                    <CTableDataCell class="text-end fw-bold">
                      {{
                        (
                          policy.agent_fee +
                          policy.leader_fee +
                          policy.director_fee +
                          policy.agency_fee
                        ).toLocaleString()
                      }}원
                      <span class="small text-muted ms-2">VAT 별도</span>
                    </CTableDataCell>

                    <!-- VAT 포함 청구금액 -->
                    <CTableDataCell class="text-end fw-bold text-danger table-warning">
                      {{
                        Math.floor(
                          (policy.agent_fee +
                            policy.leader_fee +
                            policy.director_fee +
                            policy.agency_fee) *
                            1.1,
                        ).toLocaleString()
                      }}원
                      <span class="small text-muted ms-2"> VAT 포함 </span>
                    </CTableDataCell>

                    <!-- 지급 조건 -->
                    <CTableDataCell>
                      <v-chip
                        :color="conditionBadgeColor[policy.pay_condition] || 'secondary'"
                        shape="rounded-pill"
                        variant="flat"
                        size="x-small"
                      >
                        {{ policy.pay_condition_display }}
                      </v-chip>
                    </CTableDataCell>

                    <!-- 상태 -->
                    <CTableDataCell>
                      <v-chip
                        :color="policy.is_active ? 'success' : 'secondary'"
                        variant="flat"
                        size="x-small"
                      >
                        {{ policy.is_active ? '활성' : '비활성' }}
                      </v-chip>
                    </CTableDataCell>

                    <!-- 관리 버튼 -->
                    <CTableDataCell>
                      <template v-if="canSalesPolicy">
                        <v-btn
                          icon="mdi-pencil"
                          size="x-small"
                          variant="text"
                          color="success"
                          title="수정"
                          @click="openEditPolicy(policy)"
                        />
                        <v-btn
                          icon="mdi-delete"
                          size="x-small"
                          variant="text"
                          color="danger"
                          title="삭제"
                          @click="deletePolicy(policy)"
                        />
                      </template>
                      <span v-else class="text-muted">-</span>
                    </CTableDataCell>
                  </CTableRow>

                  <CTableRow v-if="filteredPolicies.length === 0">
                    <CTableDataCell colspan="11" class="py-5 text-center text-muted">
                      등록된 수수료 정책이 없거나 조건에 일치하는 결과가 없습니다.
                    </CTableDataCell>
                  </CTableRow>
                </CTableBody>
              </CTable>
            </CCardBody>
          </CCard>
        </div>
      </CCardBody>

      <!-- 등록/수정 모달 -->
      <PolicyFormModal
        v-if="project"
        ref="policyModalRef"
        :project="project"
        :order-group-list="orderGroupList"
        :unit-type-list="unitTypeList"
        @saved="onSaved"
      />

      <!-- 삭제 확인 모달 -->
      <ConfirmModal ref="confirmModalRef">
        <template #header>수수료 정책 삭제 확인</template>
        <template #default>
          <p class="mb-0">
            <strong>[{{ pendingDeletePolicy?.name }}]</strong> 수수료 정책을 삭제하시겠습니까?
          </p>
          <p class="text-danger small mt-2 mb-0">
            * 삭제 시 해당 정책을 참조하는 미정산 계약 매핑의 적용 정책 연결이 해제되며 기본 정책으로
            대체됩니다.
          </p>
        </template>
        <template #footer>
          <v-btn size="small" color="danger" @click="executeDeletePolicy">삭제</v-btn>
        </template>
      </ConfirmModal>
    </ContentBody>
  </SalesAuthGuard>
</template>

<style scoped lang="scss">
.dark-theme .table-warning {
  background-color: #4c422a !important;
  color: #fff !important;
}
</style>
