<script setup lang="ts">
import { ref, watch } from 'vue'
import { isValidate } from '@/utils/helper.ts'
import { useWork } from '@/store/pinia/work_project'
import type { Role } from '@/store/types/work_project'
import { CModal } from '@coreui/vue'

const props = defineProps<{
  visible: boolean
  role: Role | null
  maxOrder: number
  workManager: boolean
}>()

const emit = defineEmits(['close'])

const validated = ref(false)

const workStore = useWork()

const form = ref({
  pk: 0,
  name: '',
  assignable: true,
  issue_visible: 'PUB' as 'ALL' | 'PUB' | 'PRI' | 'NOP',
  user_visible: 'ALL' as 'ALL' | 'PRJ' | 'NOP',
  category: 'work_core' as 'work_core' | 'ibs_global',
  order: 1,
  permissions: [] as number[],
})

watch(
  () => props.visible,
  val => {
    if (val) {
      if (props.role) {
        form.value = {
          pk: props.role.pk,
          name: props.role.name,
          assignable: props.role.assignable,
          issue_visible: props.role.issue_visible,
          user_visible: props.role.user_visible,
          category: props.role.category || 'work_core',
          order: props.role.order,
          permissions: props.role.permissions || [],
        }
      } else {
        form.value = {
          pk: 0,
          name: '',
          assignable: true,
          issue_visible: 'PUB',
          user_visible: 'ALL',
          category: 'work_core',
          order: props.maxOrder + 1,
          permissions: [],
        }
      }
    }
  },
)

const saveRole = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    if (form.value.pk) await workStore.updateRole(form.value as Role)
    else await workStore.createRole(form.value as Role)
    emit('close')
  }
}
</script>

<template>
  <CModal :visible="visible" alignment="center" size="md" @close="emit('close')">
    <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="saveRole">
      <CModalHeader>
        <CModalTitle>{{ form.pk ? '역할 수정' : '새 역할' }}</CModalTitle>
      </CModalHeader>
      <CModalBody>
        <div class="mb-3">
          <CFormLabel>이름</CFormLabel>
          <CFormInput v-model="form.name" placeholder="역할명을 입력하세요" required />
        </div>
        <div class="mb-3">
          <CFormCheck id="assignable" v-model="form.assignable" label="업무 할당 가능 여부" />
        </div>
        <div class="mb-3">
          <CFormLabel>업무 보기 권한</CFormLabel>
          <CFormSelect v-model="form.issue_visible">
            <option value="ALL">모든 업무</option>
            <option value="PUB">비공개 업무 제외</option>
            <option value="PRI">직접 생성 또는 담당한 업무</option>
            <option value="NOP">없음</option>
          </CFormSelect>
        </div>
        <div class="mb-3">
          <CFormLabel>사용자 보기 권한</CFormLabel>
          <CFormSelect v-model="form.user_visible">
            <option value="ALL">모든 활성 사용자</option>
            <option value="PRJ">보이는 프로젝트 사용자</option>
            <option value="NOP">없음</option>
          </CFormSelect>
        </div>
        <div class="mb-3">
          <CFormLabel>권한 구분(카테고리)</CFormLabel>
          <CFormSelect v-model="form.category">
            <option value="work_core">협업 및 업무 관리 권한 (work_core)</option>
            <option value="ibs_global">비즈니스 데이터 관리 권한 (ibs_global)</option>
          </CFormSelect>
        </div>
        <div class="mt-4">
          <CAlert color="info" class="py-2 small">
            <CIcon name="cil-info" class="me-2" />
            <span v-if="!form.pk">
              역할 생성 후 <strong>'권한 보고서'</strong> 탭에서 세부 권한을 설정할 수 있습니다.
            </span>
            <span v-else>
              이 역할의 세부 권한은 <strong>'권한 보고서'</strong> 탭에서 관리할 수 있습니다.
            </span>
          </CAlert>
        </div>
      </CModalBody>
      <CModalFooter>
        <v-btn
          type="submit"
          :color="form.pk ? 'success' : 'primary'"
          size="small"
          :disabled="!workManager"
        >
          저장
        </v-btn>
        <v-btn color="light" size="small" @click="emit('close')" flat>취소</v-btn>
      </CModalFooter>
    </CForm>
  </CModal>
</template>
