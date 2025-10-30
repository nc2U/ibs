<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useContract } from '@/store/pinia/contract'
import { bgLight, TableSecondary } from '@/utils/cssMixins'
import Pagination from '@/components/Pagination'
import Succession from '@/views/contracts/Succession/components/Succession.vue'

const emit = defineEmits(['page-select', 'call-form', 'done-alert'])

const props = defineProps({
  highlightId: { type: [Number, null] as PropType<number | null>, default: null },
  currentPage: { type: Number, default: 1 },
})

const contractStore = useContract()
const successionList = computed(() => contractStore.successionList)
const successionPages = computed(() => contractStore.successionPages)

const pageSelect = (page: number) => emit('page-select', page)
const callForm = () => emit('call-form')
const doneAlert = () => emit('done-alert')
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
    </colgroup>

    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>계약 정보</CTableHeaderCell>
        <CTableHeaderCell>양도계약자</CTableHeaderCell>
        <CTableHeaderCell>양수계약자</CTableHeaderCell>
        <CTableHeaderCell>승계신청일</CTableHeaderCell>
        <CTableHeaderCell>매매계약일</CTableHeaderCell>
        <CTableHeaderCell>변경인가일</CTableHeaderCell>
        <CTableHeaderCell>변경인가여부</CTableHeaderCell>
        <CTableHeaderCell>확인</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody>
      <CTableRow
        v-for="suc in successionList"
        :key="suc.pk"
        :class="suc.is_approval ? bgLight : ''"
        :color="props.highlightId === suc.pk ? 'warning' : ''"
        :data-succession-id="suc.pk"
      >
        <Succession
          :succession="suc"
          :is-highlighted="props.highlightId === suc.pk"
          @call-form="callForm"
          @done-alert="doneAlert"
        />
      </CTableRow>
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="props.currentPage"
    :limit="8"
    :pages="successionPages(10)"
    class="mt-3"
    @active-page-change="pageSelect"
  />
</template>
