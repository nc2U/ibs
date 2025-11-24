<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useProCash } from '@/store/pinia/proCash'
import { numFormat } from '@/utils/baseMixins'
import { TableSecondary } from '@/utils/cssMixins'
import {
  type ProBankAcc,
  type ProjectAccountD2,
  type ProjectAccountD3,
  type ProjectCashBook,
} from '@/store/types/proCash'

defineProps({ date: { type: String, default: '' } })

const dateIncSet = ref<ProjectCashBook[]>([])
const dateOutSet = ref<ProjectCashBook[]>([])
const dateIncTotal = ref<number>(0)
const dateOutTotal = ref<number>(0)

const proCashStore = useProCash()
const allAccD2List = computed(() => proCashStore.allAccD2List)
const allAccD3List = computed(() => proCashStore.allAccD3List)
const proBankAccountList = computed(() => proCashStore.proBankAccountList)
const proDateCashBook = computed(() => proCashStore.proDateCashBook)

watch(proDateCashBook, () => setData())

onBeforeMount(() => setData())

const getD1Text = (num: number) =>
  allAccD2List.value
    .filter((d: ProjectAccountD2) => d.pk === num)
    .map((d: ProjectAccountD2) => d.name)[0]

const getD3Text = (num: number) =>
  allAccD3List.value
    .filter((d: ProjectAccountD3) => d.pk === num)
    .map((d: ProjectAccountD3) => d.name)[0]

const getBankAcc = (num: number) =>
  proBankAccountList.value
    .filter((b: ProBankAcc) => b.pk === num)
    .map((b: ProBankAcc) => b.alias_name)[0]

const setData = () => {
  dateIncSet.value = proDateCashBook.value.filter(
    (i: ProjectCashBook) => i.income && i.income > 0 && !i.outlay,
  )
  dateOutSet.value = proDateCashBook.value.filter(
    (o: ProjectCashBook) => o.outlay && o.outlay > 0 && !o.income,
  )
  dateIncTotal.value = dateIncSet.value
    .map((i: ProjectCashBook) => i.income || 0)
    .reduce((x: number, y: number) => x + y, 0)
  dateOutTotal.value = dateOutSet.value
    .map((o: ProjectCashBook) => o.outlay || 0)
    .reduce((x: number, y: number) => x + y, 0)
}
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 25%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="5">
          <strong>
            <CIcon name="cilFolderOpen" />
            프로젝트 당일 입금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>항목</CTableHeaderCell>
        <CTableHeaderCell>세부 항목</CTableHeaderCell>
        <CTableHeaderCell>입금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="inc in dateIncSet" :key="inc.pk" class="text-center">
        <CTableDataCell>{{ getD1Text(inc.project_account_d2 as number) }}</CTableDataCell>
        <CTableDataCell>{{ getD3Text(inc.project_account_d3 as number) }}</CTableDataCell>
        <CTableDataCell class="text-right" color="success">
          {{ numFormat(inc.income || 0) }}
        </CTableDataCell>
        <CTableDataCell>{{ getBankAcc(inc.bank_account as number) }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.trader }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ inc.content }}</CTableDataCell>
      </CTableRow>

      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="success"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="2" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateIncTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>

  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 15%" />
      <col style="width: 25%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="5">
          <strong>
            <CIcon name="cilFolderOpen" />
            프로젝트 당일 출금내역
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>항목</CTableHeaderCell>
        <CTableHeaderCell>세부 항목</CTableHeaderCell>
        <CTableHeaderCell>출금 금액</CTableHeaderCell>
        <CTableHeaderCell>거래 계좌</CTableHeaderCell>
        <CTableHeaderCell>거래처</CTableHeaderCell>
        <CTableHeaderCell>적요</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="out in dateOutSet" :key="out.pk" class="text-center">
        <CTableDataCell>
          {{ getD1Text(out.project_account_d2 as number) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ getD3Text(out.project_account_d3 as number) }}
        </CTableDataCell>
        <CTableDataCell class="text-right" color="danger">
          {{ numFormat(out.outlay || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ getBankAcc(out.bank_account as number) }}
        </CTableDataCell>
        <CTableDataCell class="text-left">{{ out.trader }}</CTableDataCell>
        <CTableDataCell class="text-left">{{ out.content }}</CTableDataCell>
      </CTableRow>
      <CTableRow class="text-center">
        <CTableDataCell>&nbsp;</CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell color="danger"></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
        <CTableDataCell></CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="2" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(dateOutTotal) }}</CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
