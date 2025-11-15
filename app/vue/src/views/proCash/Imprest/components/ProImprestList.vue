<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useProCash } from '@/store/pinia/proCash'
import { type ProBankAcc, type ProjectCashBook } from '@/store/types/proCash'
import { TableSecondary } from '@/utils/cssMixins'
import { write_project_cash } from '@/utils/pageAuth'
import ProImprest from '@/views/proCash/Imprest/components/ProImprest.vue'
import Pagination from '@/components/Pagination'
import AccDepth from '../../Manage/components/AccDepth.vue'
import BankAcc from '../../Manage/components/BankAcc.vue'

const props = defineProps({ project: Number, default: () => null })
const emit = defineEmits([
  'page-select',
  'multi-submit',
  'on-delete',
  'on-bank-create',
  'on-bank-update',
])

const refAccDepth = ref()
const refBankAcc = ref()

const proCashStore = useProCash()
const proImprestList = computed(() => proCashStore.proImprestList)
const proImprestPages = computed(() => proCashStore.proImprestPages)
const proCalculated = computed(() => proCashStore.proCalculated) // 최종 정산 일자

const pageSelect = (page: number) => emit('page-select', page)

const multiSubmit = (payload: { formData: ProjectCashBook; sepData: ProjectCashBook | null }) =>
  emit('multi-submit', payload)

const onDelete = (payload: { project: number; pk: number }) => emit('on-delete', payload)

const onBankCreate = (payload: ProBankAcc) => emit('on-bank-create', payload)
const onBankUpdate = (payload: ProBankAcc) => emit('on-bank-update', payload)
const accCallModal = () => {
  if (props.project) refBankAcc.value.callModal()
}
</script>

<template>
  <CTable hover responsive align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 6%" />
      <col style="width: 11%" />
      <col style="width: 11%" />
      <col style="width: 12%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 7%" />
      <col style="width: 10%" />
      <col style="width: 9%" />
      <col v-if="write_project_cash" style="width: 6%" />
    </colgroup>

    <CTableHead>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell scope="col">거래일자</CTableHeaderCell>
        <CTableHeaderCell scope="col">구분</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          거래계좌
          <a href="javascript:void(0)">
            <CIcon name="cilCog" @click="accCallModal" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">거래처</CTableHeaderCell>
        <CTableHeaderCell scope="col">적요</CTableHeaderCell>
        <CTableHeaderCell scope="col">입금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">출금액</CTableHeaderCell>
        <CTableHeaderCell scope="col">계정</CTableHeaderCell>
        <CTableHeaderCell scope="col">
          세부계정
          <a href="javascript:void(0)">
            <CIcon name="cilCog" @click="refAccDepth.callModal()" />
          </a>
        </CTableHeaderCell>
        <CTableHeaderCell scope="col">지출증빙</CTableHeaderCell>
        <CTableHeaderCell v-if="write_project_cash" scope="col">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <ProImprest
        v-for="imprest in proImprestList"
        :key="imprest.pk as number"
        :imprest="imprest"
        :calculated="proCalculated?.calculated"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @on-bank-update="onBankUpdate"
      />
    </CTableBody>
  </CTable>

  <Pagination
    :active-page="1"
    :limit="8"
    :pages="proImprestPages(15)"
    class="mt-3"
    @active-page-change="pageSelect"
  />

  <AccDepth ref="refAccDepth" />

  <BankAcc ref="refBankAcc" @on-bank-create="onBankCreate" @on-bank-update="onBankUpdate" />
</template>
