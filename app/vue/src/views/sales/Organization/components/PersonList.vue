<script lang="ts" setup>
import { computed, ref, watch, type PropType } from 'vue'
import { useSales } from '@/store/pinia/sales'
import { usePerms } from '@/composables/usePerms'
import type { SalesPerson } from '@/store/types/sales'
import { bgLight, TableSecondary } from '@/utils/cssMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  project: { type: Number, required: true },
  selectedTeamId: { type: Number as PropType<number | null>, default: null },
  selectedAgencyId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits<{
  (e: 'add-person'): void
  (e: 'edit-person', person: SalesPerson): void
  (e: 'open-docs', person: SalesPerson): void
}>()

const { can, PERM } = usePerms()
const canSalesManage = computed(() => can(PERM.SALES_MANAGE, props.project))
const salesStore = useSales()
const personList = computed(() => salesStore.personList)

// 필터 상태
const search = ref('')
const dutyFilter = ref<string>('')
const statusFilter = ref<string>('1') // 기본: 재직자 우선

watch(
  () => props.project,
  () => {
    search.value = ''
    dutyFilter.value = ''
    statusFilter.value = '1'
  },
)

const filteredPersons = computed(() => {
  return personList.value.filter(p => {
    // 팀 필터
    if (props.selectedTeamId && p.team !== props.selectedTeamId) return false
    // 대행사 필터
    if (props.selectedAgencyId) {
      const team = salesStore.teamList.find(t => t.id === p.team)
      if (!team || team.agency !== props.selectedAgencyId) return false
    }
    // 직책 필터
    if (dutyFilter.value && p.duty !== dutyFilter.value) return false
    // 상태 필터
    if (statusFilter.value && p.status !== statusFilter.value) return false
    // 검색어 필터 (성명, 전화번호, 예금주)
    if (search.value.trim()) {
      const q = search.value.trim().toLowerCase()
      const matchName = p.name.toLowerCase().includes(q)
      const matchPhone = p.phone.includes(q)
      const matchHolder = p.account_holder?.toLowerCase().includes(q)
      if (!matchName && !matchPhone && !matchHolder) return false
    }
    return true
  })
})

const dutyBadgeColor: Record<string, string> = {
  '1': 'primary',
  '2': 'success',
  '3': 'warning',
  '4': 'dark',
  '5': 'secondary',
}

const statusBadgeColor: Record<string, string> = {
  '1': 'success',
  '2': 'warning',
  '3': 'secondary',
}

const confirmModalRef = ref()
const pendingDelete = ref<SalesPerson | null>(null)

const deletePerson = (person: SalesPerson) => {
  if (!canSalesManage.value) return
  pendingDelete.value = person
  confirmModalRef.value?.callModal()
}

const executeDelete = async () => {
  if (!pendingDelete.value) return
  confirmModalRef.value?.close()
  const ok = await salesStore.deletePerson(pendingDelete.value.id)
  if (ok && props.project) {
    await Promise.all([
      salesStore.fetchPersonList(undefined, props.project),
      salesStore.fetchTeamList(undefined, props.project),
    ])
  }
  pendingDelete.value = null
}
</script>

<template>
  <CCard class="shadow-sm mb-4">
    <CCardHeader
      :class="bgLight"
      class="d-flex flex-wrap justify-content-between align-items-center py-2"
    >
      <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
        <v-icon icon="mdi-account-multiple" size="small" class="me-1 text-primary" />
        영업 인력 명단
        <v-chip color="info" class="ms-2" shape="rounded-pill" variant="flat" size="x-small">
          {{ filteredPersons.length }}명
        </v-chip>
      </div>

      <div class="d-flex flex-wrap align-items-center gap-2">
        <!-- 직책 필터 -->
        <CFormSelect v-model="dutyFilter" style="width: 150px">
          <option value="">전체 직책</option>
          <option value="1">분양상담사</option>
          <option value="2">팀장</option>
          <option value="3">본부장</option>
          <option value="4">총괄본부장</option>
          <option value="5">지원/기타</option>
        </CFormSelect>

        <!-- 상태 필터 -->
        <CFormSelect v-model="statusFilter" style="width: 150px">
          <option value="">전체 상태</option>
          <option value="1">재직 (활동)</option>
          <option value="2">휴직</option>
          <option value="3">해촉 (퇴사)</option>
        </CFormSelect>

        <!-- 검색창 -->
        <CFormInput v-model="search" placeholder="성명/연락처 검색" style="width: 150px" />

        <!-- 등록 버튼 -->
        <v-btn
          v-if="canSalesManage"
          color="primary"
          size="small"
          @click="emit('add-person')"
        >
          <v-icon icon="mdi-account-plus" size="small" class="me-1" />
          신규 인력 등록
        </v-btn>
      </div>
    </CCardHeader>

    <CCardBody class="p-0">
      <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body">
        <colgroup>
          <col style="width: 10%" />
          <col style="width: 11%" />
          <col style="width: 9%" />
          <col style="width: 9%" />
          <col style="width: 11%" />
          <col style="width: 11%" />
          <col style="width: 15%" />
          <col style="width: 10%" />
          <col style="width: 7%" />
          <col style="width: 7%" />
        </colgroup>
        <CTableHead :color="TableSecondary">
          <CTableRow>
            <CTableHeaderCell>대행사</CTableHeaderCell>
            <CTableHeaderCell>소속 조직/팀</CTableHeaderCell>
            <CTableHeaderCell>직책</CTableHeaderCell>
            <CTableHeaderCell>성명</CTableHeaderCell>
            <CTableHeaderCell>연락처</CTableHeaderCell>
            <CTableHeaderCell>소득구분</CTableHeaderCell>
            <CTableHeaderCell>정산 계좌 정보</CTableHeaderCell>
            <CTableHeaderCell>제출 서류</CTableHeaderCell>
            <CTableHeaderCell>상태</CTableHeaderCell>
            <CTableHeaderCell>관리</CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="person in filteredPersons" :key="person.id">
            <CTableDataCell>
              <span class="text-secondary">{{ person.agency_name || '-' }}</span>
            </CTableDataCell>
            <CTableDataCell class="fw-bold">
              {{ person.team_name || '-' }}
            </CTableDataCell>
            <CTableDataCell>
              <v-chip
                :color="dutyBadgeColor[person.duty] || 'secondary'"
                shape="rounded-pill"
                variant="flat"
                size="x-small"
              >
                {{ person.duty_display }}
              </v-chip>
            </CTableDataCell>
            <CTableDataCell>
              <a
                v-if="canSalesManage"
                href="#"
                class="fw-bold text-primary text-decoration-none"
                @click.prevent="emit('edit-person', person)"
              >
                {{ person.name }}
              </a>
              <span v-else class="fw-bold">{{ person.name }}</span>
            </CTableDataCell>
            <CTableDataCell>{{ person.phone }}</CTableDataCell>
            <CTableDataCell>
              <span class="badge bg-more-light text-body border">
                {{ person.tax_type_display }}
              </span>
            </CTableDataCell>
            <CTableDataCell class="text-start font-monospace">
              <span v-if="person.bank_name || person.account_number">
                <strong>{{ person.bank_name }}</strong> {{ person.account_number }}
                <span class="text-muted">({{ person.account_holder }})</span>
              </span>
              <span v-else class="text-muted">미등록</span>
            </CTableDataCell>
            <CTableDataCell>
              <v-btn
                size="x-small"
                :color="(person.documents_count ?? 0) > 0 ? 'primary' : 'secondary'"
                variant="tonal"
                class="text-nowrap"
                title="제출 서류 관리"
                @click="emit('open-docs', person)"
              >
                <v-icon icon="mdi-paperclip" size="small" class="me-1" />
                서류 {{ person.documents_count ?? 0 }}건
              </v-btn>
            </CTableDataCell>
            <CTableDataCell>
              <v-chip
                :color="statusBadgeColor[person.status] || 'secondary'"
                variant="flat"
                size="x-small"
              >
                {{ person.status_display }}
              </v-chip>
            </CTableDataCell>
            <CTableDataCell>
              <template v-if="canSalesManage">
                <v-btn
                  icon="mdi-pencil"
                  size="x-small"
                  variant="text"
                  color="success"
                  title="수정"
                  @click="emit('edit-person', person)"
                />
                <v-btn
                  icon="mdi-delete"
                  size="x-small"
                  variant="text"
                  color="danger"
                  title="삭제"
                  @click="deletePerson(person)"
                />
              </template>
              <span v-else class="text-muted">-</span>
            </CTableDataCell>
          </CTableRow>

          <CTableRow v-if="filteredPersons.length === 0">
            <CTableDataCell colspan="10" class="py-5 text-center text-muted">
              등록된 영업 인력이 없거나 검색 조건에 일치하는 결과가 없습니다.
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCardBody>
  </CCard>

  <ConfirmModal ref="confirmModalRef">
    <template #header>삭제 확인</template>
    <template #default>
      <p class="mb-0">
        <strong>[{{ pendingDelete?.name }}]</strong> 인력을 삭제하시겠습니까?
      </p>
      <small class="text-danger"
        >(계약 실적 또는 정산·지급·환수 내역이 연결된 경우 삭제할 수 없습니다)</small
      >
    </template>
    <template #footer>
      <v-btn size="small" color="danger" @click="executeDelete">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
