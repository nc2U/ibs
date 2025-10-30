<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useContract } from '@/store/pinia/contract.ts'
import type { ConsultationLog } from '@/store/types/contract'
import Pagination from '@/components/Pagination'
import ConsultationForm from './atoms/ConsultationForm.vue'
import ConsultationFilterChips from './atoms/ConsultationFilterChips.vue'
import ConsultationListItem from './atoms/ConsultationListItem.vue'

const route = useRoute()
const contStore = useContract()

// 계약자 ID
const contractorId = computed(() =>
  route.params.contractorId ? parseInt(route.params.contractorId as string, 10) : null,
)

// Store 데이터
const consultationLogList = computed(() => contStore.consultationLogList)

// 로딩 상태
const isLoading = ref(false)

// 필터 상태
const statusFilter = ref<string>('')

// 필터링된 리스트
const filteredList = computed(() => {
  if (!statusFilter.value) return consultationLogList.value
  return consultationLogList.value.filter(log => log.status === statusFilter.value)
})

// 폼 제출
const handleSubmit = async (data: Partial<ConsultationLog>) => {
  if (!contractorId.value) return

  try {
    await contStore.createConsultationLog({
      ...data,
      contractor: contractorId.value,
    })
  } catch (error) {
    console.error('상담 내역 등록 실패:', error)
  }
}

// 수정
const handleEdit = async (log: ConsultationLog) => {
  if (!log.pk) return

  try {
    await contStore.updateConsultationLog(log.pk, log)
  } catch (error) {
    console.error('수정 실패:', error)
  }
}

// 삭제
const handleDelete = async (pk: number) => {
  if (!contractorId.value) return
  if (!confirm('상담 내역을 삭제하시겠습니까?')) return

  try {
    await contStore.deleteConsultationLog(pk, contractorId.value)
  } catch (error) {
    console.error('삭제 실패:', error)
  }
}

// 페이지
const consultationLogPages = (pageNum: number) => contStore.consultationLogPages(pageNum)

// 페이지 변경
const onPageChange = (page: number) => {
  if (!contractorId.value) return
  loadData(page)
}

// 데이터 로드
const loadData = async (page = 1) => {
  if (!contractorId.value) return

  try {
    isLoading.value = true
    await contStore.fetchConsultationLogs(contractorId.value, {
      page,
      status: statusFilter.value || undefined,
    })
  } catch (error) {
    console.error('데이터 로드 실패:', error)
  } finally {
    isLoading.value = false
  }
}

// 상태 필터 변경 시 데이터 새로고침
watch(statusFilter, () => {
  if (contractorId.value) {
    loadData(1)
  }
})

// Watch: contractorId 변경 시 데이터 로드
watch(
  contractorId,
  newId => {
    if (newId) {
      loadData()
    } else contStore.consultationLogList = []
  },
  { immediate: true },
)

onMounted(() => {
  if (contractorId.value) {
    loadData()
  }
})
</script>

<template>
  <CCardBody>
    <!-- 인라인 등록 폼 -->
    <ConsultationForm @submit="handleSubmit" />

    <!-- 필터 영역 -->
    <ConsultationFilterChips v-model="statusFilter" />

    <!-- 로딩 상태 -->
    <div v-if="isLoading" class="text-center py-5">
      <v-progress-circular indeterminate color="primary" />
      <div class="mt-2">데이터 로딩 중...</div>
    </div>

    <!-- 계약자 미선택 -->
    <div v-else-if="!contractorId" class="text-center py-5 text-grey">계약자를 선택해주세요.</div>

    <!-- 상담 내역이 없음 -->
    <div v-else-if="filteredList.length === 0" class="text-center py-5 text-grey">
      <v-icon icon="mdi-message-text-outline" size="large" class="mb-2" />
      <div>상담 내역이 없습니다.</div>
    </div>

    <!-- 상담 내역 리스트 -->
    <CTable v-else hover responsive>
      <colgroup>
        <col width="20%" />
        <col width="10%" />
        <col width="10%" />
        <col width="32%" />
        <col width="10%" />
        <col width="18%" />
      </colgroup>
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell>상담일자</CTableHeaderCell>
          <CTableHeaderCell>채널</CTableHeaderCell>
          <CTableHeaderCell>유형</CTableHeaderCell>
          <CTableHeaderCell>제목</CTableHeaderCell>
          <CTableHeaderCell>처리상태</CTableHeaderCell>
          <CTableHeaderCell>작업</CTableHeaderCell>
        </CTableRow>
      </CTableHead>
      <CTableBody>
        <ConsultationListItem
          v-for="log in filteredList"
          :key="log.pk"
          :log="log"
          @edit="handleEdit"
          @delete="handleDelete"
        />
      </CTableBody>
    </CTable>

    <!-- 페이지네이션 -->
    <CCol class="d-flex justify-content-center mt-0">
      <Pagination
        v-show="filteredList.length"
        :active-page="1"
        :limit="8"
        :pages="consultationLogPages(10)"
        class="mt-3"
        @active-page-change="onPageChange"
      />
    </CCol>
  </CCardBody>
</template>
