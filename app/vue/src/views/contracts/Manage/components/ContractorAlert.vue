<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContract } from '@/store/pinia/contract'
import { type Contractor } from '@/store/types/contract'

const props = defineProps({
  isBlank: { type: Boolean, default: false },
  contractor: { type: Object as PropType<Contractor>, required: true },
  clearRoute: { type: String, required: true },
})
const emit = defineEmits(['resume-form'])

const router = useRouter()

const isSuccession = computed(
  () => !!props.contractor?.succession && props.contractor.succession.status !== '3',
)

const alertColor = computed(() => {
  let aColor = 'info'
  if (isSuccession.value) aColor = 'success'
  else if (!!props.contractor?.contractorrelease && props.contractor.status >= '3')
    aColor = 'danger'
  return aColor
})

const statusMap: Record<string, string> = {
  '1': '청약',
  '2': '계약',
  '3': '해지신청',
  '4': '해지완료',
}
const getStatus = (num: string) => statusMap[num] || '미정'

const contStore = useContract()
const clearContractor = () => {
  contStore.contract = null
  contStore.contractor = null
  contStore.contAddressList = []
  router.replace({ name: props.clearRoute }).catch(() => {})
}

const route = useRoute()
const resumeForm = () => {
  const { contractor } = route.query
  if (!!contractor) emit('resume-form', contractor)
}
</script>

<template>
  <CAlert :color="alertColor">
    <CRow>
      <CCol xs="10">
        <strong>
          <CIcon name="cilTask" />
          계약자명 :
          {{ contractor.__str__ }} :::::: 현재상태 : [{{ getStatus(contractor.status) }}]
          {{ isSuccession ? '-> (!!!-변경 인가 진행 중-!!!)' : '' }}
        </strong>
      </CCol>
      <CCol class="text-end">
        <span v-if="!isBlank || !contractor.contract">
          <v-icon icon="mdi-close" class="pointer" style="cursor: pointer" @click.stop="clearContractor" />
          <v-tooltip activator="parent" location="start"> 계약자 선택 해제</v-tooltip>
        </span>
        <a v-else href="#" @click.prevent="resumeForm">
          <v-icon
            icon="mdi-refresh"
            size="large"
            color="primary"
            class="rotate pointer"
            style="cursor: pointer"
          />
          <v-tooltip activator="parent" location="start"> 계약자 정보 채우기</v-tooltip>
        </a>
      </CCol>
    </CRow>
  </CAlert>
</template>

<style lang="scss" scoped>
.rotate {
  -webkit-animation: spin 3s linear infinite;
  -moz-animation: spin 3s linear infinite;
  animation: spin 3s linear infinite;
}

@-moz-keyframes spin {
  100% {
    -moz-transform: rotate(360deg);
  }
}

@-webkit-keyframes spin {
  100% {
    -webkit-transform: rotate(360deg);
  }
}

@keyframes spin {
  100% {
    -webkit-transform: rotate(360deg);
    transform: rotate(360deg);
  }
}
</style>
