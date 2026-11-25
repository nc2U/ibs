<script lang="ts" setup>
import { ref, type PropType, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useWork } from '@/store/pinia/work_project'
import type { IssueProject } from '@/store/types/work_project'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  project: { type: Object as PropType<IssueProject>, required: true },
})

const { can, canGlobal, PERM } = usePerms()
const canProjectCreate = computed(() => canGlobal(PERM.PROJECT_CREATE))
const canProjectDelete = computed(() => can(PERM.PROJECT_DELETE, props.project.slug))

const router = useRouter()
const workStore = useWork()

const RefProjectArchiveConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)
const RefProjectDeleteConfirm = ref<InstanceType<typeof ConfirmModal> | null>(null)
const idForDelete = ref('')

const toggleArchive = async () => {
  const res = await workStore.toggleProjectLock(props.project.slug)
  if (res) {
    RefProjectArchiveConfirm.value?.close()
  }
}

const onCopyProject = () => {
  router.push({ name: '워크스페이스 - 추가', query: { copy: props.project.pk } })
}

const openDeleteConfirm = () => {
  idForDelete.value = ''
  RefProjectDeleteConfirm.value?.callModal()
}

const projectDelete = async () => {
  if (idForDelete.value === props.project.slug) {
    const res = await workStore.deleteIssueProject(props.project.slug)
    if (res) {
      RefProjectDeleteConfirm.value?.close()
      idForDelete.value = ''
    }
  }
}
</script>

<template>
  <v-btn
    v-if="canProjectCreate || canProjectDelete"
    icon
    variant="text"
    size="x-small"
    color="grey-darken-1"
  >
    <v-icon icon="mdi-dots-horizontal" />
    <v-tooltip activator="parent" location="top">Actions</v-tooltip>
    <v-menu activator="parent" location="bottom start" transition="scale-transition">
      <v-list density="compact" class="py-1">
        <v-list-item v-if="canProjectDelete" @click="RefProjectArchiveConfirm?.callModal()">
          <template v-slot:prepend>
            <v-icon
              :icon="project.status === '9' ? 'mdi-lock-open-variant' : 'mdi-lock'"
              :color="project.status === '9' ? 'success' : 'warning'"
              size="x-small"
              class="me-2"
            />
            <v-list-item-title class="text-caption">
              {{ project.status === '9' ? '잠금보관 해제' : '잠금보관' }}
            </v-list-item-title>
          </template>
        </v-list-item>

        <v-list-item v-if="canProjectCreate" @click="onCopyProject">
          <template v-slot:prepend>
            <v-icon icon="mdi-content-copy" color="info" size="x-small" class="me-2" />
            <v-list-item-title class="text-caption">복사</v-list-item-title>
          </template>
        </v-list-item>

        <v-list-item v-if="canProjectDelete" @click="openDeleteConfirm">
          <template v-slot:prepend>
            <v-icon icon="mdi-trash-can-outline" color="error" size="x-small" class="me-2" />
            <v-list-item-title class="text-caption">삭제</v-list-item-title>
          </template>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-btn>

  <ConfirmModal ref="RefProjectArchiveConfirm">
    <template #icon>
      <v-icon
        :icon="project.status === '9' ? 'mdi-lock-open-variant' : 'mdi-lock'"
        :color="project.status === '9' ? 'success' : 'warning'"
        class="me-2"
      />
    </template>
    <template #header>
      {{ project.status === '9' ? '잠금보관 해제' : '잠금보관' }}
    </template>
    <template #default>
      <span v-if="project.status === '9'">
        '{{ project.name }}' 워크스페이스의 잠금보관을 해제하고 정상 상태로 다시 전환하시겠습니까?
      </span>
      <span v-else>
        '{{ project.name }}' 워크스페이스를 '잠금보관' 상태로 변경하고 모든 접근을 차단하시겠습니까?
      </span>
    </template>
    <template #footer>
      <v-btn
        :color="project.status === '9' ? 'success' : 'warning'"
        size="small"
        @click="toggleArchive"
      >
        확인
      </v-btn>
    </template>
  </ConfirmModal>

  <ConfirmModal ref="RefProjectDeleteConfirm">
    <template #icon>
      <v-icon icon="mdi-trash-can" color="error" class="me-2" />
    </template>
    <template #header>워크스페이스 삭제</template>
    <template #default>
      <div class="bg-warning-subtle p-4 text-center rounded">
        <h6>{{ project.name }}</h6>
        <p class="mb-1">이 워크스페이스를 삭제 처리하시겠습니까?</p>
        <p class="text-caption text-medium-emphasis mb-3">
          (단, 업무/회의/문서 이력이 존재하는 워크스페이스는 삭제되지 않고 '잠금보관' 처리됩니다.)
        </p>
        <p>
          진행하려면 이 워크스페이스의 식별자 (<strong>{{ project.slug }}</strong
          >)를 입력하여 주십시오.
        </p>
        <CRow>
          <CFormLabel :for="'identifier-' + project.pk" class="col-sm-2 col-form-label">
            식별자
          </CFormLabel>
          <CCol sm="10">
            <CFormInput v-model="idForDelete" :id="'identifier-' + project.pk" />
          </CCol>
        </CRow>
      </div>
    </template>
    <template #footer>
      <v-btn
        color="error"
        @click="projectDelete"
        size="small"
        :disabled="idForDelete !== project.slug"
      >
        삭제
      </v-btn>
    </template>
  </ConfirmModal>
</template>
