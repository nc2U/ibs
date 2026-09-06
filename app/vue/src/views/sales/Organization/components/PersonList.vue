<script lang="ts" setup>
import { ref, computed, type PropType } from 'vue'
import { useSales } from '@/store/pinia/sales'
import { usePerms } from '@/composables/usePerms'
import type { SalesPerson } from '@/store/types/sales'
import { TableSecondary } from '@/utils/cssMixins'

const props = defineProps({
  project: { type: Number, required: true },
  selectedTeamId: { type: Number as PropType<number | null>, default: null },
  selectedAgencyId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits(['add-person', 'edit-person', 'open-docs'])

const { can, PERM } = usePerms()
const salesStore = useSales()
const personList = computed(() => salesStore.personList)

// 필터 상태
const search = ref('')
const dutyFilter = ref<string>('')
const statusFilter = ref<string>('1') // 기본: 재직자 우선

const filteredPersons = computed(() => {
  return personList.value.filter(p => {
    // 팀 필터
    if (props.selectedTeamId && p.team !== props.selectedTeamId) return false
    // 대행사 필터
    if (props.selectedAgencyId) {
      const team = salesStore.teamList.find(t => t.id === p.team)
      if (team && team.agency !== props.selectedAgencyId) return false
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

const deletePerson = async (person: SalesPerson) => {
  if (confirm(`'${person.name}' 인력을 삭제하시겠습니까?`)) {
    await salesStore.deletePerson(person.id)
    if (props.project) {
      await salesStore.fetchPersonList(undefined, props.project)
      await salesStore.fetchTeamList(undefined, props.project)
    }
  }
}
</script>

<template>
  <CCard class="shadow-sm mb-4">
    <CCardHeader class="bg-light d-flex flex-wrap justify-content-between align-items-center py-2">
      <div class="fw-bold d-flex align-items-center mb-1 mb-md-0">
        <v-icon icon="mdi-account-multiple" size="small" class="mr-1 text-primary" />
        영업 인력 명단
        <CBadge color="primary" class="ml-2" shape="rounded-pill">
          {{ filteredPersons.length }}명
        </CBadge>
      </div>

      <div class="d-flex flex-wrap align-items-center gap-2">
        <!-- 직책 필터 -->
        <CFormSelect v-model="dutyFilter" size="sm" style="width: 120px">
          <option value="">전체 직책</option>
          <option value="1">분양상담사</option>
          <option value="2">팀장</option>
          <option value="3">본부장</option>
          <option value="4">총괄본부장</option>
          <option value="5">지원/기타</option>
        </CFormSelect>

        <!-- 상태 필터 -->
        <CFormSelect v-model="statusFilter" size="sm" style="width: 110px">
          <option value="">전체 상태</option>
          <option value="1">재직 (활동)</option>
          <option value="2">휴직</option>
          <option value="3">해촉 (퇴사)</option>
        </CFormSelect>

        <!-- 검색창 -->
        <CFormInput
          v-model="search"
          size="sm"
          placeholder="성명/연락처 검색"
          style="width: 150px"
        />

        <!-- 등록 버튼 -->
        <v-btn
          v-if="can(PERM.SALES_MANAGE)"
          color="primary"
          size="small"
          @click="emit('add-person')"
        >
          <v-icon icon="mdi-account-plus" size="small" class="mr-1" />
          신규 인력 등록
        </v-btn>
      </div>
    </CCardHeader>

    <CCardBody class="p-0">
      <CTable hover responsive bordered align="middle" class="mb-0 text-center text-body small">
        <colgroup>
          <col style="width: 10%" />
          <col style="width: 12%" />
          <col style="width: 9%" />
          <col style="width: 9%" />
          <col style="width: 11%" />
          <col style="width: 10%" />
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
              <CBadge :color="dutyBadgeColor[person.duty] || 'secondary'" shape="rounded-pill">
                {{ person.duty_display }}
              </CBadge>
            </CTableDataCell>
            <CTableDataCell>
              <a
                href="javascript:void(0);"
                class="fw-bold text-primary text-decoration-none"
                @click="emit('edit-person', person)"
              >
                {{ person.name }}
              </a>
            </CTableDataCell>
            <CTableDataCell>{{ person.phone }}</CTableDataCell>
            <CTableDataCell>
              <span class="badge bg-light text-dark border">
                {{ person.tax_type_display }}
              </span>
            </CTableDataCell>
            <CTableDataCell class="text-left font-monospace small">
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
                <v-icon icon="mdi-paperclip" size="x-small" class="mr-1" />
                서류 {{ person.documents_count ?? 0 }}건
              </v-btn>
            </CTableDataCell>
            <CTableDataCell>
              <CBadge :color="statusBadgeColor[person.status] || 'secondary'">
                {{ person.status_display }}
              </CBadge>
            </CTableDataCell>
            <CTableDataCell>
              <template v-if="can(PERM.SALES_MANAGE)">
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
</template>
