<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watchEffect } from 'vue'
import type { Version } from '@/store/types/work'
import { useRoute, useRouter } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import IssueDropDown from '@/views/_Work/Manages/Issues/components/IssueDropDown.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import VersionSummary from '@/views/_Work/Manages/Projects/components/Roadmap/components/VersionSummary.vue'
import VersionTimes from '@/views/_Work/Manages/Projects/components/Roadmap/components/VersionTimes.vue'

const props = defineProps({ version: { type: Object as PropType<Version>, required: true } })

const workStore = useWork()

const boxClass = ['primary-box', 'danger-box', 'success-box']

const selectedRow = ref<number | null>(null)
const handleClickOutside = (event: any) => {
  if (!event.target.closest('.table-row')) selectedRow.value = null
}

watchEffect(() => {
  if (selectedRow.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

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
      <span class="mr-3">
        <v-icon icon="mdi-pencil" color="amber" size="16" class="mr-1" />
        <router-link :to="{ name: '(로드맵) - 수정', params: { verId: version?.pk } }">
          편집
        </router-link>
      </span>
      <span class="mr-3">
        <v-icon icon="mdi-trash-can-outline" color="grey" size="16" class="mr-1" />
        <router-link
          to=""
          @click="
            RefVersionConfirm.callModal('', '이 버전 삭제를 계속 진행 하시겠습니까?', '', 'warning')
          "
        >
          삭제
        </router-link>
      </span>
      <span class="mr-3">
        <v-icon icon="mdi-plus-circle" color="success" size="16" class="mr-1" />
        <router-link :to="{ name: '(로드맵) - 추가' }">새 업무 만들기</router-link>
      </span>
    </CCol>
  </CRow>

  <CRow v-if="version?.description" class="mb-2">
    <CCol>{{ version?.description }}</CCol>
  </CRow>

  <template v-if="!version?.issues?.length">
    <div class="form-text mb-3">이 버전에 해당하는 업무 없음</div>
  </template>

  <template v-else>
    <CRow>
      <CCol class="col-sm-10 col-md-8 col-lg-6 col-xl-4 p-0 mx-2">
        <CProgress color="success" :value="done_ratio" :style="{ '--cui-border-radius': 0 }">
          {{ done_ratio }}%
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
        <h6>연결된 업무</h6>
        <v-divider class="mb-0" />
        <CTable responsive hover small striped>
          <colgroup>
            <col style="width: 95%" />
            <col style="width: 5%" />
          </colgroup>
          <CTableBody>
            <CTableRow
              v-for="issue in version.issues"
              :key="issue.pk"
              class="table-row cursor-menu"
              :color="selectedRow === issue.pk ? 'primary' : ''"
              @click="selectedRow = issue.pk"
            >
              <CTableDataCell>
                <span>
                  <router-link
                    :to="{ name: '(업무) - 보기', params: { issueId: issue.pk } }"
                    :class="{ closed: issue.closed }"
                  >
                    기능 #{{ issue.pk }}
                  </router-link>
                </span>
                <span> : {{ issue.subject }}</span>
              </CTableDataCell>
              <CTableDataCell class="text-center p-0">
                <IssueDropDown :issue="issue" />
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>

      <CCol md="4" class="mb-4">
        <VersionTimes :issues="version.issues" :version-pk="version.pk as number" />

        <VersionSummary />
      </CCol>
    </CRow>
  </template>

  <ConfirmModal ref="RefVersionConfirm">
    <template #footer>
      <v-btn color="warning" @click="deleteSubmit">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
