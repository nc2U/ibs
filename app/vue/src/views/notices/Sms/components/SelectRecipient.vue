<script lang="ts" setup>
import { inject, computed, ref, watch, nextTick } from 'vue'
import { useNotice } from '@/store/pinia/notice'
import { useProject } from '@/store/pinia/project'
import type { Project } from '@/store/types/project.ts'
import AlertModal from '@/components/Modals/AlertModal.vue'

// Props 정의
const recipientInput = defineModel<string>('recipient-input')
const recipientsList = defineModel<string[]>('recipients-list')

// Stores
const projectStore = useProject()
const notiStore = useNotice()

// 다크 테마 감지
const isDark = inject<any>('isDark')

const refAlertModal = ref<InstanceType<typeof AlertModal>>()

// 그룹 선택
const selectedGroup = ref('')

// 그룹 정보 저장
interface RecipientGroup {
  groupName: string
  groupType: string
  phones: string[]
}

const recipientGroups = ref<RecipientGroup[]>([])
const individualRecipients = ref<string[]>([])

// recipientsList와 동기화
watch(
  [recipientGroups, individualRecipients],
  () => {
    const groupPhones = recipientGroups.value.flatMap(g => g.phones)
    const allPhones = [...new Set([...individualRecipients.value, ...groupPhones])]
    recipientsList.value = allPhones as any
  },
  { deep: true },
)

// 그룹명 매핑
const getGroupName = (groupType: string): string => {
  const groupNames: Record<string, string> = {
    all: '전체 계약자',
    // 추후 확장: order_1, order_2 등
  }
  return groupNames[groupType] || groupType
}

// v-expansion-panels 배경색 (다크 테마 대응)
const panelBgColor = computed(() => {
  return isDark?.value ? '#282933' : '#ffffff'
})

// v-expansion-panels 초기 활성 패널 (기본: 첫 번째 패널)
const activePanel = ref<number | null>(0)

const handleAddRecipient = () => {
  const input = recipientInput.value
  if (!input) return

  // v-maska 포맷: ###-###-#### (12자) 또는 ###-####-#### (13자)
  const phoneLength = input.length
  if (phoneLength !== 12 && phoneLength !== 13) {
    refAlertModal.value?.callModal('', '올바른 전화번호 형식을 입력하세요. (예: 010-1234-5678)')
    return
  }

  // 중복 체크 (전체 목록에서)
  const allRecipients = recipientsList.value || []
  if ((allRecipients as any[]).includes(input)) {
    refAlertModal.value?.callModal('', '이미 추가된 번호입니다.')
    return
  }

  individualRecipients.value.push(input)
  recipientInput.value = undefined as any
}

const handleRemoveIndividual = (phoneNumber: string) => {
  individualRecipients.value = individualRecipients.value.filter(item => item !== phoneNumber)
}

const handleRemoveGroup = (groupType: string) => {
  recipientGroups.value = recipientGroups.value.filter(g => g.groupType !== groupType)
}

const handleClearAll = () => {
  recipientGroups.value = []
  individualRecipients.value = []
}

const handleGroupSelect = async () => {
  await nextTick(async () => {
    // 빈 값 선택 시 아무 동작 안 함 (선택안함)
    if (!selectedGroup.value || selectedGroup.value === '') {
      return
    }

    const projectId = (projectStore.project as Project)?.pk

    if (!projectId) {
      refAlertModal.value?.callModal('', '프로젝트를 먼저 선택해주세요.')
      selectedGroup.value = ''
      return
    }

    // 이미 추가된 그룹인지 확인
    if (recipientGroups.value.some(g => g.groupType === selectedGroup.value)) {
      refAlertModal.value?.callModal('', '이미 추가된 그룹입니다.')
      selectedGroup.value = ''
      return
    }

    try {
      const data = await notiStore.fetchRecipientGroup(projectId, selectedGroup.value)
      const phones = data.phone_numbers || []

      if (phones.length === 0) {
        // 디버그 정보 포함한 에러 메시지
        let debugMsg = `해당 그룹에 유효한 연락처가 없습니다.\n`
        debugMsg += `프로젝트 ID: ${projectId}, 그룹: ${getGroupName(selectedGroup.value)}\n`

        if (data.debug) {
          debugMsg += `\n[디버그 정보]\n`
          debugMsg += `전체 계약자: ${data.debug.total_contractors}명\n`
          debugMsg += `활성 계약: ${data.debug.active_contracts}건\n`
          debugMsg += `활성 계약자: ${data.debug.active_contractors}명`
        }

        refAlertModal.value?.callModal('', debugMsg)
        selectedGroup.value = ''
        return
      }

      // 그룹 정보 저장
      recipientGroups.value.push({
        groupName: getGroupName(selectedGroup.value),
        groupType: selectedGroup.value,
        phones: phones,
      })

      refAlertModal.value?.callModal(
        '',
        `${data.debug.active_contractors}명의 계약 자 중 중복 제거 후 ${phones.length}명의 연락처가 추가되었습니다.`,
      )
    } catch (error) {
      refAlertModal.value?.callModal('', '그룹 조회 중 오류가 발생했습니다.')
    } finally {
      selectedGroup.value = '' // 선택 초기화
    }
  })
}
</script>

<template>
  <CCol :xs="12">
    <CCard class="mb-4">
      <CCardHeader style="height: 48px; padding-top: 12px">
        <v-icon icon="mdi-account-multiple" class="me-2" />
        <strong>수신자 관리</strong>
      </CCardHeader>
      <CCardBody>
        <!-- 수신자 입력 방법 선택 -->
        <v-expansion-panels v-model="activePanel" class="mb-3" :bg-color="panelBgColor">
          <v-expansion-panel>
            <v-expansion-panel-title>
              <v-icon icon="mdi-account-plus" class="me-2" />
              개별 번호 입력
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <CRow class="align-items-end">
                <CCol cols="12" md="10">
                  <label for="recipient-phone-input" class="form-label">휴대폰 번호</label>
                  <input
                    id="recipient-phone-input"
                    v-model="recipientInput"
                    v-maska
                    data-maska="['###-###-####', '###-####-####']"
                    maxlength="13"
                    placeholder="휴대전화 번호를 입력하세요."
                    class="form-control"
                    @keydown.enter="handleAddRecipient"
                  />
                </CCol>
                <CCol cols="12" md="2">
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
                v-model="selectedGroup"
                label="수신자 그룹"
                :options="[
                  { value: '', label: '---------' },
                  { value: 'all', label: '전체 계약자' },
                ]"
                :disabled="notiStore.loading"
                @change="handleGroupSelect"
              />
              <div v-if="notiStore.loading" class="mt-2">
                <v-progress-linear indeterminate color="primary" />
                <small class="text-muted">연락처를 조회하고 있습니다...</small>
              </div>
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
                <!-- 그룹으로 추가된 수신자 -->
                <v-chip
                  v-for="group in recipientGroups"
                  :key="`group-${group.groupType}`"
                  class="ma-1"
                  color="primary"
                  variant="tonal"
                  closable
                  @click:close="handleRemoveGroup(group.groupType)"
                >
                  {{ group.groupName }} ({{ group.phones[0] }} 외 {{ group.phones.length - 1 }}명)
                </v-chip>

                <!-- 개별 추가된 수신자 -->
                <v-chip
                  v-for="(recipient, index) in individualRecipients"
                  :key="`individual-${index}-${recipient}`"
                  class="ma-1"
                  closable
                  @click:close="handleRemoveIndividual(recipient)"
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

  <AlertModal ref="refAlertModal" />
</template>
