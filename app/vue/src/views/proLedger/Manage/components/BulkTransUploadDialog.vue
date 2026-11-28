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
  (e: 'update:result', value: BulkParseResult | null): void
  (e: 'confirm', payload: { replace: boolean; result: BulkParseResult | null }): void
}>()

const localResult = ref<BulkParseResult | null>(null)

const cloneResult = (src: BulkParseResult | null): BulkParseResult | null => {
  if (!src) return null
  return {
    ...src,
    summary: { ...src.summary },
    transactions: src.transactions.map(t => ({
      ...t,
      bankForm: { ...t.bankForm },
      errors: [...t.errors],
      warnings: [...t.warnings],
      entries: t.entries.map(e => ({
        ...e,
        errors: [...e.errors],
        warnings: [...e.warnings],
      })),
    })),
  }
}

const replace = ref(true)
const selectedBulkBank = ref<number | '' | null>(null)
const selectedBulkAccount = ref<number | null>(null)
const applyOnlyUnassignedAccount = ref(true)
const selectedBulkPayOrder = ref<number | null>(null)
const excludeDuplicates = ref(true)

watch(
  () => [props.modelValue, props.result] as const,
  ([open, nextResult]) => {
    if (open) {
      localResult.value = cloneResult(nextResult)
      replace.value = !props.hasExisting
      selectedBulkBank.value = null
      selectedBulkAccount.value = null
      selectedBulkPayOrder.value = null
      excludeDuplicates.value = true
    } else if (!nextResult) {
      localResult.value = null
    }
  },
  { immediate: true },
)

// 실제 선택 가능한 계정과목 (대분류/범주 계정 제외)
const filteredAccounts = computed(() => (props.accounts || []).filter(a => !a.is_cate_only))

// 유효한 거래계좌 옵션
const validBankAccounts = computed(() =>
  (props.bankAccounts || []).filter(b => b.value !== null && b.value !== undefined && b.value !== ''),
)

// 결과 검증 및 요약 카운트 재계산
const updateResultSummary = () => {
  if (!localResult.value) return
  const validTransactions = localResult.value.transactions.filter(t => t.isValid).length
  localResult.value.summary.validTransactions = validTransactions
  localResult.value.summary.invalidTransactions =
    localResult.value.transactions.length - validTransactions
  localResult.value.isValid =
    localResult.value.transactions.length > 0 &&
    validTransactions === localResult.value.transactions.length
}

// 1. 거래계좌 일괄 적용
const applyBulkBankAccount = () => {
  if (
    !localResult.value ||
    selectedBulkBank.value === null ||
    selectedBulkBank.value === '' ||
    selectedBulkBank.value === undefined ||
    !props.bankAccounts
  )
    return
  const matched = props.bankAccounts.find(b => b.value === selectedBulkBank.value)
  if (!matched) return

  localResult.value.transactions.forEach(t => {
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
    !localResult.value ||
    selectedBulkAccount.value === null ||
    selectedBulkAccount.value === undefined ||
    !props.accounts
  )
    return
  const matched = props.accounts.find(a => a.value === selectedBulkAccount.value)
  if (!matched) return

  localResult.value.transactions.forEach(t => {
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
  if (!localResult.value || !selectedBulkPayOrder.value || !props.payOrders) return
  const matched = props.payOrders.find(p => p.value === selectedBulkPayOrder.value)
  if (!matched) return

  localResult.value.transactions.forEach(t => {
    t.entries.forEach(e => {
      e.installment_order = matched.value
      e.installment_order_name = matched.label
      e.warnings = e.warnings.filter(w => !w.includes('납부회차'))
    })
  })
}

// 유효 건수 (중복 제외 옵션 반영)
const validCount = computed(() => {
  if (!localResult.value) return 0
  return localResult.value.transactions.filter(t => {
    if (excludeDuplicates.value && t.isDuplicate) return false
    return t.isValid
  }).length
})

const duplicateCount = computed(() => localResult.value?.summary.duplicateCount ?? 0)

const handleConfirm = () => {
  if (localResult.value && excludeDuplicates.value) {
    localResult.value.transactions.forEach(t => {
      if (t.isDuplicate) t.isValid = false
    })
  }
  const confirmedResult = cloneResult(localResult.value)
  emit('update:result', confirmedResult)
  emit('confirm', { replace: replace.value, result: confirmedResult })
  emit('update:modelValue', false)
}
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="1180" persistent scrollable>
    <v-card>
      <v-card-title class="d-flex align-center bulk-header-surface py-2">
        <v-icon color="primary" class="me-2">mdi-file-excel-box</v-icon>
        <span class="fw-bold">대량 거래 입력 엑셀 미리보기 및 검증</span>
        <v-spacer />
        <v-btn icon size="small" variant="text" @click="emit('update:modelValue', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text v-if="localResult" class="pa-4">
        <!-- 원본 서식 감지 배너 -->
        <v-alert
          v-if="localResult.fileFormat === 'bank_raw'"
          type="info"
          variant="tonal"
          class="mb-3 py-2"
          icon="mdi-bank-check"
        >
          <div class="d-flex align-center justify-space-between flex-wrap">
            <div>
              <v-chip size="x-small" color="primary" variant="flat" class="me-2 fw-bold">
                {{ localResult.detectedBankName || '인터넷 뱅킹' }} 원본 서식 감지
              </v-chip>
              <strong>은행 거래내역 엑셀 파일</strong>이 자동으로 감지되어 시스템 거래 항목으로 변환되었습니다.
            </div>
          </div>
          <div class="mt-1 text-caption text-medium-emphasis">
            ※ 통장 엑셀 특성상 계좌 및 계정과목이 미지정된 항목은 아래 <strong>[일괄 설정 도구]</strong>를 이용하여 원클릭으로 손쉽게 지정할 수 있습니다.
          </div>
        </v-alert>

        <!-- 요약 상태 알림 -->
        <v-alert :type="localResult.isValid ? 'success' : 'warning'" variant="tonal" class="mb-3 py-2">
          <div class="d-flex align-center justify-space-between flex-wrap">
            <div>
              <strong>은행거래:</strong> {{ localResult.summary.transactionCount }}건 (권장 최대 60건) |
              <strong>회계 계정:</strong> {{ localResult.summary.entryCount }}건 (최대 250행) |
              <strong class="text-success">반영 가능:</strong> {{ validCount }}건 |
              <strong class="text-error">오류:</strong> {{ localResult.summary.invalidTransactions }}건
              <template v-if="duplicateCount > 0">
                | <strong class="text-warning">중복 의심:</strong> {{ duplicateCount }}건
              </template>
            </div>
            <v-chip size="x-small" color="primary" variant="outlined" class="ms-auto">
              {{ localResult.fileFormat === 'bank_raw' ? '은행 원본 변환 모드' : 'IBS 표준 템플릿' }}
            </v-chip>
          </div>
          <div v-if="!localResult.isValid" class="mt-1 text-caption text-error">
            ※ 거래계좌 또는 계정과목 오류가 있는 거래는 제외되며, 상단 일괄 지정 도구를 통해 해결할 수 있습니다.
          </div>
        </v-alert>

        <!-- 일괄 지정 도구 패널 (통장 / 계정과목 / 납부회차 / 중복제외) -->
        <v-card variant="outlined" class="mb-3 bulk-panel-surface">
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
              <v-icon color="warning" size="18" class="me-1">mdi-alert-box-outline</v-icon>
              <span class="text-caption fw-bold text-high-emphasis me-3">
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

        <div v-if="localResult.transactions.length === 0" class="text-center text-medium-emphasis py-6">
          읽을 수 있는 거래 행이 없습니다. 엑셀 파일 형식을 확인해 주세요.
        </div>

        <div style="max-height: 480px; overflow-y: auto">
          <v-card
            v-for="t in localResult.transactions"
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
                <strong class="text-medium-emphasis">#{{ t.key }}</strong>
                <v-chip size="x-small" :color="t.bankForm.sort === 1 ? 'indigo' : 'red'" variant="flat">
                  {{ t.bankForm.sort === 1 ? '입금' : '출금' }}
                </v-chip>
                <span class="fw-medium">{{ t.bankForm.deal_date }}</span>
                <span v-if="t.bankForm.bank_account_name" class="text-primary fw-medium">
                  {{ t.bankForm.bank_account_name }}
                </span>
                <span v-else class="text-error fw-medium">
                  [계좌 미지정]
                </span>
                <span class="text-medium-emphasis">{{ t.bankForm.content }}</span>

                <v-chip v-if="t.isDuplicate" size="x-small" color="warning" variant="tonal">
                  중복 의심: {{ t.duplicateReason }}
                </v-chip>

                <v-spacer />
                <span class="fw-bold">
                  {{ (t.bankForm.amount ?? 0).toLocaleString() }}원
                </span>
              </div>

              <div v-for="(msg, i) in t.errors" :key="`e${i}`" class="text-error text-caption ms-6 mt-1">
                ✖ {{ msg }}
              </div>
              <div
                v-for="(msg, i) in t.warnings"
                :key="`w${i}`"
                class="text-warning text-caption ms-6 mt-1"
              >
                ⚠ {{ msg }}
              </div>

              <!-- 분개 항목 표 -->
              <table class="w-100 mt-2 bulk-entry-table">
                <thead>
                  <tr class="bulk-table-head-row">
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
                  <tr v-for="e in t.entries" :key="e.rowNumber" class="bulk-table-body-row">
                    <td class="pa-1 text-medium-emphasis">{{ e.rowNumber }}</td>
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
                      <span v-else class="text-medium-emphasis">-</span>
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

      <v-card-actions class="bulk-header-surface py-2 px-4">
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

<style scoped lang="scss">
.bulk-header-surface {
  background-color: #f5f5f5;
}

.bulk-panel-surface {
  background-color: #fafafa;
}

.bulk-entry-table {
  border-collapse: collapse;
  font-size: 0.85rem;
}

.bulk-table-head-row {
  background-color: #f5f5f5;
}

.bulk-table-body-row {
  border-top: 1px solid #eeeeee;
}

.dark-theme {
  .bulk-header-surface {
    background-color: #2f3349;
  }

  .bulk-panel-surface {
    background-color: #25293c;
  }

  .bulk-table-head-row {
    background-color: #2f3349;
  }

  .bulk-table-body-row {
    border-top-color: rgba(255, 255, 255, 0.12);
  }
}
</style>
