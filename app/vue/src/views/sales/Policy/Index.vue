<script lang="ts" setup>
import { ref, computed, watch, onMounted } from 'vue'
import { pageTitle, useSalesNavMenu } from '@/views/sales/_menu/headermixin'
import { useProject } from '@/store/pinia/project'
import { useProjectData } from '@/store/pinia/project_data'
import { useContract } from '@/store/pinia/contract'
import { useSales } from '@/store/pinia/sales'
import type { Project } from '@/store/types/project'
import type { CommissionPolicy } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'
import { usePerms } from '@/composables/usePerms'
import ContentHeader from '@/layouts/ContentHeader/Index.vue'
import ContentBody from '@/layouts/ContentBody/Index.vue'
import PolicyFormModal from './components/PolicyFormModal.vue'

const { can, PERM } = usePerms()
const projStore = useProject()
const project = computed(() => (projStore.project as Project)?.pk)
const navMenu = useSalesNavMenu(project)

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

const loadData = async (projId: number) => {
  await Promise.all([
    salesStore.fetchPolicyList(projId),
    pDataStore.fetchTypeList(projId),
    contStore.fetchOrderGroupList(projId),
  ])
}

const projSelect = async (projId: number | null) => {
  if (projId) {
    await loadData(projId)
  }
}

watch(
  project,
  newVal => {
    if (newVal) loadData(newVal)
  },
  { immediate: true },
)

onMounted(() => {
  if (project.value) {
    loadData(project.value)
  }
})

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

const openAddPolicy = () => policyModalRef.value?.open()
const openEditPolicy = (policy: CommissionPolicy) => policyModalRef.value?.open(policy)

const deletePolicy = async (policy: CommissionPolicy) => {
  if (confirm(`'${policy.name}' 수수료 정책을 삭제하시겠습니까?`)) {
    await salesStore.deletePolicy(policy.id)
    if (project.value) {
      await salesStore.fetchPolicyList(project.value)
    }
  }
}

const onSaved = async () => {
  if (project.value) {
    await salesStore.fetchPolicyList(project.value)
  }
}
</script>

<template>
  <ContentHeader
    :page-title="pageTitle"
    :nav-menu="navMenu"
    selector="ProjectSelect"
    @proj-select="projSelect"
  />

  <ContentBody>
    <CCardBody class="p-3 p-md-4 pb-5">
      <div v-if="!project" class="py-5 text-center text-muted">
      <v-icon icon="mdi-alert-circle-outline" size="large" class="mb-2 text-warning" />
      <h5>프로젝트를 먼저 선택해 주세요.</h5>
      <p class="mb-0 text-secondary">
        상단 프로젝트 선택 메뉴에서 관리하실 프로젝트를 선택하시면 수수료 정책을 관리할 수 있습니다.
      </p>
    </div>

    <div v-else>
      <CCard class="shadow-sm mb-4">
        <!-- 헤더 및 필터 컨트롤러 -->
        <CCardHeader class="bg-light d-flex flex-wrap justify-content-between align-items-center py-2">
          <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
            <v-icon icon="mdi-cog-outline" size="small" class="mr-1 text-primary" />
            수수료 정책 (R값 기준표)
            <CBadge color="primary" class="ml-2" shape="rounded-pill">
              {{ filteredPolicies.length }}개
            </CBadge>
          </div>

          <div class="d-flex flex-wrap align-items-center gap-2">
            <!-- 차수 필터 -->
            <CFormSelect v-model.number="filterOrderGroup" size="sm" style="width: 130px">
              <option :value="null">전체 차수</option>
              <option v-for="og in orderGroupList" :key="og.pk" :value="og.pk">
                {{ og.name }}
              </option>
            </CFormSelect>

            <!-- 타입 필터 -->
            <CFormSelect v-model.number="filterUnitType" size="sm" style="width: 130px">
              <option :value="null">전체 타입</option>
              <option v-for="t in unitTypeList" :key="t.pk" :value="t.pk">
                {{ t.name }}
              </option>
            </CFormSelect>

            <!-- 활성화 필터 -->
            <CFormSelect v-model="filterActive" size="sm" style="width: 110px">
              <option value="">전체 상태</option>
              <option value="true">활성 정책</option>
              <option value="false">비활성 정책</option>
            </CFormSelect>

            <!-- 검색창 -->
            <CFormInput
              v-model="search"
              size="sm"
              placeholder="정책명 검색"
              style="width: 150px"
            />

            <!-- 신규 등록 버튼 -->
            <v-btn
              v-if="can(PERM.SALES_POLICY)"
              color="primary"
              size="small"
              @click="openAddPolicy"
            >
              <v-icon icon="mdi-plus" size="small" class="mr-1" />
              신규 정책 등록
            </v-btn>
          </div>
        </CCardHeader>

        <!-- 테이블 목록 -->
        <CCardBody class="p-0">
          <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
            <colgroup>
              <col style="width: 18%" />
              <col style="width: 12%" />
              <col style="width: 9%" />
              <col style="width: 9%" />
              <col style="width: 9%" />
              <col style="width: 9%" />
              <col style="width: 11%" />
              <col style="width: 11%" />
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
                <CTableHeaderCell>건당 총 수수료</CTableHeaderCell>
                <CTableHeaderCell>지급 조건</CTableHeaderCell>
                <CTableHeaderCell>상태</CTableHeaderCell>
                <CTableHeaderCell>관리</CTableHeaderCell>
              </CTableRow>
            </CTableHead>

            <CTableBody>
              <CTableRow v-for="policy in filteredPolicies" :key="policy.id">
                <!-- 정책명 -->
                <CTableDataCell class="text-left font-weight-bold">
                  <a
                    v-if="can(PERM.SALES_POLICY)"
                    href="javascript:void(0);"
                    class="text-primary text-decoration-none"
                    @click="openEditPolicy(policy)"
                  >
                    {{ policy.name }}
                  </a>
                  <span v-else>{{ policy.name }}</span>
                  <div class="small text-muted font-monospace">
                    적용일: {{ policy.start_date }} ~ {{ policy.end_date || '종료일 없음' }}
                  </div>
                </CTableDataCell>

                <!-- 차수 및 타입 -->
                <CTableDataCell>
                  <div>
                    <span v-if="policy.order_group_name" class="badge bg-secondary mr-1">
                      {{ policy.order_group_name }}
                    </span>
                    <span v-else class="text-muted">전체차수</span>
                  </div>
                  <div>
                    <span v-if="policy.unit_type_name" class="badge bg-info">
                      {{ policy.unit_type_name }}
                    </span>
                    <span v-else class="text-muted">전체타입</span>
                  </div>
                </CTableDataCell>

                <!-- 상담사 -->
                <CTableDataCell class="text-right font-monospace">
                  {{ policy.agent_fee.toLocaleString() }}원
                </CTableDataCell>

                <!-- 팀장 -->
                <CTableDataCell class="text-right font-monospace">
                  {{ policy.leader_fee.toLocaleString() }}원
                </CTableDataCell>

                <!-- 본부장 -->
                <CTableDataCell class="text-right font-monospace">
                  {{ policy.director_fee.toLocaleString() }}원
                </CTableDataCell>

                <!-- 대행사 -->
                <CTableDataCell class="text-right font-monospace">
                  {{ policy.agency_fee.toLocaleString() }}원
                </CTableDataCell>

                <!-- 건당 총액 -->
                <CTableDataCell class="text-right font-monospace fw-bold text-danger">
                  {{ (policy.agent_fee + policy.leader_fee + policy.director_fee + policy.agency_fee).toLocaleString() }}원
                </CTableDataCell>

                <!-- 지급 조건 -->
                <CTableDataCell>
                  <CBadge :color="conditionBadgeColor[policy.pay_condition] || 'secondary'" shape="rounded-pill">
                    {{ policy.pay_condition_display }}
                  </CBadge>
                </CTableDataCell>

                <!-- 상태 -->
                <CTableDataCell>
                  <CBadge :color="policy.is_active ? 'success' : 'secondary'">
                    {{ policy.is_active ? '활성' : '비활성' }}
                  </CBadge>
                </CTableDataCell>

                <!-- 관리 버튼 -->
                <CTableDataCell>
                  <template v-if="can(PERM.SALES_POLICY)">
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
                <CTableDataCell colspan="10" class="py-5 text-center text-muted">
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
  </ContentBody>
</template>
