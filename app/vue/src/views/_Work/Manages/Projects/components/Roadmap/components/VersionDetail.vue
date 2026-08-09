<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import type { Version } from '@/store/types/work_project.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import VersionSummary from './automics/VersionSummary.vue'
import VersionIssuesTable from './automics/VersionIssuesTable.vue'

const props = defineProps({ version: { type: Object as PropType<Version>, required: true } })

// 권한 설정 추가
const { can, PERM } = usePerms()
const canManageVersions = computed(() => can(PERM.PROJECT_VERSION))

const workStore = useWork()

const boxClass = ['primary-box', 'danger-box', 'success-box']



const closedNum = computed(() => props.version?.issues?.filter(i => i.closed).length ?? 0)
const closedStr = computed(() => {
  if (closedNum.value === 0) return '모두 미완료'
  else if (closedNum.value === 1) return '한 건 완료'
  else return `${closedNum.value} 건 완료`
})

const progressNum = computed(() => props.version?.issues?.filter(i => !i.closed).length ?? 0)
const progressStr = computed(() => {
  if (progressNum.value === 0) return '모두 완료'
  else if (progressNum.value === 1) return '한 건 진행 중'
  else return `${progressNum.value} 건 진행 중`
})

const done_ratio = computed(() => {
  const done_sum = props.version.issues?.reduce((sum, issue) => sum + issue.done_ratio, 0) ?? 0

  if (!props.version?.issues?.length) return 0
  else return Math.round(done_sum / props.version?.issues?.length)
})

const [route, router] = [useRoute(), useRouter()]

const RefVersionConfirm = ref()

const deleteSubmit = () => {
  RefVersionConfirm.value.close()
  workStore.deleteVersion(props.version?.pk as number, props.version.project?.slug as string)
  router.replace({ name: '(로드맵)' })
}

onBeforeMount(() => {
  workStore.fetchVersion(Number(route.params.verId))
})
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="title bold mr-2" style="font-size: 1.4em">{{ version?.name }}</span>
      <span :class="boxClass[Number(version?.status) - 1]">{{ version?.status_desc }}</span>
    </CCol>

    <CCol class="text-right form-text">
      <span v-if="canManageVersions" class="mr-3">
        <v-icon icon="mdi-pencil" color="amber" size="16" class="mr-1" />
        <router-link :to="{ name: '(로드맵) - 수정', params: { verId: version?.pk } }">
          편집
        </router-link>
      </span>
      <span v-if="canManageVersions" class="mr-3">
        <v-icon icon="mdi-trash-can-outline" color="grey" size="16" class="mr-1" />
        <router-link
          to=""
          @click="
            RefVersionConfirm.callModal('', '이 단계 삭제를 계속 진행 하시겠습니까?', '', 'warning')
          "
        >
          삭제
        </router-link>
      </span>
      <span v-if="canManageVersions" class="mr-3">
        <v-icon icon="mdi-plus-circle" color="success" size="16" class="mr-1" />
        <router-link :to="{ name: '(업무) - 추가', query: { version: version?.pk } }">
          새 업무
        </router-link>
      </span>
    </CCol>
  </CRow>

  <CRow v-if="version?.description" class="mb-2">
    <CCol>{{ version?.description }}</CCol>
  </CRow>

  <template v-if="!version?.issues?.length">
    <div class="form-text mb-3">이 단계에 해당하는 업무 없음</div>
  </template>

  <template v-else>
    <CRow>
      <CCol class="col-sm-10 col-md-8 col-lg-6 col-xl-4 p-0 mx-2">
        <CProgress color="success" :value="done_ratio" :style="{ '--cui-border-radius': 0 }">
          {{ done_ratio.toFixed(0) }}%
        </CProgress>
      </CCol>
    </CRow>

    <CRow class="mb-4">
      <CCol class="form-text">
        <span>
          <router-link :to="{ name: '(업무)', query: { status: 'any' } }">
            업무 {{ version?.issues?.length }} 건
          </router-link>
        </span>
        <span>
          (<router-link :to="{ name: '(업무)', query: { status: 'closed' } }">
            {{ closedStr }}
          </router-link>
          -
        </span>
        <span>
          <router-link :to="{ name: '(업무)', query: { status: 'open' } }">
            {{ progressStr }} </router-link
          >)
        </span>
      </CCol>
    </CRow>

    <CRow class="flex-md-row flex-column-reverse">
      <CCol md="8" class="mb-4">
        <VersionIssuesTable :issues="version?.issues ?? []" />
      </CCol>

      <CCol md="4" class="mb-4">
        <VersionSummary :issues="version?.issues ?? []" />
      </CCol>
    </CRow>
  </template>

  <ConfirmModal ref="RefVersionConfirm">
    <template #footer>
      <v-btn color="warning" @click="deleteSubmit">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
