<script lang="ts" setup>
import { ref, computed } from 'vue'
import { TableSecondary } from '@/utils/cssMixins'
import { useContract } from '@/store/pinia/contract'
import { usePerms } from '@/composables/usePerms.ts'
import Contract from '@/views/notices/Bill/components/Contract.vue'
import Pagination from '@/components/Pagination'

defineProps({
  nowOrder: { type: Number, default: null },
  limit: { type: Number, default: 10 },
})

const emit = defineEmits(['page-select', 'on-cont-chk', 'all-un-checked'])

const { can, PERM } = usePerms()
const canNoticeRead = computed(() => can(PERM.NOTICE_READ))

const page = ref(1)
const allChecked = ref(false)

const contractStore = useContract()
const contractList = computed(() => contractStore.contractList)
const contractPages = computed(() => contractStore.contractPages)

const pageSelect = (page: number) => {
  allChecked.value = false
  emit('page-select', page)
}

const allUnChecked = () => {
  allChecked.value = !allChecked.value
  if (!allChecked.value) emit('all-un-checked')
}

const onContChk = (payload: { chk: boolean; pk: number }) => emit('on-cont-chk', payload)
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col v-if="canNoticeRead" style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 11%" />
      <col style="width: 8%" />
      <col style="width: 12%" />
      <col style="width: 20%" />
      <col style="width: 12%" />
    </colgroup>

    <CTableHead :color="TableSecondary">
      <CTableRow class="text-center">
        <CTableHeaderCell v-if="canNoticeRead" scope="col">
          <CFormCheck id="checkAll" v-model="allChecked" label="전체" @change="allUnChecked" />
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">차수</CTableHeaderCell>
        <CTableHeaderCell scope="col">타입</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약 일련번호</CTableHeaderCell>
        <CTableHeaderCell scope="col">동호수</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약자</CTableHeaderCell>
        <CTableHeaderCell scope="col">납입금액합계</CTableHeaderCell>
        <CTableHeaderCell scope="col">납입상태 (완납회차)</CTableHeaderCell>
        <CTableHeaderCell scope="col">계약일자</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <Contract
        v-for="contract in contractList"
        :key="contract.pk"
        :page="page"
        :now-order="nowOrder"
        :all-checked="allChecked"
        :contract="contract"
        @on-cont-chk="onContChk"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="1"
    :limit="8"
    :pages="contractPages(limit)"
    class="mt-3"
    @on-ctor-pk="onContChk"
    @active-page-change="pageSelect"
  />
</template>
