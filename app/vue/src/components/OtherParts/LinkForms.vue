<script lang="ts" setup>
import { nextTick, onBeforeMount, type PropType, ref, watch } from 'vue'
import type { Link } from '@/store/types/docs'
import { AlertSecondary } from '@/utils/cssMixins'

const props = defineProps({
  label: { type: String, default: '링크' },
  links: { type: Array as PropType<Link[]>, default: () => [] },
})

const emit = defineEmits(['links-update', 'new-link-push'])

const form = ref<{ links: Link[] }>({ links: [] })

const formUpdate = () => nextTick(() => emit('links-update', form.value.links))

let linkSlotSeq = 1
const newLinkSlots = ref<{ id: number; value: string }[]>([{ id: linkSlotSeq++, value: '' }])

const ctlLinkNum = (idx: number) => {
  if (idx + 1 >= newLinkSlots.value.length) {
    newLinkSlots.value.push({ id: linkSlotSeq++, value: '' })
  } else {
    newLinkSlots.value.splice(idx, 1)
  }
}

const getNewLinks = (): string[] => newLinkSlots.value.map(s => s.value.trim()).filter(Boolean)

const clearNewLinks = () => {
  newLinkSlots.value = [{ id: linkSlotSeq++, value: '' }]
}

const newLinkPush = () => {
  const validLinks = getNewLinks()
  emit('new-link-push', validLinks)
  clearNewLinks()
}

defineExpose({ newLinkPush, getNewLinks, clearNewLinks })

const dataSetup = () => {
  if (props.links) {
    form.value.links = props.links.map(link => ({
      ...link,
      del: false,
    }))
  }
  formUpdate()
}

watch(
  () => props.links,
  () => dataSetup(),
  { deep: true },
)

onBeforeMount(() => dataSetup())
</script>

<template>
  <CRow>
    <CFormLabel for="title" class="col-form-label col-2 text-end">{{ label }}</CFormLabel>
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
              <CInputGroupText class="py-0">
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
          <CInputGroup v-for="(slot, idx) in newLinkSlots" :key="`ln-${slot.id}`" class="mb-2">
            <CFormInput :id="`link-${slot.id}`" v-model="slot.value" placeholder="파일 링크" />
            <CInputGroupText class="pointer" @click="ctlLinkNum(idx)">
              <v-icon
                :icon="`mdi-${idx + 1 < newLinkSlots.length ? 'minus' : 'plus'}-thick`"
                :color="idx + 1 < newLinkSlots.length ? 'error' : 'primary'"
              />
            </CInputGroupText>
          </CInputGroup>
        </CCol>
      </CRow>
    </CCol>
  </CRow>
</template>
