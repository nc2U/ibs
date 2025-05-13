<script lang="ts" setup>
import { ref, reactive, computed, onBeforeMount, inject, type PropType } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { write_project } from '@/utils/pageAuth'
import type { OptionItem } from '@/store/types/project'
import Multiselect from '@/components/MultiSelect/index.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const props = defineProps({ optionItem: { type: Object as PropType<OptionItem>, required: true } })
const emit = defineEmits(['on-update', 'on-delete'])

const getTypes = inject('getTypes')

const form = reactive({
  types: [] as number[],
  opt_code: '' as string | null,
  opt_name: '',
  opt_desc: '' as string | null,
  opt_maker: '' as string | null,
  opt_price: null as null | number,
  opt_deposit: null as null | number,
  opt_balance: null as null | number,
})

const refAlertModal = ref()
const refConfirmModal = ref()

const formsCheck = computed(() => {
  const a = JSON.stringify(form.types) === JSON.stringify(props.optionItem.types)
  const b = form.opt_code === props.optionItem.opt_code
  const c = form.opt_name === props.optionItem.opt_name
  const d = form.opt_desc === props.optionItem.opt_desc
  const e = form.opt_maker === props.optionItem.opt_maker
  const f = form.opt_price === props.optionItem.opt_price
  const g = form.opt_deposit === props.optionItem.opt_deposit
  const h = form.opt_balance === props.optionItem.opt_balance
  return a && b && c && d && e && f && g && h
})

const formCheck = (bool: boolean) => {
  if (bool) onUpdateOption()
  return
}

const onUpdateOption = () => {
  if (write_project.value) {
    const pk = props.optionItem.pk
    emit('on-update', { ...{ pk }, ...form })
  } else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const onDeleteOption = () => {
  if (useAccount().superAuth) refConfirmModal.value.callModal()
  else {
    refAlertModal.value.callModal()
    dataSetup()
  }
}
const modalAction = () => {
  emit('on-delete', props.optionItem.pk)
  refConfirmModal.value.close()
}
const dataSetup = () => {
  form.types = props.optionItem.types
  form.opt_code = props.optionItem.opt_code
  form.opt_name = props.optionItem.opt_name
  form.opt_desc = props.optionItem.opt_desc
  form.opt_maker = props.optionItem.opt_maker
  form.opt_price = props.optionItem.opt_price
  form.opt_deposit = props.optionItem.opt_deposit
  form.opt_balance = props.optionItem.opt_balance
}

onBeforeMount(() => dataSetup())
</script>

<template>
  <CTableRow>
    <CTableDataCell>
      <Multiselect
        mode="multiple"
        v-model="form.types"
        :options="getTypes"
        placeholder="타입구분"
        :classes="{ search: 'form-control multiselect-search' }"
        appendToBody
        required
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.opt_code"
        maxlength="20"
        placeholder="품목 코드"
        @keypress.enter="formCheck(form.opt_code !== optionItem.opt_code)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.opt_name"
        maxlength="100"
        placeholder="품목 이름"
        required
        @keypress.enter="formCheck(form.opt_name !== optionItem.opt_name)"
      />
    </CTableDataCell>
    <CTableDataCell>
      <CFormInput
        v-model="form.opt_desc"
        maxlength="200"
        placeholder="세부 옵션"
        @keypress.enter="formCheck(form.opt_desc !== optionItem.opt_desc)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model="form.opt_maker"
        placeholder="제조사"
        @keypress.enter="formCheck(form.opt_maker !== optionItem.opt_maker)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_price"
        placeholder="옵션 가격"
        type="number"
        min="0"
        required
        @keypress.enter="formCheck(form.opt_price !== optionItem.opt_price)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_deposit"
        placeholder="계약금"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.opt_deposit !== optionItem.opt_deposit)"
      />
    </CTableDataCell>

    <CTableDataCell>
      <CFormInput
        v-model.number="form.opt_balance"
        placeholder="잔금"
        type="number"
        min="0"
        @keypress.enter="formCheck(form.opt_balance !== optionItem.opt_balance)"
      />
    </CTableDataCell>

    <CTableDataCell v-if="write_project" class="text-center pt-3">
      <v-btn color="success" size="x-small" :disabled="formsCheck" @click="onUpdateOption">
        수정
      </v-btn>
      <v-btn color="warning" size="x-small" @click="onDeleteOption">삭제</v-btn>
    </CTableDataCell>
  </CTableRow>

  <ConfirmModal ref="refConfirmModal">
    <template #header> 옵션 정보 삭제</template>
    <template #default> 이 유상 옵션 데이터를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="modalAction">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>
