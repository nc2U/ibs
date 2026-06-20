<script lang="ts" setup>
import { ref, type PropType } from 'vue'
import { useRouter } from 'vue-router'
import { cutString, diffDate } from '@/utils/baseMixins'
import type { IssueRelation } from '@/store/types/work_issue.ts'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  rel: { type: Object as PropType<IssueRelation>, required: true },
  type: { type: String as PropType<'선행업무' | '후행업무'>, required: true },
})

const emit = defineEmits(['delete-relation'])
const router = useRouter()

const delRelRef = ref()

const deleteRelation = () => {
  delRelRef.value.callModal()
}

const deleteRelConfirm = () => {
  emit('delete-relation')
  delRelRef.value.close()
}
</script>

<template>
  <CRow class="rel-issue">
    <CCol md="6" class="pt-1">
      <span>{{ type }} : </span>
      <span>
        <router-link :to="{ name: '(업무) - 보기', params: { issueId: rel.issue?.pk } }">
          {{ rel.issue?.tracker }} #{{ rel.issue?.pk }}
        </router-link>
        : {{ rel.issue?.subject }}
      </span>
    </CCol>
    <CCol class="col-sm-8 col-md-3 text-right pt-1">
      <span class="mr-3">{{ rel.issue?.status }}</span>
      <span class="mr-3">
        <router-link :to="{ name: '사용자 - 보기', params: { userId: rel.issue?.assigned_to.pk } }">
          {{ cutString(rel.issue?.assigned_to.username, 9) }}
        </router-link>
      </span>
      <span class="mr-3">{{ rel.issue?.start_date }}</span>
      <span
        class="mr-3"
        :class="{ 'text-danger': rel.issue?.due_date && diffDate(rel.issue?.due_date) > 0 }"
      >
        {{ rel.issue?.due_date }}
      </span>
    </CCol>
    <CCol class="col-sm-4 col-md-3 text-right">
      <span>
        <CProgress
          color="green-lighten-3"
          :value="rel.issue?.done_ratio"
          style="width: 100px; float: left; margin-top: 7px"
          height="14"
        />
      </span>
      <span class="pointer" @click="deleteRelation">삭제</span>
    </CCol>
  </CRow>

  <ConfirmModal ref="delRelRef">
    <template #header>연결된 업무 관계 지우기</template>
    <template #default> 계속 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="deleteRelConfirm">확인</v-btn>
    </template>
  </ConfirmModal>
</template>
