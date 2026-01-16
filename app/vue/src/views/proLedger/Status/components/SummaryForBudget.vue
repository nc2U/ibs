<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useProject } from '@/store/pinia/project'
import { write_project_cash } from '@/utils/pageAuth'
import { numFormat } from '@/utils/baseMixins'
import { TableInfo, TableSecondary } from '@/utils/cssMixins'
import type { StatusOutBudget, ExecAmountToBudget as ExeBudget } from '@/store/types/project'

defineProps({ date: { type: String, default: '' } })

const emit = defineEmits(['patch-budget', 'update-revised'])

const formNumber = ref(1000)
const isRevised = ref('1')

const projStore = useProject()
const execAmountList = computed(() => projStore.execAmountList)
const statusOutBudgetList = computed(() => projStore.statusOutBudgetList)

const getD3sInter = (arr: number[]) => {
  const d3s = statusOutBudgetList.value.map((b: StatusOutBudget) => b.account_d3?.pk)
  return arr.filter(x => d3s.includes(x))
}
const getLength = (arr: number[]) => getD3sInter(arr).length

const isFirst = (arr: number[], d3Pk: number) => getD3sInter(arr)[0] === d3Pk

const getSubTitle = (sub: string, d2: number) =>
  sub !== ''
    ? statusOutBudgetList.value
        .filter((b: StatusOutBudget) => b.account_opt === sub && b.account_d2?.pk === d2)
        .map(b => b.pk)
    : []

const getExecAmount = (d3: number) => execAmountList.value.filter((e: ExeBudget) => e.acc_d3 === d3)

const getEASum = (d3: number) => getExecAmount(d3).map((e: ExeBudget) => e.all_sum)[0]

const getEAMonth = (d3: number) => getExecAmount(d3).map((e: ExeBudget) => e.month_sum)[0]

const sumTotal = computed(() => {
  const totalBudgetCalc = statusOutBudgetList.value
    .map((b: StatusOutBudget) => b.budget)
    .reduce((res: number, val: number) => res + val, 0)
  const totalRevisedBudgetCalc = statusOutBudgetList.value
    .map((b: StatusOutBudget) => b.revised_budget || b.budget)
    .reduce((res: number, val: number) => res + val, 0)
  const monthExecAmtCalc = execAmountList.value
    .map((a: ExeBudget) => a.month_sum)
    .reduce((r: number, v: number) => r + v, 0)
  const totalExecAmtCalc = execAmountList.value
    .map((a: ExeBudget) => a.all_sum)
    .reduce((r: number, v: number) => r + v, 0)

  const preExecAmt = totalExecAmtCalc - monthExecAmtCalc
  const monthExecAmt = monthExecAmtCalc
  const totalExecAmt = totalExecAmtCalc
  const availableBudget = totalBudgetCalc - totalExecAmtCalc
  const availableRevisedBudget = totalRevisedBudgetCalc - totalExecAmtCalc
  return {
    totalBudgetCalc,
    totalRevisedBudgetCalc,
    preExecAmt,
    monthExecAmt,
    totalExecAmt,
    availableBudget,
    availableRevisedBudget,
  }
})

const patchBudget = (pk: number, budget: string, oldBudget: number, isRevised = false) => {
  formNumber.value = 1000
  if (write_project_cash.value) {
    const bg = parseInt(budget)
    if (bg !== oldBudget) emit('patch-budget', pk, bg, isRevised)
  } else {
    alert('예산 수정 권한 없음!')
  }
}

const updateRevised = ($event: any) => emit('update-revised', $event.target.value)
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 5%" />
      <col style="width: 5%" />
      <col style="width: 10%" />
      <col style="width: 10%" />
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 14%" />
      <col style="width: 14%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="4">
          <strong>
            <CIcon name="cilFolderOpen" />
            사업예산 및 집행현황
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 기준 </small>
        </CTableDataCell>
        <CTableDataCell class="text-center">
          <v-btn-group
            density="compact"
            role="group"
            aria-label="Basic checkbox toggle button group"
          >
            <CFormCheck
              type="radio"
              :button="{ color: 'dark', variant: 'outline' }"
              name="budget_select"
              id="budget0"
              autocomplete="off"
              label="기초 예산"
              value="0"
              v-model="isRevised"
              @click="updateRevised"
            />
            <CFormCheck
              type="radio"
              :button="{ color: 'dark', variant: 'outline' }"
              name="budget_select"
              id="budget1"
              autocomplete="off"
              label="현황 예산"
              value="1"
              v-model="isRevised"
              @click="updateRevised"
            />
          </v-btn-group>
        </CTableDataCell>
        <CTableDataCell colspan="4" class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>
      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell colspan="4">구분</CTableHeaderCell>
        <CTableHeaderCell color="light" v-show="isRevised === '0'">기초 예산 금액</CTableHeaderCell>
        <CTableHeaderCell color="light" v-show="isRevised === '1'">현황 예산 금액</CTableHeaderCell>
        <CTableHeaderCell>전월 집행 금액 누계</CTableHeaderCell>
        <CTableHeaderCell>당월 집행 금액</CTableHeaderCell>
        <CTableHeaderCell>집행금액 합계</CTableHeaderCell>
        <CTableHeaderCell>가용(잔여) 예산 합계</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody>
      <CTableRow v-for="(obj, i) in statusOutBudgetList" :key="obj.pk" class="text-right">
        <CTableDataCell
          v-if="i === 0"
          :color="TableInfo"
          class="text-center"
          :rowspan="statusOutBudgetList.length"
        >
          사업비
        </CTableDataCell>
        <CTableDataCell
          v-if="isFirst(obj.account_d2?.pro_d3s || [], obj.account_d3?.pk || 0)"
          class="text-center"
          :rowspan="getLength(obj.account_d2?.pro_d3s || [])"
        >
          {{ obj.account_d2?.name }}
        </CTableDataCell>
        <CTableDataCell
          v-if="
            obj.account_opt && obj.pk === getSubTitle(obj.account_opt, obj.account_d2?.pk || 0)[0]
          "
          class="text-left"
          :rowspan="getSubTitle(obj.account_opt, obj.account_d2?.pk || 0).length"
        >
          {{ obj.account_opt }}
        </CTableDataCell>
        <CTableDataCell class="text-left" :colspan="obj.account_opt ? 1 : 2">
          {{ obj.account_d3?.name }}
          <v-tooltip v-if="obj.basis_calc" activator="parent" location="left">
            {{ obj.basis_calc }}
          </v-tooltip>
        </CTableDataCell>
        <CTableDataCell v-show="isRevised === '0'" class="py-0 bg-indigo-lighten-5">
          <span>{{ numFormat(obj.budget) }}</span>
        </CTableDataCell>
        <CTableDataCell
          v-show="isRevised === '1'"
          class="py-0 bg-amber-lighten-5"
          style="cursor: pointer"
          @dblclick="formNumber = i"
        >
          <span v-if="formNumber !== i">
            {{ numFormat(obj.revised_budget || obj.budget) }}
          </span>
          <span v-else class="p-0">
            <CFormInput
              type="text"
              class="form-control text-right"
              :value="obj.revised_budget || obj.budget"
              @blur="
                patchBudget(obj.pk as number, $event.target.value, obj.revised_budget ?? 0, true)
              "
              @keydown.enter="
                patchBudget(obj.pk as number, $event.target.value, obj.revised_budget ?? 0, true)
              "
            />
          </span>
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(getEASum(obj.account_d3?.pk || 0) - getEAMonth(obj.account_d3?.pk || 0)) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(getEAMonth(obj.account_d3?.pk || 0) || 0) }}
        </CTableDataCell>
        <CTableDataCell>
          {{ numFormat(getEASum(obj.account_d3?.pk || 0) || 0) }}
        </CTableDataCell>
        <CTableDataCell
          v-show="isRevised === '0'"
          :class="obj.budget < getEASum(obj.account_d3?.pk || 0) ? 'text-danger' : ''"
        >
          {{ numFormat(obj.budget - (getEASum(obj.account_d3?.pk || 0) || 0)) }}
        </CTableDataCell>
        <CTableDataCell
          v-show="isRevised === '1'"
          :class="
            (obj.revised_budget || obj.budget) < getEASum(obj.account_d3?.pk || 0)
              ? 'text-danger'
              : ''
          "
        >
          {{
            numFormat((obj.revised_budget || obj.budget) - (getEASum(obj.account_d3?.pk || 0) || 0))
          }}
        </CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-right">
        <CTableHeaderCell colspan="4" class="text-center"> 합계</CTableHeaderCell>
        <CTableHeaderCell v-show="isRevised === '0'">
          {{ numFormat(sumTotal.totalBudgetCalc) }}
        </CTableHeaderCell>
        <CTableHeaderCell v-show="isRevised === '1'">
          {{ numFormat(sumTotal.totalRevisedBudgetCalc) }}
        </CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(sumTotal.preExecAmt) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(sumTotal.monthExecAmt) }}</CTableHeaderCell>
        <CTableHeaderCell>{{ numFormat(sumTotal.totalExecAmt) }}</CTableHeaderCell>
        <CTableHeaderCell v-show="isRevised === '0'">
          {{ numFormat(sumTotal.availableBudget) }}
        </CTableHeaderCell>
        <CTableHeaderCell v-show="isRevised === '1'">
          {{ numFormat(sumTotal.availableRevisedBudget) }}
        </CTableHeaderCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
