<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useAccount } from '@/store/pinia/account.ts'
import type { Todo, TodoIssueInfo } from '@/store/types/accounts.ts'

const props = defineProps<{
  visible: boolean
  todo: Todo | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (
    e: 'converted',
    payload: {
      todo: Todo
      issue: TodoIssueInfo
    },
  ): void
}>()

const workStore = useWork()
const accountStore = useAccount()

const project = ref<number | ''>('')
const subject = ref('')
const description = ref('')
const submitting = ref(false)
const errorMessage = ref('')

const projectList = computed(() => {
  const myProjects = workStore.getMyActiveProjects
  if (myProjects && myProjects.length > 0) return myProjects
  return workStore.getAllActiveProjects
})

watch(
  () => props.visible,
  async isVisible => {
    if (isVisible) {
      errorMessage.value = ''
      submitting.value = false
      subject.value = props.todo?.title || ''
      description.value = ''

      // 프로젝트 목록 로드
      if (projectList.value.length === 0) {
        await workStore.fetchMyProjectsList()
        if (workStore.getMyActiveProjects.length === 0) {
          await workStore.fetchAllProjectList()
        }
      }

      // 기본 프로젝트 선택 (현재 선택된 워크스페이스나 첫 번째 프로젝트)
      if (workStore.currentProject?.pk) {
        project.value = workStore.currentProject.pk
      } else if (projectList.value.length > 0) {
        project.value = projectList.value[0].value
      } else {
        project.value = ''
      }
    }
  },
)

const close = () => {
  emit('update:visible', false)
}

const handleConvert = async () => {
  if (!props.todo?.pk) return
  if (!project.value) {
    errorMessage.value = '업무를 등록할 워크스페이스를 선택해 주세요.'
    return
  }
  if (!subject.value.trim()) {
    errorMessage.value = '업무 제목을 입력해 주세요.'
    return
  }

  submitting.value = true
  errorMessage.value = ''

  try {
    const res = await accountStore.convertTodoToIssue(props.todo.pk, {
      project: Number(project.value),
      subject: subject.value.trim(),
      description: description.value.trim(),
    })

    if (res && res.issue) {
      emit('converted', res)
      close()
    } else {
      errorMessage.value = '업무 전환 처리에 실패했습니다.'
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : ''
    errorMessage.value = msg || '업무 전환 중 오류가 발생했습니다.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <CModal :visible="visible" alignment="center" backdrop="static" @close="close">
    <CModalHeader>
      <CModalTitle class="fs-6 d-flex align-items-center">
        <v-icon icon="mdi-transfer-right" class="me-2 text-primary" size="20" />
        할 일을 업무(Issue)로 전환
      </CModalTitle>
    </CModalHeader>

    <CModalBody class="py-3 text-body">
      <p class="text-muted mb-3 small">
        개인 할 일을 워크스페이스 공식 업무로 등록합니다. 전환 완료 시 본 할 일은 자동으로 완료
        처리됩니다.
      </p>

      <CAlert v-if="errorMessage" color="danger" class="py-2 small">
        {{ errorMessage }}
      </CAlert>

      <div class="mb-3">
        <CFormLabel for="convert-project" class="small fw-semibold">
          대상 워크스페이스 <span class="text-danger">*</span>
        </CFormLabel>
        <CFormSelect id="convert-project" v-model.number="project" size="sm" :disabled="submitting">
          <option value="" disabled>워크스페이스를 선택하세요</option>
          <option v-for="p in projectList" :key="p.value" :value="p.value">
            {{ p.label }}
          </option>
        </CFormSelect>
      </div>

      <div class="mb-3">
        <CFormLabel for="convert-subject" class="small fw-semibold">
          업무 제목 <span class="text-danger">*</span>
        </CFormLabel>
        <CFormInput
          id="convert-subject"
          v-model="subject"
          size="sm"
          maxlength="100"
          placeholder="업무 제목을 입력하세요"
          :disabled="submitting"
          @keyup.enter="handleConvert"
        />
      </div>

      <div class="mb-2">
        <CFormLabel for="convert-desc" class="small fw-semibold">설명 (선택)</CFormLabel>
        <CFormTextarea
          id="convert-desc"
          v-model="description"
          size="sm"
          rows="3"
          placeholder="추가 세부 사항이나 메모를 입력하세요 (선택 사항)"
          :disabled="submitting"
        />
      </div>
    </CModalBody>

    <CModalFooter class="py-2">
      <CButton color="secondary" variant="ghost" size="sm" :disabled="submitting" @click="close">
        취소
      </CButton>
      <CButton color="primary" size="sm" :disabled="submitting || !project" @click="handleConvert">
        <CSpinner v-if="submitting" size="sm" class="me-1" />
        업무로 전환
      </CButton>
    </CModalFooter>
  </CModal>
</template>
