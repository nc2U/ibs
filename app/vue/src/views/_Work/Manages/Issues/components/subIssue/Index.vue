<script lang="ts" setup>
import { computed, ref, type PropType, watchEffect, onUnmounted } from 'vue'
import { cutString, getOverdueDays } from '@/utils/baseMixins'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import type { SubIssue } from '@/store/types/work_issue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import IssueDropDown from '@/views/_Work/Manages/Issues/components/IssueDropDown.vue'

const props = defineProps({ sub: { type: Object as PropType<SubIssue>, required: true } })

const emit = defineEmits(['unlink-sub-issue'])

const route = useRoute()
const { can, canViewUser, PERM } = usePerms()

const selected = ref<number | null>(null)

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null
  const closestSubIssue = target?.closest('.sub-issue')
  // 클릭한 대상이 .sub-issue 외부이거나, 혹은 다른 rel-issue 요소인 경우 선택 해제
  if (!closestSubIssue || closestSubIssue.id !== `sub-issue-${props.sub?.pk}`) {
    selected.value = null
  }
}

watchEffect(() => {
  if (selected.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const delSubRef = ref<InstanceType<typeof ConfirmModal> | null>(null)
const child = ref<number | null>(null)

const parentUnlink = (pk: number) => {
  child.value = pk
  delSubRef.value?.callModal()
}

const unlinkSubIssue = () => {
  emit('unlink-sub-issue', child.value)
  child.value = null
  delSubRef.value?.close()
}

const projId = computed(() => route.params.projId as string | undefined)
const targetProjSlug = computed(() => props.sub.project?.slug || projId.value)
const detailRouteName = computed(() => '(업무) - 보기')
const detailRouteParams = (id: number) => ({ projId: targetProjSlug.value, issueId: id })
</script>

<template>
  <CRow
    class="sub-issue cursor-menu"
    :id="`sub-issue-${sub.pk}`"
    :class="{ 'selected-row': selected === sub.pk }"
    @click="selected = sub.pk"
  >
    <CCol md="6" lg="4" class="pt-1">
      <router-link
        v-if="targetProjSlug && can(PERM.ISSUE_READ, targetProjSlug)"
        :to="{ name: detailRouteName, params: detailRouteParams(sub.pk) }"
        :class="{ closed: sub.closed }"
      >
        {{ sub.tracker?.name || '업무' }} #{{ sub.pk }}
      </router-link>
      <span v-else :class="{ closed: sub.closed }"
        >{{ sub.tracker?.name || '업무' }} #{{ sub.pk }}</span
      >
      : {{ sub.subject }}
    </CCol>

    <CCol class="col-sm-6 col-md-3 col-lg-4 text-end pt-1">
      <span class="me-3">{{ sub.status }}</span>
      <span v-if="sub.assigned_to" class="me-3">
        <router-link
          v-if="canViewUser(sub.assigned_to.pk)"
          :to="{ name: '사용자 - 보기', params: { userId: sub.assigned_to.pk } }"
        >
          {{ cutString(sub.assigned_to.username, 9) }}
        </router-link>
        <span v-else>{{ cutString(sub.assigned_to.username, 9) }}</span>
      </span>
      <span class="me-3">
        {{ sub?.start_date }}
      </span>
      <span class="me-3" :class="{ 'text-danger': getOverdueDays(sub.due_date) > 0 }">
        {{ sub.due_date }}
      </span>
    </CCol>

    <CCol class="col-sm-6 col-md-3 col-lg-4 text-end">
      <span class="me-3">
        <CProgress
          :color="sub.done_ratio === 100 ? 'success' : 'warning'"
          :value="sub?.done_ratio ?? 0"
          style="width: 100px; float: left; margin-top: 10px"
          height="10"
        />
      </span>
      <v-btn
        v-if="can(PERM.ISSUE_SUB_MANAGE, targetProjSlug)"
        variant="plain"
        class="me-3"
        @click="parentUnlink(sub.pk)"
      >
        <v-icon icon="mdi-link-variant-off" size="16" />
        <v-tooltip activator="parent" location="start"> 관계 지우기 </v-tooltip>
      </v-btn>
      <IssueDropDown :issue="sub" />
    </CCol>
  </CRow>

  <ConfirmModal ref="delSubRef">
    <template #header>하위 업무 관계 삭제</template>
    <template #default>상위 업무와의 관계를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" size="small" @click="unlinkSubIssue">확인</v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.selected-row {
  background-color: rgba(var(--v-theme-warning), 0.16);
}
</style>
