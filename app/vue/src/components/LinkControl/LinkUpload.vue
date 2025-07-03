<script lang="ts" setup>
import { computed, ref } from 'vue'
import type { Link } from '@/store/types/docs.ts'

const newLinks = ref<Link[]>([])

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newLinkNum = ref(1)
const newLinkRange = computed(() => range(0, newLinkNum.value))

const ctlLinkNum = (n: number) => {
  if (n + 1 >= newLinkNum.value) newLinkNum.value = newLinkNum.value + 1
  else newLinkNum.value = newLinkNum.value - 1
}

const enableStore = () => 1
</script>

<template>
  <CRow class="mb-2">
    <CCol>
      <CInputGroup v-for="lNum in newLinkRange" :key="`ln-${lNum}`" class="mb-2">
        <CFormInput
          :id="`link-${lNum}`"
          v-model="newLinks[lNum]"
          placeholder="파일 링크"
          @input="enableStore"
        />
        <CInputGroupText id="basic-addon1" @click="ctlLinkNum(lNum)">
          <v-icon
            :icon="`mdi-${lNum + 1 < newLinkNum ? 'minus' : 'plus'}-thick`"
            :color="lNum + 1 < newLinkNum ? 'error' : 'primary'"
          />
        </CInputGroupText>
      </CInputGroup>
    </CCol>
  </CRow>
</template>
