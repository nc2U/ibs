<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import type { Version } from '@/store/types/work_project.ts'

const props = defineProps({ version: { type: Object as PropType<Version>, required: true } })

const { can, PERM } = usePerms()

const [route, router] = [useRoute(), useRouter()]
const projId = computed(() => (route.params.projId as string) || props.version.project?.slug || '')

const boxClass = ['primary-box', 'danger-box', 'success-box']

const closedNum = computed(() => props.version.closed_num ?? 0)
const closedStr = computed(() => {
  if (closedNum.value === 0) return '모두 미완료'
  else if (closedNum.value === 1) return '한 건 완료'
  else return `${closedNum.value} 건 완료`
})

const progressNum = computed(() => props.version.open_num ?? 0)
const progressStr = computed(() => {
  if (progressNum.value === 0) return '모두 완료'
  else if (progressNum.value === 1) return '한 건 진행 중'
  else return `${progressNum.value} 건 진행 중`
})

const done_ratio = computed(() => {
  // 백엔드에서 issue_stats가 포함되지 않은 경우를 대비한 안전장치
  return props.version.done_ratio ?? 0
})
</script>

<template>
  <CCol>
    <CRow class="mb-3">
      <CCol>
        <v-icon icon="mdi-star-box-multiple" color="amber" class="mr-2" />
        <span class="mr-2 bold" style="font-size: large">
          <router-link :to="{ name: '(로드맵) - 보기', params: { projId, verId: version.pk } }">
            {{ version.name }}
          </router-link>
        </span>

        <span :class="boxClass[Number(version.status) - 1]">
          {{ version.status_desc }}
        </span>
      </CCol>
      <CCol v-if="can(PERM.PROJECT_VERSION)" class="text-right">
        <!-- 관리자 권한 있을 때 렌더링 -->
        <v-icon
          icon="mdi-pencil"
          color="amber"
          size="18"
          @click="router.push({ name: '(로드맵) - 수정', params: { verId: version.pk } })"
        />
      </CCol>
    </CRow>

    <CRow v-if="version.description" class="mb-2">
      <CCol>{{ version.description }}</CCol>
    </CRow>

    <template v-if="version.total_num === 0">
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

      <!--      <CRow>-->
      <!--        <CCol class="mb-4">-->
      <!--          <h6>연결된 업무</h6>-->
      <!--          <v-divider class="mb-0" />-->
      <!--          <CTable responsive hover small striped>-->
      <!--            <colgroup>-->
      <!--              <col style="width: 95%" />-->
      <!--              <col style="width: 5%" />-->
      <!--            </colgroup>-->
      <!--            <CTableBody>-->
      <!--              <CTableRow v-for="issue in version.issues" :key="issue.pk">-->
      <!--                <CTableDataCell>-->
      <!--                  <span>-->
      <!--                    <router-link-->
      <!--                      :to="{ name: '(업무) - 보기', params: { issueId: issue.pk } }"-->
      <!--                      :class="{ closed: issue.closed }"-->
      <!--                    >-->
      <!--                      기능 #{{ issue.pk }}-->
      <!--                    </router-link>-->
      <!--                  </span>-->
      <!--                  <span> : {{ issue.subject }}</span>-->
      <!--                </CTableDataCell>-->
      <!--                <CTableDataCell class="text-center p-0">-->
      <!--                  <IssueDropDown :issue="issue" />-->
      <!--                </CTableDataCell>-->
      <!--              </CTableRow>-->
      <!--            </CTableBody>-->
      <!--          </CTable>-->
      <!--        </CCol>-->
      <!--      </CRow>-->
    </template>
  </CCol>
</template>
