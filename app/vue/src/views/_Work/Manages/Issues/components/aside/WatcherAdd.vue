<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useWork } from '@/store/pinia/work'
import { useAccount } from '@/store/pinia/account'
import type { IssueProject } from '@/store/types/work'
import Multiselect from '@vueform/multiselect'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  watchers: { type: Array as PropType<{ pk: number; username: string }[]>, default: () => [] },
})

const emit = defineEmits(['watcher-add-submit'])

const addUser = ref()
const refConfirmModal = ref()

const addUsers = ref<number[]>([])
const addMembers = ref<{ pk: number; username: string }[]>([])

const userAdding = () => {
  const user = getUsers.value
    .filter(u => u.value === addUser.value)
    .map(u => ({
      pk: u.value,
      username: u.label,
    }))[0]
  addMembers.value.push(user)
  addUser.value = null
}

const workStore = useWork()
const iProject = inject<ComputedRef<IssueProject>>('iProject')

const members = computed(() =>
  (iProject?.value ? iProject?.value?.all_members : workStore?.memberList)?.map(m => m.user),
) // 기본 멤버리스트

const accStore = useAccount()
const getUsers = computed(() =>
  accStore.getUsers.filter(
    u =>
      !members.value?.map(m => m.pk).includes(u.value) &&
      !props.watchers.map(w => w.pk).includes(u.value) &&
      !addMembers.value.map(m => m.pk).includes(u.value),
  ),
) // 전체 유저에서 기본 멤버리스트 제외 목록

const memberList = computed(() =>
  members.value?.filter(m => !props.watchers.map(m => m.pk).includes(m.pk)),
) // 기본 멤버리스트에서 관람자 리스트 제외 목록

watch(
  () => memberList.value,
  nVal => (addMembers.value = nVal ?? []),
)

const callModal = () => refConfirmModal.value.callModal()
defineExpose({ callModal })

const watcherAddSubmit = () => {
  emit('watcher-add-submit', [...addUsers.value])
  refConfirmModal.value.close()
}

onBeforeMount(() => {
  accStore.fetchUsersList()
  addMembers.value = memberList.value ?? []
})
</script>

<template>
  <ConfirmModal ref="refConfirmModal">
    <template #header>업무 관람자 추가</template>

    <template #default>
      <Multiselect v-model="addUser" :options="getUsers" searchable placeholder="사용자 찾기" />

      <CRow v-if="addUser">
        <CCol class="text-right pt-3 mr-2">
          <v-btn color="info" size="small" @click="userAdding">목록추가</v-btn>
        </CCol>
      </CRow>

      <CRow class="mt-3">
        <CCol>
          <CFormCheck
            v-model="addUsers"
            v-for="mem in addMembers"
            :value="mem.pk"
            :id="`member-${mem.pk}`"
            :label="mem.username"
            :key="mem.pk"
            inline
          />
        </CCol>
      </CRow>
    </template>

    <template #footer>
      <v-btn color="primary" size="small" :disabled="!addUsers.length" @click="watcherAddSubmit">
        추가
      </v-btn>
    </template>
  </ConfirmModal>
</template>
