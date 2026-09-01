<script lang="ts" setup>
import { computed } from 'vue'
import { usePerms } from '@/composables/usePerms.ts'
import { useCompany } from '@/store/pinia/company.ts'
import { TableSecondary } from '@/utils/cssMixins.ts'
import { type PromotionPolicy as PromotionPolicyType } from '@/store/types/company.ts'
import Pagination from '@/components/Pagination'
import Policy from './Policy.vue'

const emit = defineEmits(['page-select', 'multi-submit', 'on-delete'])

const { canGlobal, PERM } = usePerms()
const canHrWorkManage = computed(
  () => canGlobal(PERM.HQ_HR_WORK_CREATE) || canGlobal(PERM.HQ_HR_WORK_UPDATE),
)

const companyStore = useCompany()
const promotionPolicyList = computed(() => companyStore.promotionPolicyList)
const promotionPoliciesCount = computed(() => companyStore.promotionPoliciesCount)

const promotionPolicyPages = (page: number) => companyStore.promotionPolicyPages(page)
const pageSelect = (page: number) => emit('page-select', page)
const multiSubmit = (payload: PromotionPolicyType) => emit('multi-submit', payload)
const onDelete = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 14%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 12%" />
      <col style="width: 18%" />
      <col style="width: 15%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
      <col v-if="canHrWorkManage" style="width: 5%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center" align="middle">
        <CTableHeaderCell scope="col">승급 경로</CTableHeaderCell>
        <CTableHeaderCell scope="col">최소 체류</CTableHeaderCell>
        <CTableHeaderCell scope="col">최소 평점</CTableHeaderCell>
        <CTableHeaderCell scope="col">최소 평가등급</CTableHeaderCell>
        <CTableHeaderCell scope="col">필수 역량/자격 요건</CTableHeaderCell>
        <CTableHeaderCell scope="col">승급 결격 사유</CTableHeaderCell>
        <CTableHeaderCell scope="col">세부 설명</CTableHeaderCell>
        <CTableHeaderCell scope="col">상태</CTableHeaderCell>
        <CTableHeaderCell v-if="canHrWorkManage" scope="col">관리</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Policy
        v-for="policy in promotionPolicyList"
        :key="policy.pk"
        :policy="policy"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
      />
      <CTableRow v-if="promotionPolicyList.length === 0">
        <CTableDataCell :colspan="canHrWorkManage ? 9 : 8" class="text-center text-muted py-4">
          조회된 직급별 승급 정책이 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    v-if="promotionPoliciesCount > 10"
    :active-page="1"
    :limit="8"
    :pages="promotionPolicyPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
