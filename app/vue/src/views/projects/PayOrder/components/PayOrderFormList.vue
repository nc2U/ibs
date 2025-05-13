<script lang="ts" setup>
import { computed } from 'vue'
import { write_project } from '@/utils/pageAuth'
import { usePayment } from '@/store/pinia/payment'
import { type PayOrder as po } from '@/store/types/payment'
import { TableSecondary } from '@/utils/cssMixins'
import PayOrder from '@/views/projects/PayOrder/components/PayOrder.vue'

const emit = defineEmits(['on-update', 'on-delete'])

const paymentStore = usePayment()
const payOrderList = computed(() => paymentStore.payOrderList)

const onUpdatePayOrder = (payload: po) => emit('on-update', payload)
const onDeletePayOrder = (pk: number) => emit('on-delete', pk)
</script>

<template>
  <CTable hover responsive>
    <colgroup>
      <col style="width: 6%" />
      <col style="width: 5%" />
      <col style="width: 5%" />
      <col style="width: 4%" />
      <col style="width: 4%" />
      <col style="width: 6%" />
      <col style="width: 5%" />
      <col style="width: 6%" />
      <col style="width: 5%" />
      <col style="width: 7%" />
      <col style="width: 5%" />
      <col style="width: 6%" />
      <col style="width: 5%" />
      <col style="width: 7%" />
      <col style="width: 6%" />
      <col style="width: 5%" />
      <col style="width: 7%" />
      <col v-if="write_project" style="width: 6%" />
    </colgroup>
    <CTableHead :color="TableSecondary" class="text-center">
      <CTableRow>
        <CTableHeaderCell>타입종류</CTableHeaderCell>
        <CTableHeaderCell>회차종류</CTableHeaderCell>
        <CTableHeaderCell>공급가 포함 여부</CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          회차코드
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            프로젝트 내 납부회차별 코드번호 - 동일 회차 중복(분리) 등록 가능
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          납부순서
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            동일 납부회차에 2가지 항목을 별도로 납부하여야 하는 경우(ex: 분담금 + 업무대행료) 하나의
            납입회차 코드(ex: 1)에 2개의 납부순서(ex: 1, 2)를 등록한다.
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell>회차 명</CTableHeaderCell>
        <CTableHeaderCell>별칭</CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          약정금액
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            약정금이 차수, 타입에 관계 없이 정액인 경우 설정(예: 세대별 업무대행비)
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          납부비율(%)
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            분양가 대비 납부비율, 계약금 항목인 경우 "계약 금액 등록" 데이터 우선, 잔금 항목인 경우
            "공급 가격 등록" 데이터와 비교 차액 데이터 우선
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell>납부약정일</CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          전회기준 경과일수
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            전 회차(예: 계약일)로부터 __일 이내 형식으로 납부기한을 지정할 경우 해당 일수
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell>선납할인 적용</CTableHeaderCell>
        <CTableHeaderCell>선납할인율</CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          선납기준일
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            선납 할인 기준은 납부 약정일이 원칙이나 이 값이 있는 경우 선납 기준일로 우선 적용한다.
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell>연체가산 적용</CTableHeaderCell>
        <CTableHeaderCell>연체가산율</CTableHeaderCell>
        <CTableHeaderCell class="cursor-help">
          연체기준일
          <v-icon icon="mdi-tooltip-question-outline" size="14" color="grey" />
          <v-tooltip activator="parent" location="top">
            연체료 계산 기준은 납부기한일이 원칙이나 이 값이 있는 경우 연체 기준일로 우선 적용한다.
          </v-tooltip>
        </CTableHeaderCell>
        <CTableHeaderCell v-if="write_project">비고</CTableHeaderCell>
      </CTableRow>
    </CTableHead>
    <CTableBody v-if="payOrderList.length > 0">
      <PayOrder
        v-for="payOrder in payOrderList"
        :key="payOrder.pk as number"
        :pay-order="payOrder"
        @on-update="onUpdatePayOrder"
        @on-delete="onDeletePayOrder"
      />
    </CTableBody>

    <CTableBody v-else>
      <CTableRow>
        <CTableDataCell :colspan="write_project ? 17 : 16" class="text-center p-5 text-danger">
          등록된 데이터가 없습니다.
        </CTableDataCell>
      </CTableRow>
    </CTableBody>
  </CTable>
</template>
