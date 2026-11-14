<script lang="ts" setup>
import { computed, ref, watch } from 'vue'
import type { BulkParseResult } from '@/composables/useBulkTransExcel'

const props = defineProps<{
  modelValue: boolean
  result: BulkParseResult | null
  // 현재 폼에 입력된 거래가 있는지 (있으면 기본값을 '추가'로 둔다)
  hasExisting: boolean
  // 연관 대상 열 이름 (프로젝트: 계약자, 본사: 관계회사(프로젝트))
  relatedLabel?: string
  // 프로젝트 전용: 납부회차 목록
  payOrders?: Array<{ value: number; label: string }>
  // 거래계좌 목록 (통장 일괄 지정용)
  bankAccounts?: Array<{ value: number | string | null | undefined; label: string }>
  // 회계계정 목록 (계정과목 일괄 지정용)
  accounts?: Array<{ value: number; label: string; is_cate_only?: boolean }>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', payload: { replace: boolean }): void
}>()

const replace = ref(true)
const selectedBulkBank = ref<number | '' | null>(null)
const selectedBulkAccount = ref<number | null>(null)
const applyOnlyUnassignedAccount = ref(true)
const selectedBulkPayOrder = ref<number | null>(null)
const excludeDuplicates = ref(true)

watch(
  () => props.modelValue,
  open => {
    if (open) {
      replace.value = !props.hasExisting
      selectedBulkBank.value = null
      selectedBulkAccount.value = null
      selectedBulkPayOrder.value = null
      excludeDuplicates.value = true
    }
  },
)

// 실제 선택 가능한 계정과목 (대분류/범주 계정 제외)
const filteredAccounts = computed(() => (props.accounts || []).filter(a => !a.is_cate_only))

// 유효한 거래계좌 옵션
const validBankAccounts = computed(() =>
  (props.bankAccounts || []).filter(b => b.value !== null && b.value !== undefined && b.value !== ''),
)

// 결과 검증 및 요약 카운트 재계산
const updateResultSummary = () => {
  if (!props.result) return
  const validTransactions = props.result.transactions.filter(t => t.isValid).length
  props.result.summary.validTransactions = validTransactions
  props.result.summary.invalidTransactions = props.result.transactions.length - validTransactions
  props.result.isValid = props.result.transactions.length > 0 && validTransactions === props.result.transactions.length
}

// 1. 거래계좌 일괄 적용
const applyBulkBankAccount = () => {
  if (
    !props.result ||
    selectedBulkBank.value === null ||
    selectedBulkBank.value === '' ||
    selectedBulkBank.value === undefined ||
    !props.bankAccounts
  )
    return
  const matched = props.bankAccounts.find(b => b.value === selectedBulkBank.value)
  if (!matched) return

  props.result.transactions.forEach(t => {
    t.bankForm.bank_account = matched.value as number
    t.bankForm.bank_account_name = matched.label
    t.errors = t.errors.filter(err => !err.includes('거래계좌'))
    t.isValid = t.errors.length === 0 && t.entries.every(e => e.errors.length === 0)
  })
  updateResultSummary()
}

// 2. 계정과목 일괄 적용
const applyBulkAccount = () => {
  if (
    !props.result ||
    selectedBulkAccount.value === null ||
    selectedBulkAccount.value === undefined ||
    !props.accounts
  )
    return
  const matched = props.accounts.find(a => a.value === selectedBulkAccount.value)
  if (!matched) return

  props.result.transactions.forEach(t => {
    t.entries.forEach(e => {
      if (!applyOnlyUnassignedAccount.value || !e.account) {
        e.account = matched.value
        e.account_name = matched.label
        e.errors = e.errors.filter(err => !err.includes('계정'))
        e.isAutoMatched = false
      }
    })
    t.isValid = t.errors.length === 0 && t.entries.every(e => e.errors.length === 0)
  })
  updateResultSummary()
}

// 3. 일괄 납부회차 적용
const applyBulkPayOrder = () => {
  if (!props.result || !selectedBulkPayOrder.value || !props.payOrders) return
  const matched = props.payOrders.find(p => p.value === selectedBulkPayOrder.value)
  if (!matched) return

  props.result.transactions.forEach(t => {
    t.entries.forEach(e => {
      e.installment_order = matched.value
      e.installment_order_name = matched.label
      e.warnings = e.warnings.filter(w => !w.includes('납부회차'))
    })
  })
}

// 유효 건수 (중복 제외 옵션 반영)
const validCount = computed(() => {
  if (!props.result) return 0
  return props.result.transactions.filter(t => {
    if (excludeDuplicates.value && t.isDuplicate) return false
    return t.isValid
  }).length
})

const duplicateCount = computed(() => props.result?.summary.duplicateCount ?? 0)

const handleConfirm = () => {
  if (props.result && excludeDuplicates.value) {
    props.result.transactions.forEach(t => {
      if (t.isDuplicate) t.isValid = false
    })
  }
  emit('confirm', { replace: replace.value })
  emit('update:modelValue', false)
}
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="1180" persistent scrollable>
    <v-card>
      <v-card-title class="d-flex align-center bg-grey-lighten-4 py-2">
        <v-icon color="primary" class="me-2">mdi-file-excel-box</v-icon>
        <span class="fw-bold">대량 거래 입력 엑셀 미리보기 및 검증</span>
        <v-spacer />
        <v-btn icon size="small" variant="text" @click="emit('update:modelValue', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text v-if="result" class="pa-4">
        <!-- 원본 서식 감지 배너 -->
        <v-alert
          v-if="result.fileFormat === 'bank_raw'"
          type="info"
          variant="tonal"
          class="mb-3 py-2"
          icon="mdi-bank-check"
        >
          <div class="d-flex align-center justify-space-between flex-wrap">
            <div>
              <v-chip size="x-small" color="primary" variant="flat" class="me-2 fw-bold">
                {{ result.detectedBankName || '인터넷 뱅킹' }} 원본 서식 감지
              </v-chip>
              <strong>은행 거래내역 엑셀 파일</strong>이 자동으로 감지되어 시스템 거래 항목으로 변환되었습니다.
            </div>
          </div>
          <div class="mt-1 text-caption text-grey-darken-2">
            ※ 통장 엑셀 특성상 계좌 및 계정과목이 미지정된 항목은 아래 <strong>[일괄 설정 도구]</strong>를 이용하여 원클릭으로 손쉽게 지정할 수 있습니다.
          </div>
        </v-alert>

        <!-- 요약 상태 알림 -->
        <v-alert :type="result.isValid ? 'success' : 'warning'" variant="tonal" class="mb-3 py-2">
          <div class="d-flex align-center justify-space-between flex-wrap">
            <div>
              <strong>은행거래:</strong> {{ result.summary.transactionCount }}건 (권장 최대 60건) |
              <strong>회계 계정:</strong> {{ result.summary.entryCount }}건 (최대 250행) |
              <strong class="text-success">반영 가능:</strong> {{ validCount }}건 |
              <strong class="text-error">오류:</strong> {{ result.summary.invalidTransactions }}건
              <template v-if="duplicateCount > 0">
                | <strong class="text-warning">중복 의심:</strong> {{ duplicateCount }}건
              </template>
            </div>
            <v-chip size="x-small" color="primary" variant="outlined" class="ms-auto">
              {{ result.fileFormat === 'bank_raw' ? '은행 원본 변환 모드' : 'IBS 표준 템플릿' }}
            </v-chip>
          </div>
          <div v-if="!result.isValid" class="mt-1 text-caption text-error">
            ※ 거래계좌 또는 계정과목 오류가 있는 거래는 제외되며, 상단 일괄 지정 도구를 통해 해결할 수 있습니다.
          </div>
        </v-alert>

        <!-- 일괄 지정 도구 패널 (통장 / 계정과목 / 납부회차 / 중복제외) -->
        <v-card variant="outlined" class="mb-3 bg-grey-lighten-5">
          <v-card-text class="py-2">
            <div class="text-caption fw-bold text-primary mb-2 d-flex align-center">
              <v-icon size="16" color="primary" class="me-1">mdi-auto-fix</v-icon>
              원클릭 일괄 지정 및 편의 도구
            </div>

            <div class="d-flex flex-wrap align-center ga-3">
              <!-- 1. 거래계좌 일괄 지정 -->
              <div v-if="validBankAccounts.length" class="d-flex align-center ga-1 flex-grow-1" style="min-width: 260px">
                <v-select
                  v-model="selectedBulkBank"
                  :items="validBankAccounts"
                  item-title="label"
                  item-value="value"
                  density="compact"
                  variant="outlined"
                  hide-details
                  placeholder="거래계좌 선택"
                  class="bg-white"
                  clearable
                />
                <v-btn
                  size="small"
                  color="indigo"
                  variant="flat"
                  :disabled="!selectedBulkBank"
                  @click="applyBulkBankAccount"
                >
                  계좌 일괄 적용
                </v-btn>
              </div>

              <!-- 2. 계정과목 일괄 지정 -->
              <div v-if="filteredAccounts.length" class="d-flex align-center ga-1 flex-grow-1" style="min-width: 280px">
                <v-select
                  v-model="selectedBulkAccount"
                  :items="filteredAccounts"
                  item-title="label"
                  item-value="value"
                  density="compact"
                  variant="outlined"
                  hide-details
                  placeholder="계정과목 선택"
                  class="bg-white"
                  clearable
                />
                <v-btn
                  size="small"
                  color="teal"
                  variant="flat"
                  :disabled="!selectedBulkAccount"
                  @click="applyBulkAccount"
                >
                  계정 일괄 적용
                </v-btn>
                <v-checkbox
                  v-model="applyOnlyUnassignedAccount"
                  label="미지정만"
                  density="compact"
                  hide-details
                  class="ma-0 pa-0 text-caption"
                  v-tooltip="'체크 시 계정과목이 아직 지정되지 않은 항목에만 적용합니다.'"
                />
              </div>

              <!-- 3. 납부회차 일괄 지정 (프로젝트 분양 모드) -->
              <div v-if="payOrders && payOrders.length" class="d-flex align-center ga-1 flex-grow-1" style="min-width: 240px">
                <v-select
                  v-model="selectedBulkPayOrder"
                  :items="payOrders"
                  item-title="label"
                  item-value="value"
                  density="compact"
                  variant="outlined"
                  hide-details
                  placeholder="납부회차 선택"
                  class="bg-white"
                  clearable
                />
                <v-btn
                  size="small"
                  color="deep-purple"
                  variant="flat"
                  :disabled="!selectedBulkPayOrder"
                  @click="applyBulkPayOrder"
                >
                  회차 일괄 적용
                </v-btn>
              </div>
            </div>

            <!-- 중복 의심 거래 건너뛰기 토글 -->
            <div v-if="duplicateCount > 0" class="mt-2 pt-2 border-t d-flex align-center">
              <v-icon color="warning" size="18" class="mr-1">mdi-alert-box-outline</v-icon>
              <span class="text-caption font-weight-bold text-grey-darken-3 mr-3">
                기존 등록된 거래와 일치하는 중복 의심 거래가 {{ duplicateCount }}건 있습니다.
              </span>
              <v-switch
                v-model="excludeDuplicates"
                label="중복 의심 거래 제외하고 반영 (권장)"
                color="warning"
                density="compact"
                hide-details
              />
            </div>
          </v-card-text>
        </v-card>

        <div v-if="result.transactions.length === 0" class="text-center text-grey py-6">
          읽을 수 있는 거래 행이 없습니다. 엑셀 파일 형식을 확인해 주세요.
        </div>

        <div style="max-height: 480px; overflow-y: auto">
          <v-card
            v-for="t in result.transactions"
            :key="t.firstRow"
            variant="outlined"
            class="mb-3"
            :color="t.isDuplicate && excludeDuplicates ? 'warning' : t.isValid ? undefined : 'error'"
          >
            <v-card-text class="py-2">
              <div class="d-flex align-center flex-wrap ga-2">
                <v-icon
                  :icon="t.isDuplicate && excludeDuplicates ? 'mdi-alert-circle-outline' : t.isValid ? 'mdi-check-circle' : 'mdi-alert-circle'"
                  :color="t.isDuplicate && excludeDuplicates ? 'warning' : t.isValid ? 'success' : 'error'"
                  size="18"
                />
                <strong class="text-grey-darken-2">#{{ t.key }}</strong>
                <v-chip size="x-small" :color="t.bankForm.sort === 1 ? 'indigo' : 'red'" variant="flat">
                  {{ t.bankForm.sort === 1 ? '입금' : '출금' }}
                </v-chip>
                <span class="font-weight-medium">{{ t.bankForm.deal_date }}</span>
                <span v-if="t.bankForm.bank_account_name" class="text-primary font-weight-medium">
                  {{ t.bankForm.bank_account_name }}
                </span>
                <span v-else class="text-error font-weight-medium">
                  [계좌 미지정]
                </span>
                <span class="text-grey-darken-1">{{ t.bankForm.content }}</span>

                <v-chip v-if="t.isDuplicate" size="x-small" color="warning" variant="tonal">
                  중복 의심: {{ t.duplicateReason }}
                </v-chip>

                <v-spacer />
                <span class="fw-bold">
                  {{ (t.bankForm.amount ?? 0).toLocaleString() }}원
                </span>
              </div>

              <div v-for="(msg, i) in t.errors" :key="`e${i}`" class="text-error text-caption ml-6 mt-1">
                ✖ {{ msg }}
              </div>
              <div
                v-for="(msg, i) in t.warnings"
                :key="`w${i}`"
                class="text-warning text-caption ml-6 mt-1"
              >
                ⚠ {{ msg }}
              </div>

              <!-- 분개 항목 표 -->
              <table class="w-100 mt-2" style="border-collapse: collapse; font-size: 0.85rem">
                <thead>
                  <tr style="background: #f5f5f5">
                    <th class="pa-1 text-start" style="width: 50px">행</th>
                    <th class="pa-1 text-start">계정이름</th>
                    <th class="pa-1 text-start">거래처</th>
                    <th class="pa-1 text-end" style="width: 130px">분류금액</th>
                    <th class="pa-1 text-start">{{ relatedLabel ?? '계약자' }}</th>
                    <th v-if="payOrders && payOrders.length" class="pa-1 text-start">납부회차</th>
                    <th class="pa-1 text-start" style="width: 140px">상태/검증</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="e in t.entries" :key="e.rowNumber" style="border-top: 1px solid #eee">
                    <td class="pa-1 text-grey">{{ e.rowNumber }}</td>
                    <td class="pa-1">
                      <span v-if="e.account_name" class="fw-medium">
                        {{ e.account_name }}
                      </span>
                      <span v-else class="text-error fw-bold">
                        (미지정)
                      </span>
                      <v-chip v-if="e.isAutoMatched" size="x-small" color="teal" variant="flat" class="ms-1">
                        자동추천
                      </v-chip>
                    </td>
                    <td class="pa-1">{{ e.trader || '-' }}</td>
                    <td class="pa-1 text-end fw-medium">{{ e.amount.toLocaleString() }}원</td>
                    <td class="pa-1">
                      <span>{{ e.contract_name || '-' }}</span>
                      <v-chip v-if="e.isContractAutoMatched" size="x-small" color="indigo" variant="flat" class="ms-1">
                        계약자 매칭
                      </v-chip>
                    </td>
                    <td v-if="payOrders && payOrders.length" class="pa-1">
                      <span v-if="e.installment_order_name" class="text-primary fw-medium">
                        {{ e.installment_order_name }}
                      </span>
                      <span v-else class="text-grey">-</span>
                    </td>
                    <td class="pa-1">
                      <span v-for="(m, i) in e.errors" :key="`ee${i}`" class="text-error d-block">
                        ✖ {{ m }}
                      </span>
                      <span v-for="(m, i) in e.warnings" :key="`ew${i}`" class="text-warning d-block">
                        ⚠ {{ m }}
                      </span>
                      <span v-if="!e.errors.length && !e.warnings.length" class="text-success fw-bold">
                        ✓ 정상
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>

      <v-card-actions class="bg-grey-lighten-4 py-2 px-4">
        <v-switch
          v-model="replace"
          color="primary"
          density="compact"
          hide-details
          :label="replace ? '현재 입력 내용을 대체' : '현재 입력 내용 뒤에 추가'"
          class="me-3"
        />
        <v-spacer />
        <v-btn variant="tonal" @click="emit('update:modelValue', false)">취소</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :disabled="validCount === 0"
          @click="handleConfirm"
        >
          정상 {{ validCount }}건 폼에 반영
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
