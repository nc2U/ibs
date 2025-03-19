<script lang="ts" setup>
import { computed, ref } from 'vue'
import type { Link } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

defineProps({ docs: { type: Object, default: () => null } })

const attach = ref(true)
const form = ref({
  links: [],
})

const newLinks = ref<Link[]>([])

const newLinkNum = ref(1)
const newLinkRange = computed(() => range(0, newLinkNum.value))

const ctlLinkNum = (n: number) => {
  if (n + 1 >= newLinkNum.value) newLinkNum.value = newLinkNum.value + 1
  else newLinkNum.value = newLinkNum.value - 1
}

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const enableStore = (event: Event) => {
  const el = event.target as HTMLInputElement
  attach.value = !el.value
}
</script>

<template>
  <CRow>
    <CFormLabel for="title" class="col-form-label col-2">링크</CFormLabel>
    <CCol class="col-sm-10 col-xl-8">
      <CRow v-if="docs && (form.links as Link[]).length">
        <CAlert :color="AlertSecondary">
          <CCol>
            <CInputGroup v-for="(link, i) in form.links as Link[]" :key="link.pk" class="mb-2">
              <CFormInput
                :id="`docs-link-${link.pk}`"
                v-model="(form.links as Link[])[i].link"
                size="sm"
                placeholder="파일 링크"
                @input="enableStore"
              />
              <CInputGroupText id="basic-addon1" class="py-0">
                <CFormCheck
                  :id="`del-link-${link.pk}`"
                  v-model="(form.links as Link[])[i].del"
                  @input="enableStore"
                  label="삭제"
                />
              </CInputGroupText>
            </CInputGroup>
          </CCol>
        </CAlert>
      </CRow>

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
    </CCol>
  </CRow>
</template>
