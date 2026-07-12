<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms.ts'
import { cutString, diffDate } from '@/utils/baseMixins'
import type { IssueRelation } from '@/store/types/work_issue.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import IssueDropDown from '@/views/_Work/Manages/Issues/components/IssueDropDown.vue'

defineProps({
  rel: { type: Object as PropType<IssueRelation>, required: true },
  type: { type: String as PropType<'선행업무' | '후행업무'>, required: true },
})

const emit = defineEmits(['delete-relation'])

const selected = ref<number | null>(null)

const route = useRoute()
const { can, PERM } = usePerms()
const delRelRef = ref()

const deleteRelation = () => {
  delRelRef.value.callModal()
}

const deleteRelConfirm = () => {
  emit('delete-relation')
  delRelRef.value.close()
}

const projId = route.params.projId as string
const detailRouteName = projId ? '(업무) - 보기' : '업무 - 보기'
const detailRouteParams = (id: number) => (projId ? { projId, issueId: id } : { issueId: id })
</script>

<template>
  <CRow
    v-if="rel.issue"
    class="rel-issue cursor-menu"
    :class="{ 'bg-info-lighten': selected === rel.issue.pk }"
  >
    <CCol md="6" class="pt-1">
      <span>{{ type }} : </span>
      <span v-if="rel.issue">
        <router-link
          v-if="can(PERM.ISSUE_READ)"
          :to="{ name: detailRouteName, params: detailRouteParams(rel.issue.pk) }"
        >
          {{ rel.issue.tracker.name }} #{{ rel.issue.pk }}
        </router-link>
        <span v-else>{{ rel.issue.tracker.name }} #{{ rel.issue.pk }}</span>
        : {{ rel.issue.subject }}
      </span>
    </CCol>

    <CCol class="col-sm-8 col-md-3 text-right pt-1">
      <span class="mr-3">{{ rel.issue.status }}</span>
      <span class="mr-3" v-if="rel.issue.assigned_to">
        담당자 :
        <router-link :to="{ name: '사용자 - 보기', params: { userId: rel.issue.assigned_to?.pk } }">
          {{ cutString(rel.issue.assigned_to?.username, 9) }}
        </router-link>
      </span>
      <span class="mr-3">{{ rel.issue.start_date }}</span>
      <span
        class="mr-3"
        :class="{ 'text-danger': rel.issue.due_date && diffDate(rel.issue.due_date) > 0 }"
      >
        {{ rel.issue.due_date }}
      </span>
    </CCol>
    <CCol class="col-sm-4 col-md-3 text-right">
      <span v-if="rel.issue">
        <CProgress
          color="green-lighten-3"
          :value="rel.issue.done_ratio"
          style="width: 100px; float: left; margin-top: 7px"
          height="14"
        />
      </span>
      <v-btn v-if="can(PERM.ISSUE_REL_MANAGE)" variant="plain" size="small" @click="deleteRelation">
        <v-icon icon="mdi-link-variant-off" size="16" />
        <v-tooltip activator="parent" location="start">관계 지우기</v-tooltip>
      </v-btn>
      <span v-if="can(PERM.ISSUE_SUB_MANAGE)">
        <IssueDropDown :issue="rel.issue" />
      </span>
    </CCol>
  </CRow>

  <ConfirmModal ref="delRelRef">
    <template #header>연결된 업무 관계 삭제</template>
    <template #default> 연결된 업무의 관계를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteRelConfirm">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
