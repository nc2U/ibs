<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { useContract } from '@/store/pinia/contract'
import { type Contractor } from '@/store/types/contract'

const props = defineProps({
  isBlank: { type: Boolean, default: false },
  contractor: { type: Object as PropType<Contractor>, required: true },
})
const emit = defineEmits(['resume-form'])

const isSuccession = computed(
  () => !!props.contractor.succession && !props.contractor.succession.is_approval,
)

const alertColor = computed(() => {
  let aColor = 'info'
  if (isSuccession.value) aColor = 'success'
  else if (!!props.contractor.contractorrelease && props.contractor.status >= '3') aColor = 'danger'
  return aColor
})

const getStatus = (num: string) => {
  const status = [
    { code: '1', text: '청약' },
    { code: '2', text: '계약' },
    { code: '3', text: '해지신청' },
    { code: '4', text: '해지완료' },
  ]
  return status.filter(s => s.code === num).map(s => s.text)[0]
}

const contStore = useContract()
const removeContractor = () => {
  contStore.contract = null
  contStore.contractor = null
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
      <CCol class="text-right">
        <router-link v-if="!isBlank || !contractor.contract" to="">
          <v-icon icon="mdi mdi-close" @click="removeContractor" />
          <v-tooltip activator="parent" location="start"> 계약자 선택 해제</v-tooltip>
        </router-link>
        <a v-else href="javascript:void(0)">
          <v-icon
            icon="mdi mdi-refresh"
            size="large"
            color="primary"
            class="rotate"
            @click="resumeForm"
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
