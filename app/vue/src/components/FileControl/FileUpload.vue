<script lang="ts" setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['file-upload'])

const newFileNum = ref(1)
const newFileRange = computed(() => range(0, newFileNum.value))

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const ctlFileNum = (n: number) => {
  if (n + 1 >= newFileNum.value) newFileNum.value = newFileNum.value + 1
  else newFileNum.value = newFileNum.value - 1
}

const fileUpload = (event: Event) => {
  const el = event.target as HTMLInputElement
  if (el.files) {
    const file = el.files[0]
    emit('file-upload', file)
  }
}
</script>

<template>
  <CRow class="mb-2">
    <CCol>
      <CInputGroup v-for="fNum in newFileRange" :key="`fn-${fNum}`" class="mb-2">
        <CFormInput :id="`file-${fNum}`" type="file" @input="fileUpload" />
        <CInputGroupText id="basic-addon2" @click="ctlFileNum(fNum)">
          <v-icon
            :icon="`mdi-${fNum + 1 < newFileNum ? 'minus' : 'plus'}-thick`"
            :color="fNum + 1 < newFileNum ? 'error' : 'primary'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>
</template>
