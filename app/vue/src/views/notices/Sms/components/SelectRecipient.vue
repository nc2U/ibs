<script lang="ts" setup>
import { inject, computed } from 'vue'

// Props 정의
const recipientInput = defineModel<string>('recipient-input')
const recipientsList = defineModel<string[]>('recipients-list')

// 다크 테마 감지
const isDark = inject<any>('isDark')

// v-expansion-panels 배경색 (다크 테마 대응)
const panelBgColor = computed(() => {
  return isDark?.value ? '#282933' : '#ffffff'
})

const handleAddRecipient = () => {
  const input = recipientInput.value
  if (!input) return

  const list: string[] = (recipientsList.value || []) as string[]
  list.push(input)
  recipientsList.value = list as any

  recipientInput.value = undefined as any
}

const handleRemoveRecipient = (phoneNumber: string) => {
  const list = recipientsList.value as string[]
  if (list && Array.isArray(list)) {
    const newList = list.filter(item => item !== phoneNumber)
    recipientsList.value = newList as any
  }
}

const handleClearAll = () => (recipientsList.value = [] as any)
</script>

<template>
  <CCol :md="6" :xs="12">
    <CCard class="mb-4">
      <CCardHeader style="height: 48px; padding-top: 12px">
        <v-icon icon="mdi-account-multiple" class="me-2" />
        <strong>수신자 관리</strong>
      </CCardHeader>
      <CCardBody>
        <!-- 수신자 입력 방법 선택 -->
        <v-expansion-panels class="mb-3" :bg-color="panelBgColor">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon icon="mdi-account-plus" class="me-2" />
              개별 번호 입력
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <CRow class="align-items-end">
                <CCol cols="12" md="8">
                  <input
                    v-model="recipientInput"
                    v-maska
                    data-maska="['###-###-####', '###-####-####']"
                    maxlength="13"
                    placeholder="010-1234-5678"
                    label="휴대폰 번호"
                    class="form-control"
                    @keydown.enter="handleAddRecipient"
                  />
                </CCol>
                <CCol cols="12" md="4">
                  <v-btn color="primary" @click="handleAddRecipient" prepend-icon="mdi-plus" block>
                    추가
                  </v-btn>
                </CCol>
              </CRow>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon icon="mdi-account-group" class="me-2" />
              그룹 선택
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <CFormSelect
                label="수신자 그룹"
                :options="[
                  { value: 'all', label: '전체 계약자' },
                  { value: 'contractors', label: '계약 완료자' },
                  { value: 'applicants', label: '청약자' },
                ]"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon icon="mdi-file-excel" class="me-2" />
              Excel 파일 업로드
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-file-input
                label="Excel 파일 선택"
                accept=".xlsx,.xls"
                prepend-icon="mdi-file-excel"
                show-size
              />
              <v-alert type="info" variant="tonal" class="mt-2" density="compact">
                첫 번째 열에 휴대폰 번호를 입력해주세요.
              </v-alert>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- 선택된 수신자 목록 -->
        <div class="mt-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <strong>선택된 수신자 ({{ recipientsList?.length || 0 }}명)</strong>
            <v-btn size="small" color="error" variant="outlined" @click="handleClearAll">
              전체 삭제
            </v-btn>
          </div>

          <CCard v-if="recipientsList && recipientsList.length > 0" variant="outline">
            <CCardBody class="p-2">
              <div style="max-height: 200px; overflow-y: auto">
                <v-chip
                  v-for="(recipient, index) in recipientsList"
                  :key="`recipient-${index}-${recipient}`"
                  class="ma-1"
                  closable
                  @click:close="handleRemoveRecipient(recipient)"
                >
                  {{ recipient }}
                </v-chip>
              </div>
            </CCardBody>
          </CCard>

          <v-alert v-else type="info" variant="tonal" density="compact">
            수신자를 선택해주세요.
          </v-alert>
        </div>
      </CCardBody>
    </CCard>
  </CCol>
</template>
