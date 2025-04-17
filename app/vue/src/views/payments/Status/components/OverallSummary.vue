<script lang="ts" setup>
import { computed } from 'vue'
import { useProject } from '@/store/pinia/project'
import { useContract } from '@/store/pinia/contract'
import { useProjectData } from '@/store/pinia/project_data'
import { usePayment } from '@/store/pinia/payment'
import { TableSecondary } from '@/utils/cssMixins'
import { numFormat } from '@/utils/baseMixins'

defineProps({
  date: { type: String, default: '' },
})

const proStore = useProject()
const budgetList = computed(() => proStore.proIncBudgetList)

const contStore = useContract()
const orderGroup = computed(() => contStore.orderGroupList)
const contSum = computed(() => contStore.contSummaryList)

const prDataStore = useProjectData()
const unitType = computed(() => prDataStore.unitTypeList)

const paymentStore = usePayment()
const paySumList = computed(() => paymentStore.paySumList)

// 차수명
const getOGName = (og: number) =>
  orderGroup.value.length ? orderGroup.value.filter(o => o.pk === og)[0] : { order_group_name: '' }
// 타입명
const getUTName = (ut: number) =>
  unitType.value.length ? unitType.value.filter(u => u.pk === ut)[0] : { name: '', color: '' }
// 차수 및 타입별 계약 건수
const getContNum = (og: number, ut: number) =>
  contSum.value.filter(c => c.order_group === og && c.unit_type === ut).map(c => c.conts_num)[0]
// 차수 및 타입별 계약 가격 총액
const getContSum = (og: number, ut: number) =>
  contSum.value.filter(c => c.order_group === og && c.unit_type === ut).map(c => c.price_sum)[0]
// 차수별 타입수
const getUTbyOGNum = (og: number) => budgetList.value.filter(b => b.order_group === og).length
// 차수별 첫번째 타입
const getFirstType = (og: number) => budgetList.value.filter(b => b.order_group === og)[0].unit_type

const paidSum = (og: number, ut: number) =>
  paySumList.value.filter(s => s.order_group === og && s.unit_type === ut)[0]

const totalBudgetNum = computed(
  () => budgetList.value.map(b => b.quantity).reduce((p, n) => p + n, 0), // 총 계획 세대수
)
const totalContNum = computed(() =>
  budgetList.value.length ? contSum.value.map(c => c.conts_num).reduce((x, y) => x + y, 0) : 0,
) // 총 계약 세대수

const totalContSum = computed(() =>
  contSum.value.map(c => c.price_sum || 0).reduce((x, y) => x + y, 0),
) // 총 계약금액

const totalPaidSum = computed(() =>
  budgetList.value.length ? paySumList.value.map(s => s.paid_sum).reduce((x, y) => x + y, 0) : 0,
) // 총 실수납 금액

const totalBudget = computed(
  () => budgetList.value.map(b => b.budget).reduce((x, y) => x + y, 0), // 총 예산합계
) // 총 예산 합계
</script>

<template>
  <CTable hover responsive bordered align="middle">
    <colgroup>
      <col style="width: 8%" />
      <col style="width: 8%" />
      <col style="width: 10%" />
      <col style="width: 7%" />
      <col style="width: 7%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
      <col style="width: 12%" />
    </colgroup>
    <CTableHead>
      <CTableRow>
        <CTableDataCell colspan="9">
          <strong>
            <CIcon name="cilFolderOpen" />
            차수 및 타입별 수납 현황
          </strong>
          <small class="text-medium-emphasis"> ({{ date }}) 현재 </small>
        </CTableDataCell>
        <CTableDataCell class="text-right">(단위: 원)</CTableDataCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-center" align="middle">
        <CTableHeaderCell rowspan="2">차수</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">타입</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">단가(평균)</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">계획 세대수</CTableHeaderCell>
        <CTableHeaderCell colspan="4">계약 현황</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">미계약 금액</CTableHeaderCell>
        <CTableHeaderCell rowspan="2">합계</CTableHeaderCell>
      </CTableRow>

      <CTableRow :color="TableSecondary" class="text-center">
        <CTableHeaderCell>계약 세대수</CTableHeaderCell>
        <CTableHeaderCell>계약 금액</CTableHeaderCell>
        <CTableHeaderCell>실수납 금액</CTableHeaderCell>
        <CTableHeaderCell>미수 금액</CTableHeaderCell>
      </CTableRow>
    </CTableHead>

    <CTableBody v-if="budgetList.length">
      <CTableRow v-for="bg in budgetList" :key="bg.pk" class="text-right">
        <CTableDataCell
          v-if="bg.unit_type === getFirstType(bg.order_group || 0)"
          :rowspan="getUTbyOGNum(bg.order_group || 0)"
          class="text-center"
          :color="TableSecondary"
        >
          <!-- 차수명 -->
          {{ getOGName(bg.order_group || 0).order_group_name }}
        </CTableDataCell>
        <CTableDataCell class="text-left pl-4">
          <v-icon icon="mdi mdi-square" :color="getUTName(bg.unit_type || 0).color" size="sm" />
          <!-- 타입명 -->
          {{ getUTName(bg.unit_type || 0).name }}
        </CTableDataCell>
        <!-- 단가(평균) -->
        <CTableDataCell>{{ numFormat(bg.average_price || 0) }}</CTableDataCell>
        <!-- 계획세대수 -->
        <CTableDataCell>{{ numFormat(bg.quantity) }}</CTableDataCell>
        <CTableDataCell>
          <!-- 계약세대수 -->
          {{ numFormat(getContNum(bg.order_group || 0, bg.unit_type || 0)) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 계약금액 -->
          {{ numFormat(getContSum(bg.order_group || 0, bg.unit_type || 0)) }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 실수납금액 -->
          {{
            numFormat(
              paidSum(bg.order_group || 0, bg.unit_type || 0)
                ? paidSum(bg.order_group || 0, bg.unit_type || 0).paid_sum
                : 0,
            )
          }}
        </CTableDataCell>
        <CTableDataCell>
          <!-- 미수금액 -->
          {{
            numFormat(
              getContSum(bg.order_group || 0, bg.unit_type || 0) -
                (paidSum(bg.order_group || 0, bg.unit_type || 0)
                  ? paidSum(bg.order_group || 0, bg.unit_type || 0).paid_sum
                  : 0),
            )
          }}
        </CTableDataCell>
        <CTableDataCell
          :class="{
            'text-danger':
              0 >
              (bg.average_price || 0) *
                (bg.quantity - (getContNum(bg.order_group || 0, bg.unit_type || 0) || 0)),
          }"
        >
          <!-- 미계약 금액 -->
          {{
            numFormat(
              (bg.average_price || 0) *
                (bg.quantity - (getContNum(bg.order_group || 0, bg.unit_type || 0) || 0)),
            )
          }}
        </CTableDataCell>
        <!-- 합계 -->
        <CTableDataCell>{{ numFormat(bg.budget) }}</CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableBody v-else>
      <CTableRow class="text-center text-danger" style="height: 200px">
        <CTableDataCell colspan="10">
          [
          <router-link :to="{ name: '수입 예산 등록' }"> 수입 예산 등록 </router-link>
          ] >> [신규 프로젝트] > [수입 예산 항목]에서 데이터를 등록하세요.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>

    <CTableHead>
      <CTableRow class="text-right" :color="TableSecondary">
        <CTableHeaderCell colspan="2" class="text-center"> 합계 </CTableHeaderCell>
        <CTableHeaderCell></CTableHeaderCell>
        <!-- 계획 세대수 합계 -->
        <CTableHeaderCell>{{ numFormat(totalBudgetNum) }}</CTableHeaderCell>
        <!-- 계약 세대수 합계 -->
        <CTableHeaderCell>{{ numFormat(totalContNum) }}</CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 계약 금액 합계 -->
          {{ numFormat(totalContSum) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 실수납 금액 합계 -->
          {{ numFormat(totalPaidSum) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 미수 금액 합계 -->
          {{ numFormat(totalContSum - totalPaidSum) }}
        </CTableHeaderCell>
        <CTableHeaderCell>
          <!-- 미계약 금액 합계 -->
          {{ numFormat(totalBudget - totalContSum) }}
        </CTableHeaderCell>
        <!-- 총계 -->
        <CTableHeaderCell>{{ numFormat(totalBudget) }}</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
  </CTable>
</template>
