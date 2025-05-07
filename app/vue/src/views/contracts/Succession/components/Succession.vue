<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { type Succession } from '@/store/types/contract'
import { useRouter } from 'vue-router'

const props = defineProps({
  succession: { type: Object as PropType<Succession>, required: true },
})
const emit = defineEmits(['call-form', 'done-alert'])

const done = computed(() => props.succession.is_approval)
const buttonColor = computed(() => (!done.value ? 'success' : 'secondary'))

const router = useRouter()

const callFormModal = () => {
  if (!done.value) {
    router.replace({
      name: '권리 의무 승계',
      query: { contractor: props.succession?.buyer.pk },
    })
    setTimeout(() => {
      emit('call-form', props.succession)
    }, 300)
  } else emit('done-alert')
}
</script>

<template>
  <CTableDataCell class="text-center">
    <router-link to="" @click="callFormModal">
      {{ succession.contract.serial_number }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <router-link to="" @click="callFormModal">
      {{ succession.seller.name }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <router-link to="" @click="callFormModal">
      {{ succession.buyer.name }}
    </router-link>
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ succession.apply_date }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    {{ succession.trading_date }}
  </CTableDataCell>
  <CTableDataCell class="text-primary text-center fw-bold">
    {{ succession.approval_date }}
  </CTableDataCell>
  <CTableDataCell class="text-primary text-center fw-bold">
    {{ done ? '완료' : '' }}
  </CTableDataCell>
  <CTableDataCell class="text-center">
    <v-btn type="button" :color="buttonColor" size="small" @click="callFormModal"> 확인</v-btn>
  </CTableDataCell>
</template>
