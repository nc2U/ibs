<script lang="ts" setup>
import { computed, onBeforeMount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useProject } from '@/store/pinia/project'
import { useWork } from '@/store/pinia/work_project'
import Multiselect from '@vueform/multiselect'

defineProps({ selectable: { type: Boolean, default: true } })
const emit = defineEmits(['proj-select'])

const { can, PERM } = usePerms()
const canProjectCreate = computed(() => can(PERM.PROJECT_CREATE))

const router = useRouter()
const route = useRoute()

const projStore = useProject()
const workStore = useWork()

const projectPk = computed(() => projStore.project?.pk)
const projSelectList = computed(() => workStore.getDevProjects)

const loadProject = async () => {
  const urlId = route.query.project ? parseInt(route.query.project as string, 10) : null
  const targetId = urlId || projStore.currentProject
  const allowedIds = projSelectList.value.map(p => p.value)

  if (targetId && allowedIds.includes(targetId)) await projStore.fetchProject(targetId)
}

// 1. 초기 데이터 로드 및 초기 프로젝트 설정
onBeforeMount(async () => {
  await projStore.fetchProjectList()

  // 데이터가 로드된 상태에 따라 바로 로드하거나 watch를 통해 대기
  if (projSelectList.value.length > 0) {
    await loadProject()
  } else {
    const unwatch = watch(
      () => projSelectList.value,
      newList => {
        if (newList.length > 0) {
          loadProject()
          unwatch() // 한 번만 실행하고 감시 종료
        }
      },
    )
  }
})
</script>

<template>
  <CRow class="m-0 align-items-center">
    <CFormLabel class="col-lg-1 col-form-label text-body">프로젝트</CFormLabel>
    <CCol md="6" lg="3">
      <Multiselect
        :value="projectPk"
        :options="projSelectList"
        placeholder="프로젝트선택"
        autocomplete="label"
        :classes="{ search: 'form-control multiselect-search' }"
        :add-option-on="['enter', 'tab']"
        searchable
        :disabled="!selectable"
        @select="emit('proj-select', $event)"
        @clear="emit('proj-select', null)"
      />
    </CCol>
    <CCol v-if="!projSelectList.length" class="pl-0 align-middle">
      <v-icon
        icon="mdi mdi-plus-thick"
        color="success"
        :disabled="!canProjectCreate"
        @click="router.push({ name: '프로젝트 등록' })"
      />
      <v-tooltip v-if="!canProjectCreate" activator="parent" location="end">
        프로젝트 생성 권한이 필요합니다.
      </v-tooltip>
    </CCol>
  </CRow>
</template>
