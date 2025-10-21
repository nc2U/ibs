<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useContract } from '@/store/pinia/contract'
import { write_contract } from '@/utils/pageAuth'
import { TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import Contract from '@/views/contracts/List/components/Contract.vue'

const emit = defineEmits(['page-select', 'contract-converted'])

const props = defineProps({
  limit: { type: Number, default: 10 },
  unitSet: { type: Boolean, default: false },
  highlightId: { type: [Number, null] as PropType<number | null>, default: null },
  currentPage: { type: Number, default: 1 },
})

const contractStore = useContract()
const contractList = computed(() => contractStore.contractList)

const contractPages = (pageNum: number) => contractStore.contractPages(pageNum)
const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 7%" />
      <col style="width: 7%" />
      <col style="width: 8%" />
      <col style="width: 6%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 9%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 6%" />
      <col v-if="write_contract" style="width: 6%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell scope="col">일련번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">등록상태</CTableHeaderCell>
        <CTableHeaderCell scope="col">차수</CTableHeaderCell>
        <CTableHeaderCell scope="col">타입</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약자</CTableHeaderCell>
        <CTableHeaderCell scope="col">동호수</CTableHeaderCell>
        <CTableHeaderCell scope="col">가입 계약일</CTableHeaderCell>
        <CTableHeaderCell scope="col">공급 계약일</CTableHeaderCell>
        <CTableHeaderCell scope="col">공급계약가격</CTableHeaderCell>
        <CTableHeaderCell scope="col">납입금액합계</CTableHeaderCell>
        <CTableHeaderCell scope="col">최종납입회차</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약서</CTableHeaderCell>
        <CTableHeaderCell v-if="write_contract" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Contract
        v-for="contract in contractList"
        :key="contract.pk"
        :contract="contract"
        :unit-set="unitSet"
        :is-highlighted="props.highlightId === contract.pk"
        :current-page="props.currentPage"
        @contract-converted="$emit('contract-converted')"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage"
    :limit="8"
    :pages="contractPages(limit)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
