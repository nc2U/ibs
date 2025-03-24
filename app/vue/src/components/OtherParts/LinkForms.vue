<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, onBeforeUpdate, type PropType, ref } from 'vue'
import type { Link } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

const props = defineProps({ links: { type: Array as PropType<Link[]>, default: () => [] } })

const emit = defineEmits(['links-update', 'new-link-push'])

const form = ref<{ links: Link[] }>({
  links: [],
})

const formUpdate = () => nextTick(() => emit('links-update', form.value.links))

const range = (from: number, to: number): number[] =>
  from < to ? [from, ...range(from + 1, to)] : []

const newLinks = ref<Link[]>([])

const newLinkNum = ref(1)
const newLinkRange = computed(() => range(0, newLinkNum.value))

const ctlLinkNum = (n: number) => {
  if (n + 1 >= newLinkNum.value) newLinkNum.value = newLinkNum.value + 1
  else newLinkNum.value = newLinkNum.value - 1
}

const dataSetup = () => {
  if (props.links) form.value.links = props.links
  formUpdate()
}

const newLinkPush = () => {
  emit('new-link-push', newLinks.value)
  newLinks.value = []
  newLinkNum.value = 1
}
defineExpose({ newLinkPush })

onBeforeUpdate(() => dataSetup())
onBeforeMount(() => dataSetup())
</script>

<template>
  <CRow>
    <CFormLabel for="title" class="col-form-label col-2 text-right">링크</CFormLabel>
    <CCol class="col-sm-10 col-xl-8">
      <CRow v-if="(links as Link[]).length">
        <CAlert :color="AlertSecondary">
          <CCol>
            <CInputGroup v-for="(link, i) in links as Link[]" :key="link.pk" class="mb-2">
              <CFormInput
                :id="`docs-link-${link.pk}`"
                v-model="(form.links as Link[])[i].link"
                size="sm"
                placeholder="파일 링크"
              />
              <CInputGroupText id="basic-addon1" class="py-0">
                <CFormCheck
                  :id="`del-link-${link.pk}`"
                  v-model="(form.links as Link[])[i].del"
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
            <CFormInput :id="`link-${lNum}`" v-model="newLinks[lNum]" placeholder="파일 링크" />
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
