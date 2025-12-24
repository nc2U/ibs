<script lang="ts" setup>
import { computed } from 'vue'
import type { ParseResult } from '@/composables/useExcelUpload'

interface Props {
  modelValue: boolean
  parseResult: ParseResult | null
  transactionAmount: number
  systemType: 'company' | 'project'
}

const props = defineProps<Props>()

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
}

const emit = defineEmits<Emits>()

const amountDiff = computed(() => {
  if (!props.parseResult) return 0
  return props.parseResult.totalAmount - props.transactionAmount
})

const amountStatus = computed(() => {
  if (!props.parseResult) return 'unknown'
  const diff = Math.abs(amountDiff.value)
  if (diff === 0) return 'valid'
  return 'invalid'
})

const contractOrAffiliateLabel = computed(() => {
  return props.systemType === 'project' ? '프로젝트' : '거래처'
})

const handleConfirm = () => {
  emit('confirm')
  emit('update:modelValue', false)
}

const handleCancel = () => {
  emit('update:modelValue', false)
}
</script>

<template>
  <v-dialog :model-value="modelValue" max-width="1000" persistent scrollable>
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>엑셀 업로드 미리보기</span>
        <v-spacer />
        <v-btn icon size="small" @click="handleCancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text v-if="parseResult">
        <!-- Validation Summary -->
        <v-alert
          :type="parseResult.isValid ? 'success' : 'warning'"
          variant="tonal"
          class="mb-4"
        >
          <div class="d-flex flex-column">
            <div>
              <strong>수정:</strong> {{ parseResult.validationSummary.updateCount }}건 |
              <strong>추가:</strong> {{ parseResult.validationSummary.createCount }}건 |
              <strong class="text-error">삭제:</strong>
              {{ parseResult.validationSummary.deleteCount }}건 |
              <strong class="text-error">오류:</strong>
              {{ parseResult.validationSummary.invalidRows }}건
            </div>
            <div class="mt-2">
              <strong>합계 금액:</strong> {{ parseResult.totalAmount.toLocaleString() }}원 |
              <strong>거래 금액:</strong> {{ transactionAmount.toLocaleString() }}원 |
              <strong :class="amountStatus === 'valid' ? 'text-success' : 'text-error'">
                차이: {{ amountDiff.toLocaleString() }}원
              </strong>
            </div>
          </div>
        </v-alert>

        <!-- Three Sections: Update / Create / Delete -->
        <div style="max-height: 500px; overflow-y: auto">
          <!-- Section 1: Entries to Update -->
          <div v-if="parseResult.entriesToUpdate.length > 0" class="mb-4">
            <div class="text-h6 mb-2 d-flex align-center">
              <v-icon icon="mdi-pencil" class="mr-2" color="primary"></v-icon>
              수정될 항목 ({{ parseResult.entriesToUpdate.length }}건)
            </div>
            <table class="w-100" style="border-collapse: collapse">
              <thead style="position: sticky; top: 0; background: white; z-index: 1">
                <tr style="border-bottom: 2px solid #e0e0e0; background: #f5f5f5">
                  <th class="pa-2 text-left" style="min-width: 50px">행</th>
                  <th class="pa-2 text-left" style="min-width: 150px">계정</th>
                  <th class="pa-2 text-left" style="min-width: 150px">내역</th>
                  <th class="pa-2 text-left" style="min-width: 100px">거래처</th>
                  <th class="pa-2 text-right" style="min-width: 100px">금액</th>
                  <th class="pa-2 text-left" style="min-width: 100px">증빙</th>
                  <th class="pa-2 text-left" style="min-width: 150px">상태</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="entry in parseResult.entriesToUpdate"
                  :key="entry.rowNumber"
                  :class="{ 'bg-red-lighten-5': !entry.isValid, 'bg-blue-lighten-5': entry.isValid }"
                  style="border-bottom: 1px solid #f0f0f0"
                >
                  <td class="pa-2">{{ entry.rowNumber }}</td>
                  <td class="pa-2">{{ entry.account_name }}</td>
                  <td class="pa-2">{{ entry.description }}</td>
                  <td class="pa-2">{{ entry.trader }}</td>
                  <td class="pa-2 text-right">{{ entry.amount.toLocaleString() }}</td>
                  <td class="pa-2">{{ entry.evidence_type }}</td>
                  <td class="pa-2">
                    <div v-if="entry.isValid">
                      <v-icon color="success" size="small">mdi-check-circle</v-icon>
                      <div
                        v-if="entry.validationWarnings.length > 0"
                        class="text-caption text-warning mt-1"
                      >
                        <div v-for="(warning, idx) in entry.validationWarnings" :key="idx">
                          {{ warning }}
                        </div>
                      </div>
                    </div>
                    <div v-else>
                      <v-icon color="error" size="small">mdi-alert-circle</v-icon>
                      <div class="text-caption text-error mt-1">
                        <div v-for="(error, idx) in entry.validationErrors" :key="idx">
                          {{ error }}
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Section 2: Entries to Create -->
          <div v-if="parseResult.entriesToCreate.length > 0" class="mb-4">
            <div class="text-h6 mb-2 d-flex align-center">
              <v-icon icon="mdi-plus-circle" class="mr-2" color="success"></v-icon>
              추가될 항목 ({{ parseResult.entriesToCreate.length }}건)
            </div>
            <table class="w-100" style="border-collapse: collapse">
              <thead style="position: sticky; top: 0; background: white; z-index: 1">
                <tr style="border-bottom: 2px solid #e0e0e0; background: #f5f5f5">
                  <th class="pa-2 text-left" style="min-width: 50px">행</th>
                  <th class="pa-2 text-left" style="min-width: 150px">계정</th>
                  <th class="pa-2 text-left" style="min-width: 150px">내역</th>
                  <th class="pa-2 text-left" style="min-width: 100px">거래처</th>
                  <th class="pa-2 text-right" style="min-width: 100px">금액</th>
                  <th class="pa-2 text-left" style="min-width: 100px">증빙</th>
                  <th class="pa-2 text-left" style="min-width: 150px">상태</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="entry in parseResult.entriesToCreate"
                  :key="entry.rowNumber"
                  :class="{ 'bg-red-lighten-5': !entry.isValid, 'bg-green-lighten-5': entry.isValid }"
                  style="border-bottom: 1px solid #f0f0f0"
                >
                  <td class="pa-2">{{ entry.rowNumber }}</td>
                  <td class="pa-2">{{ entry.account_name }}</td>
                  <td class="pa-2">{{ entry.description }}</td>
                  <td class="pa-2">{{ entry.trader }}</td>
                  <td class="pa-2 text-right">{{ entry.amount.toLocaleString() }}</td>
                  <td class="pa-2">{{ entry.evidence_type }}</td>
                  <td class="pa-2">
                    <div v-if="entry.isValid">
                      <v-icon color="success" size="small">mdi-check-circle</v-icon>
                      <div
                        v-if="entry.validationWarnings.length > 0"
                        class="text-caption text-warning mt-1"
                      >
                        <div v-for="(warning, idx) in entry.validationWarnings" :key="idx">
                          {{ warning }}
                        </div>
                      </div>
                    </div>
                    <div v-else>
                      <v-icon color="error" size="small">mdi-alert-circle</v-icon>
                      <div class="text-caption text-error mt-1">
                        <div v-for="(error, idx) in entry.validationErrors" :key="idx">
                          {{ error }}
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Section 3: Entries to Delete -->
          <div v-if="parseResult.entriesToDelete.length > 0" class="mb-4">
            <div class="text-h6 mb-2 d-flex align-center">
              <v-icon icon="mdi-delete" class="mr-2" color="error"></v-icon>
              삭제될 항목 ({{ parseResult.entriesToDelete.length }}건)
            </div>
            <v-alert type="warning" variant="tonal" class="mb-2">
              엑셀 파일의 행 수가 기존 항목보다 적어 다음 항목들이 삭제됩니다.
            </v-alert>
            <table class="w-100" style="border-collapse: collapse">
              <thead style="position: sticky; top: 0; background: white; z-index: 1">
                <tr style="border-bottom: 2px solid #e0e0e0; background: #f5f5f5">
                  <th class="pa-2 text-left" style="min-width: 150px">계정</th>
                  <th class="pa-2 text-left" style="min-width: 150px">내역</th>
                  <th class="pa-2 text-left" style="min-width: 100px">거래처</th>
                  <th class="pa-2 text-right" style="min-width: 100px">금액</th>
                  <th class="pa-2 text-left" style="min-width: 100px">증빙</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(entry, idx) in parseResult.entriesToDelete"
                  :key="idx"
                  class="bg-red-lighten-5"
                  style="border-bottom: 1px solid #f0f0f0"
                >
                  <td class="pa-2">{{ entry.account_name }}</td>
                  <td class="pa-2">{{ entry.description }}</td>
                  <td class="pa-2">{{ entry.trader }}</td>
                  <td class="pa-2 text-right">{{ entry.amount?.toLocaleString() }}</td>
                  <td class="pa-2">{{ entry.evidence_type }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="handleCancel">취소</v-btn>
        <v-btn color="primary" :disabled="!parseResult?.isValid" @click="handleConfirm">
          적용
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
table {
  font-size: 0.875rem;
}

th {
  font-weight: 600;
  background-color: #f5f5f5;
}
</style>
