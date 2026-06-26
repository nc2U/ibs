<script lang="ts" setup>
import ExcelJS from 'exceljs'
import { computed, nextTick, ref, watch } from 'vue'
import { useStore } from '@/store'
import { useNotice } from '@/store/pinia/notice'
import { useProject } from '@/store/pinia/project'
import type { Project } from '@/store/types/project.ts'
import AlertModal from '@/components/Modals/AlertModal.vue'

// Props 정의
const recipientInput = defineModel<string>('recipient-input')
const recipientsList = defineModel<string[]>('recipients-list')

const props = defineProps<{
  hasTemplateVariables?: boolean
  variableNames?: string[]
}>()

// Emits 정의
const emit = defineEmits<{
  'update:recipientsWithVariables': [
    value: Array<{ phone: string; variables: Record<string, string> }>,
  ]
}>()

// Stores
const projectStore = useProject()
const notiStore = useNotice()

// 다크 테마 감지
const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const refAlertModal = ref<InstanceType<typeof AlertModal>>()

// 그룹 선택
const selectedGroup = ref('')

// 엑셀 파일 처리
const excelLoading = ref(false)
const excelFileInput = ref<File | null>(null)

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

/**
 * 전화번호 포맷 정리 및 유효성 검증
 * @param rawPhone 원본 전화번호 문자열
 * @returns 포맷팅된 전화번호 또는 null (무효)
 *
 * 지원 형식:
 * - 9자리: 021112222 → 02-111-2222 (서울 3자리 국번)
 * - 10자리: 0212345678 → 02-1234-5678 (서울 4자리 국번)
 * - 10자리: 0311234567 → 031-123-4567 (경기 3자리 국번)
 * - 11자리: 01012345678 → 010-1234-5678 (휴대폰)
 */
const normalizePhoneNumber = (rawPhone: string): string | null => {
  // 공백, 하이픈, 괄호, 점 제거
  const digitsOnly = rawPhone.replace(/[\s\-().]/g, '')

  // 숫자만 남았는지 확인
  if (!/^\d+$/.test(digitsOnly)) {
    return null
  }

  const length = digitsOnly.length

  // 길이 검증 (9~11자)
  if (length < 9 || length > 11) {
    return null
  }

  // 11자리: 휴대폰 (010, 011, 016, 017, 018, 019)
  if (length === 11) {
    return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3, 7)}-${digitsOnly.slice(7)}`
  }

  // 10자리: 지역번호 판단
  if (length === 10) {
    const prefix = digitsOnly.slice(0, 2)

    // 02 (서울): 02-XXXX-XXXX
    if (prefix === '02') {
      return `${digitsOnly.slice(0, 2)}-${digitsOnly.slice(2, 6)}-${digitsOnly.slice(6)}`
    }

    // 031~070 (지역번호): 0XX-XXX-XXXX
    return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3, 6)}-${digitsOnly.slice(6)}`
  }

  // 9자리: 서울 3자리 국번 또는 지역번호 3자리 국번
  if (length === 9) {
    const prefix = digitsOnly.slice(0, 2)

    // 02 (서울): 02-XXX-XXXX
    if (prefix === '02') {
      return `${digitsOnly.slice(0, 2)}-${digitsOnly.slice(2, 5)}-${digitsOnly.slice(5)}`
    }

    // 031~070 (지역번호): 0XX-XXX-XXXX
    return `${digitsOnly.slice(0, 3)}-${digitsOnly.slice(3, 6)}-${digitsOnly.slice(6)}`
  }

  return null
}

/**
 * 여러 줄의 전화번호 텍스트를 파싱
 * @param text 입력된 텍스트 (줄바꿈 포함 가능)
 * @returns { valid: string[], invalid: string[] }
 */
const parseMultiplePhoneNumbers = (text: string): { valid: string[]; invalid: string[] } => {
  const lines = text
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)

  const valid: string[] = []
  const invalid: string[] = []

  for (const line of lines) {
    const normalized = normalizePhoneNumber(line)
    if (normalized) {
      valid.push(normalized)
    } else {
      invalid.push(line)
    }
  }

  return { valid, invalid }
}

/**
 * 엑셀 파일에서 전화번호 추출 (변수 모드 지원) - ExcelJS 사용
 * @param file Excel 파일 객체
 * @returns Promise<string[] | Array<{phone: string, variables: Record<string, string>}>>
 */
const parseExcelFile = async (
  file: File,
): Promise<string[] | Array<{ phone: string; variables: Record<string, string> }>> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = async e => {
      try {
        const arrayBuffer = e.target?.result as ArrayBuffer

        // ExcelJS Workbook 생성
        const workbook = new ExcelJS.Workbook()
        await workbook.xlsx.load(arrayBuffer)

        // 첫 번째 워크시트 가져오기
        const worksheet = workbook.worksheets[0]

        if (!worksheet) {
          reject(new Error('엑셀 파일에 시트가 없습니다.'))
          return
        }

        // 모든 행을 배열로 변환
        const rows: any[][] = []
        worksheet.eachRow((row, rowNumber) => {
          const rowValues: any[] = []
          row.eachCell({ includeEmpty: true }, (cell, colNumber) => {
            rowValues.push(cell.value)
          })
          rows.push(rowValues)
        })

        // 변수 모드인 경우
        if (props.hasTemplateVariables && props.variableNames && props.variableNames.length > 0) {
          const result: Array<{ phone: string; variables: Record<string, string> }> = []

          if (rows.length === 0) {
            reject(new Error('엑셀 파일이 비어있습니다.'))
            return
          }

          // 헤더 행 검증
          const headerRow = rows[0]
          if (!headerRow || headerRow.length < 2) {
            reject(
              new Error('엑셀 파일 형식이 올바르지 않습니다. (최소 2개 열 필요: 전화번호 + 변수)'),
            )
            return
          }

          // 헤더에서 변수명 추출 (A열은 전화번호, B열부터 변수)
          const excelVariableNames: string[] = []
          for (let i = 1; i < headerRow.length; i++) {
            const varName = headerRow[i] ? String(headerRow[i]).trim() : ''
            if (varName) {
              excelVariableNames.push(varName)
            }
          }

          // 템플릿 변수와 엑셀 헤더 일치 확인
          const missingVars = props.variableNames.filter(v => !excelVariableNames.includes(v))
          if (missingVars.length > 0) {
            reject(
              new Error(
                `엑셀 헤더에 필요한 변수가 없습니다.\n필요한 변수: ${props.variableNames.join(', ')}\n엑셀 헤더: ${excelVariableNames.join(', ')}\n누락된 변수: ${missingVars.join(', ')}`,
              ),
            )
            return
          }

          // 데이터 행 순회 (헤더 다음 행부터)
          for (let i = 1; i < rows.length; i++) {
            const row = rows[i]

            // A열: 전화번호
            const phone = row[0] ? String(row[0]).trim() : ''
            if (!phone) continue

            // B열 이후: 변수 값
            const variables: Record<string, string> = {}
            for (let j = 1; j < headerRow.length; j++) {
              const varName = headerRow[j] ? String(headerRow[j]).trim() : ''
              const varValue = row[j] ? String(row[j]).trim() : ''
              if (varName) {
                variables[varName] = varValue
              }
            }

            result.push({ phone, variables })
          }

          resolve(result)
        } else {
          // 일반 모드 (변수 없음)
          const phoneNumbers: string[] = []
          let startRow = 0

          // 헤더 감지 (첫 번째 행에 문자열이 많으면 헤더로 판단)
          if (rows.length > 0) {
            const firstRow = rows[0]
            const hasHeader = firstRow.some(
              cell => typeof cell === 'string' && isNaN(Number(String(cell).replace(/[^\d]/g, ''))),
            )
            startRow = hasHeader ? 1 : 0
          }

          // 데이터 행 순회
          for (let i = startRow; i < rows.length; i++) {
            const row = rows[i]

            // A열 우선, B열 대체
            const cellA = row[0]
            const cellB = row[1]

            let phone: string | null = null

            // A열 확인
            if (cellA) {
              phone = String(cellA).trim()
            }

            // A열이 비어있으면 B열 확인
            if (!phone && cellB) {
              phone = String(cellB).trim()
            }

            if (phone) {
              phoneNumbers.push(phone)
            }
          }

          resolve(phoneNumbers)
        }
      } catch (error) {
        reject(error)
      }
    }

    reader.onerror = () => {
      reject(new Error('파일 읽기 실패'))
    }

    reader.readAsArrayBuffer(file)
  })
}

/**
 * 엑셀 파일 선택 시 자동 처리 (변수 모드 지원)
 * @param file 선택된 File 또는 File 배열
 */
const handleExcelFileChange = async (file: File | File[] | null) => {
  // 파일이 없으면 무시
  if (!file) {
    return
  }

  // File 배열인 경우 첫 번째 파일 선택
  const selectedFile = Array.isArray(file) ? file[0] : file

  if (!selectedFile) {
    return
  }

  // 파일 크기 확인 (10MB 제한)
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (selectedFile.size > maxSize) {
    refAlertModal.value?.callModal('파일 크기 초과', '파일 크기는 10MB 이하여야 합니다.')
    excelFileInput.value = null
    return
  }

  excelLoading.value = true

  try {
    // 엑셀 파일 파싱
    const extractedData = await parseExcelFile(selectedFile)

    // 변수 모드 처리
    if (props.hasTemplateVariables && props.variableNames && props.variableNames.length > 0) {
      const recipientsWithVars = extractedData as Array<{
        phone: string
        variables: Record<string, string>
      }>

      // 최대 개수 확인 (1,000개 제한)
      if (recipientsWithVars.length > 1000) {
        refAlertModal.value?.callModal(
          '전화번호 개수 초과',
          `추출된 전화번호가 ${recipientsWithVars.length}개입니다.\n최대 1,000개까지만 처리할 수 있습니다.`,
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 전화번호 없음
      if (recipientsWithVars.length === 0) {
        refAlertModal.value?.callModal(
          '전화번호 없음',
          '엑셀 파일에서 유효한 전화번호를 찾을 수 없습니다.',
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 전화번호 검증 및 포맷팅
      const validRecipientsWithVars: Array<{
        phone: string
        variables: Record<string, string>
      }> = []
      const invalid: string[] = []

      for (const item of recipientsWithVars) {
        const normalized = normalizePhoneNumber(item.phone)
        if (normalized) {
          validRecipientsWithVars.push({
            phone: normalized,
            variables: item.variables,
          })
        } else {
          invalid.push(item.phone)
        }
      }

      // 유효한 번호가 없는 경우
      if (validRecipientsWithVars.length === 0) {
        refAlertModal.value?.callModal(
          '유효한 전화번호 없음',
          `추출된 ${recipientsWithVars.length}개의 번호가 모두 유효하지 않습니다.\n\n올바른 형식:\n- 휴대폰: 010-1234-5678 (11자리)\n- 서울: 02-1234-5678 (9~10자리)\n- 지역: 031-123-4567 (9~10자리)`,
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 부모 컴포넌트에 변수 포함 수신자 전달
      emit('update:recipientsWithVariables', validRecipientsWithVars)

      // recipientsList도 업데이트 (전화번호만)
      const phones = validRecipientsWithVars.map(item => item.phone)
      recipientsList.value = phones as any

      // individualRecipients도 업데이트 (v-chip 표시를 위해)
      // 기존 수신자 초기화 후 새로운 수신자 추가
      individualRecipients.value = []
      recipientGroups.value = []
      individualRecipients.value.push(...phones)

      // 결과 메시지
      let message = `📊 변수 템플릿 엑셀 처리 결과:\n\n`
      message += `📁 파일명: ${selectedFile.name}\n`
      message += `📝 추출된 번호: ${recipientsWithVars.length}개\n`
      message += `📋 변수: ${props.variableNames.join(', ')}\n\n`
      message += `✅ 유효한 번호: ${validRecipientsWithVars.length}개\n`

      if (invalid.length > 0) {
        message += `❌ 유효하지 않은 번호: ${invalid.length}개\n`
        message += `\n유효하지 않은 번호 예시:\n${invalid.slice(0, 3).join('\n')}${invalid.length > 3 ? '\n...' : ''}`
      }

      refAlertModal.value?.callModal('엑셀 업로드 완료', message)
    } else {
      // 일반 모드 처리 (변수 없음)
      const extractedPhones = extractedData as string[]

      // 최대 개수 확인 (1,000개 제한)
      if (extractedPhones.length > 1000) {
        refAlertModal.value?.callModal(
          '전화번호 개수 초과',
          `추출된 전화번호가 ${extractedPhones.length}개입니다.\n최대 1,000개까지만 처리할 수 있습니다.`,
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 전화번호 없음
      if (extractedPhones.length === 0) {
        refAlertModal.value?.callModal(
          '전화번호 없음',
          '엑셀 파일에서 유효한 전화번호를 찾을 수 없습니다.',
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 전화번호 검증 및 포맷팅
      const { valid, invalid } = parseMultiplePhoneNumbers(extractedPhones.join('\n'))

      // 유효한 번호가 없는 경우
      if (valid.length === 0) {
        refAlertModal.value?.callModal(
          '유효한 전화번호 없음',
          `추출된 ${extractedPhones.length}개의 번호가 모두 유효하지 않습니다.\n\n올바른 형식:\n- 휴대폰: 010-1234-5678 (11자리)\n- 서울: 02-1234-5678 (9~10자리)\n- 지역: 031-123-4567 (9~10자리)`,
        )
        excelFileInput.value = null
        excelLoading.value = false
        return
      }

      // 중복 체크 및 필터링
      const allRecipients = recipientsList.value || []
      const newRecipients = valid.filter(phone => !allRecipients.includes(phone))
      const duplicates = valid.filter(phone => allRecipients.includes(phone))

      // 새로운 번호 추가
      if (newRecipients.length > 0) {
        individualRecipients.value.push(...newRecipients)
      }

      // 결과 메시지
      let message = `📊 엑셀 파일 처리 결과:\n\n`
      message += `📁 파일명: ${selectedFile.name}\n`
      message += `📝 추출된 번호: ${extractedPhones.length}개\n\n`

      if (newRecipients.length > 0) {
        message += `✅ 추가된 번호: ${newRecipients.length}개\n`
      }
      if (duplicates.length > 0) {
        message += `⚠️ 중복된 번호: ${duplicates.length}개\n`
      }
      if (invalid.length > 0) {
        message += `❌ 유효하지 않은 번호: ${invalid.length}개\n`
        message += `\n유효하지 않은 번호 예시:\n${invalid.slice(0, 3).join('\n')}${invalid.length > 3 ? '\n...' : ''}`
      }

      refAlertModal.value?.callModal('엑셀 업로드 완료', message)
    }
  } catch (error: any) {
    refAlertModal.value?.callModal(
      '파일 처리 오류',
      `파일을 처리하는 중 오류가 발생했습니다:\n${error.message}`,
    )
  } finally {
    excelFileInput.value = null
    excelLoading.value = false
  }
}

// v-expansion-panels 배경색 (다크 테마 대응)
const panelBgColor = computed(() => {
  return isDark?.value ? '#282933' : '#ffffff'
})

// v-expansion-panels 초기 활성 패널 (기본: 첫 번째 패널)
const activePanel = ref<number | null>(0)

// 변수 모드 활성화 시 엑셀 업로드 패널 자동 열기
watch(
  () => props.hasTemplateVariables,
  hasVariables => {
    if (hasVariables) {
      // 변수 모드 활성화 시 엑셀 업로드 패널(2번)로 전환
      activePanel.value = 2
    } else {
      // 변수 모드 해제 시 첫 번째 패널(0번)로 전환
      activePanel.value = 0
    }
  },
)

const handleAddRecipient = () => {
  const input = recipientInput.value
  if (!input) return

  // 여러 줄 파싱
  const { valid, invalid } = parseMultiplePhoneNumbers(input)

  // 유효한 번호가 없는 경우
  if (valid.length === 0) {
    if (invalid.length > 0) {
      refAlertModal.value?.callModal(
        '잘못된 전화번호',
        `유효하지 않은 번호:\n${invalid.join('\n')}\n\n올바른 형식:\n- 휴대폰: 010-1234-5678 (11자리)\n- 서울: 02-1234-5678 (9~10자리)\n- 지역: 031-123-4567 (9~10자리)`,
      )
    }
    return
  }

  // 중복 체크 및 필터링
  const allRecipients = recipientsList.value || []
  const newRecipients = valid.filter(phone => !allRecipients.includes(phone))
  const duplicates = valid.filter(phone => allRecipients.includes(phone))

  // 새로운 번호 추가
  if (newRecipients.length > 0) {
    individualRecipients.value.push(...newRecipients)
  }

  // 결과 메시지
  let message = ''
  if (newRecipients.length > 0) {
    message += `✅ ${newRecipients.length}개의 번호가 추가되었습니다.`
  }
  if (duplicates.length > 0) {
    message += `\n⚠️ ${duplicates.length}개의 번호는 이미 존재합니다.`
  }
  if (invalid.length > 0) {
    message += `\n❌ ${invalid.length}개의 번호는 형식이 올바르지 않습니다:\n${invalid.slice(0, 3).join('\n')}${invalid.length > 3 ? '\n...' : ''}`
  }

  if (message) {
    refAlertModal.value?.callModal('추가 결과', message)
  }

  // 입력 필드 초기화
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
        <!-- 변수 모드 안내 -->
        <v-alert
          v-if="hasTemplateVariables"
          type="info"
          color="primary"
          variant="tonal"
          class="mb-3"
          density="compact"
        >
          <strong>📋 변수 템플릿 모드</strong><br />
          선택한 템플릿에 변수가 포함되어 있습니다: <strong>{{ variableNames?.join(', ') }}</strong
          ><br />
          Excel 파일 업로드만 사용할 수 있습니다. (A열: 전화번호, B열 이후: 변수 값)
        </v-alert>

        <!-- 수신자 입력 방법 선택 -->
        <v-expansion-panels v-model="activePanel" class="mb-3" :bg-color="panelBgColor">
          <v-expansion-panel :disabled="!!hasTemplateVariables">
            <v-expansion-panel-title>
              <v-icon icon="mdi-account-plus" class="me-2" />
              개별 번호 입력
              <v-chip v-if="hasTemplateVariables" size="small" color="dark" class="ms-2">
                변수 모드에서 비활성화
              </v-chip>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <CRow class="align-items-end">
                <CCol cols="12" md="10">
                  <div class="d-flex justify-content-between align-items-center mb-1">
                    <label for="recipient-phone-input" class="form-label mb-0">휴대폰 번호</label>
                    <small v-if="recipientInput" class="text-muted">
                      {{ parseMultiplePhoneNumbers(recipientInput).valid.length }}개 유효 /
                      {{ parseMultiplePhoneNumbers(recipientInput).invalid.length }}개 무효
                    </small>
                  </div>
                  <textarea
                    id="recipient-phone-input"
                    v-model="recipientInput"
                    @keydown.shift.enter="handleAddRecipient"
                    @keydown.ctrl.enter="handleAddRecipient"
                    rows="3"
                    placeholder="휴대전화 번호를 입력하세요. (직접 입력 또는 엑셀 메모장 붙여넣기)
한 줄에 하나씩 여러 줄을 입력하여 한번에 발송할 수 있습니다.
예: 010-1234-5678, 01012345678, 02-111-2222, 031-123-4567"
                    class="form-control"
                  />
                </CCol>
                <CCol cols="12" md="2">
                  <v-btn color="primary" @click="handleAddRecipient" prepend-icon="mdi-plus" block>
                    {{ recipientInput?.includes('\n') ? '일괄 추가' : '추가' }}
                  </v-btn>
                </CCol>
              </CRow>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <v-expansion-panel :disabled="!!hasTemplateVariables">
            <v-expansion-panel-title>
              <v-icon icon="mdi-account-group" class="me-2" />
              그룹 선택
              <v-chip v-if="hasTemplateVariables" size="small" color="dark" class="ms-2">
                변수 모드에서 비활성화
              </v-chip>
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
              <v-chip v-if="hasTemplateVariables" size="small" color="primary" class="ms-2">
                변수 모드에서 사용 가능
              </v-chip>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-file-input
                v-model="excelFileInput"
                label="Excel 파일 선택"
                accept=".xlsx,.xls"
                prepend-icon="mdi-file-excel"
                show-size
                :loading="excelLoading"
                :disabled="excelLoading"
                @update:model-value="handleExcelFileChange"
              />
              <div v-if="excelLoading" class="mt-2">
                <v-progress-linear indeterminate color="primary" />
                <small class="text-muted">파일을 처리하고 있습니다...</small>
              </div>

              <!-- 변수 모드 안내 -->
              <v-alert
                v-if="hasTemplateVariables"
                type="info"
                color="primary"
                variant="tonal"
                class="mt-2"
                density="compact"
              >
                <strong>📋 변수 템플릿 EXCEL 파일 형식 : </strong><br />
                <strong>A열 : </strong> 전화번호<br />
                <strong>B열 이후 : </strong> 변수 값 (헤더: {{ variableNames?.join(', ') }})<br />
                <strong>예시 : </strong><br />
                <code>
                  | 전화번호 | {{ variableNames?.[0] || '변수1' }} |
                  {{ variableNames?.[1] || '변수2' }} |
                </code>
                <br />
                <code>| 010-1234-5678 | 홍길동 | 1,000,000 |</code>
              </v-alert>

              <!-- 일반 모드 안내 -->
              <v-alert v-else type="info" variant="tonal" class="mt-2" density="compact">
                <strong>파일 형식:</strong> .xlsx, .xls (최대 10MB)<br />
                <strong>전화번호 위치:</strong> A열(우선) 또는 B열에 입력<br />
                <strong>자동 인식:</strong> 헤더 행 자동 감지 및 제외<br />
                <strong>최대 개수:</strong> 1,000개
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

<style>
/* 비활성화된 expansion-panel 가시성 개선 - global 스타일 */
.v-expansion-panel--disabled .v-expansion-panel-title {
  opacity: 1 !important;
}

/* 라이트 모드 - 비활성화 텍스트 */
.v-expansion-panel--disabled .v-expansion-panel-title,
.v-expansion-panel--disabled .v-expansion-panel-title .v-icon {
  color: rgba(0, 0, 0, 0.38) !important;
}

/* 다크모드 - 비활성화 텍스트 (모든 가능한 셀렉터) */
body[class*='dark'] .v-expansion-panel--disabled .v-expansion-panel-title,
body[class*='dark'] .v-expansion-panel--disabled .v-expansion-panel-title * {
  color: rgba(255, 255, 255, 0.5) !important;
}
</style>
