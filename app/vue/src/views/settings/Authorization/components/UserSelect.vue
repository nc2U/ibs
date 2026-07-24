<script lang="ts" setup>
import { ref, computed, nextTick, onBeforeMount, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { bgLight } from '@/utils/cssMixins'
import Multiselect from '@vueform/multiselect'

const props = defineProps({
  selUser: { type: Number, default: null },
})
const emit = defineEmits(['select-user', 'add-user-modal'])

const userId = ref<number | null>(null)

const accountStore = useAccount()
const userInfo = computed(() => accountStore.userInfo)
const superAuth = computed(() => accountStore.superAuth)
const getUsers = computed(() => accountStore.getUsers)

const allowGetUsers = computed(() =>
  userInfo.value?.is_superuser
    ? getUsers.value
    : getUsers.value.filter(u => u.value === userInfo.value?.pk),
)

const selectUser = () => nextTick(() => emit('select-user', userId.value))

onBeforeMount(() => {
  if (userInfo.value) userId.value = userInfo.value.pk as number
})

watch(
  () => props.selUser,
  newVal => {
    if (!!newVal) userId.value = newVal
    else userId.value = null
  },
)

const addUserModal = () => emit('add-user-modal')
</script>

<template>
  <CCallout color="dark" class="mb-4" :class="bgLight">
    <CRow class="align-items-center">
      <CCol lg="8" xl="6">
        <CRow class="m-1 align-items-center">
          <CFormLabel class="col-md-3 col-form-label fw-bold">사용자 선택</CFormLabel>
          <CCol>
            <Multiselect
              v-model="userId"
              :options="allowGetUsers"
              placeholder="사용자"
              autocomplete="label"
              :classes="{ search: 'form-control multiselect-search' }"
              :add-option-on="['enter', 'tab']"
              searchable
              @change="selectUser"
            />
          </CCol>
        </CRow>
      </CCol>
      <CCol xl="4" v-if="superAuth" class="text-end pt-1">
        <v-btn variant="tonal" color="primary" @click="addUserModal">사용자 생성</v-btn>
      </CCol>
    </CRow>
  </CCallout>

  <v-divider />
</template>
