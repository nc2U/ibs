<script setup lang="ts">
import { ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project'
import type { Role } from '@/store/types/work_project'

const props = defineProps<{
  visible: boolean
  role: Role | null
  maxOrder: number
  workManager: boolean
}>()

const emit = defineEmits(['close'])

const workStore = useWork()

const form = ref({
  pk: 0,
  name: '',
  assignable: true,
  issue_visible: 'PUB' as 'ALL' | 'PUB' | 'PRI' | 'NOP',
  user_visible: 'ALL' as 'ALL' | 'PRJ' | 'NOP',
  order: 1,
  permissions: [] as number[],
})

watch(
  () => props.visible,
  val => {
    if (val) {
      if (props.role) {
        form.value = { ...props.role }
      } else {
        form.value = {
          pk: 0,
          name: '',
          assignable: true,
          issue_visible: 'PUB',
          user_visible: 'ALL',
          order: props.maxOrder + 1,
          permissions: [],
        }
      }
    }
  },
)

const saveRole = async () => {
  if (form.value.pk) {
    await workStore.updateRole(form.value as Role)
  } else {
    await workStore.createRole(form.value as Role)
  }
  emit('close')
}
</script>

<template>
  <CModal :visible="visible" alignment="center" size="md" @close="emit('close')">
    <CModalHeader>
      <CModalTitle>{{ form.pk ? '역할 수정' : '새 역할' }}</CModalTitle>
    </CModalHeader>
    <CModalBody>
      <CForm>
        <div class="mb-3">
          <CFormLabel>이름</CFormLabel>
          <CFormInput v-model="form.name" required />
        </div>
        <div class="mb-3">
          <CFormCheck id="assignable" v-model="form.assignable" label="업무 위탁 권한" />
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
      </CForm>
    </CModalBody>
    <CModalFooter>
      <v-btn color="secondary" size="small" @click="emit('close')">취소</v-btn>
      <v-btn
        :color="form.pk ? 'success' : 'primary'"
        size="small"
        :disabled="!workManager"
        @click="saveRole"
        >저장</v-btn
      >
    </CModalFooter>
  </CModal>
</template>
