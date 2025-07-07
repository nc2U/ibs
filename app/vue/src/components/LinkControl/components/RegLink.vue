<script lang="ts" setup>
import { onBeforeMount, type PropType, ref } from 'vue'
import type { Link } from '@/store/types/docs.ts'

const props = defineProps({ link: { type: Object as PropType<Link>, required: true } })

const emit = defineEmits(['enable-store', 'link-change', 'link-delete'])

const form = ref<{ link: Link | null }>({
  link: null,
})

const linkChange = (event: Event, pk: number) => {
  const e = event.target as HTMLInputElement
  emit('link-change', { pk, link: e.value })
  emit('enable-store', event)
}

const handleDelete = () => {
  if (form.value.link) (form.value.link as Link).del = !(form.value.link as Link).del
  const del = (form.value.link as Link).del
  emit('link-delete', { pk: (form.value.link as Link)?.pk, del })
}

onBeforeMount(async () => {
  if (props.link) form.value.link = { ...props.link }
})
</script>

<template>
  <CFormInput
    v-model="(form.link as Link).link"
    :id="`docs-link-${link.pk}`"
    size="sm"
    placeholder="파일 링크"
    @input="linkChange($event, link.pk as number)"
  />

  <CInputGroupText id="basic-addon1" class="py-0">
    <CFormCheck
      v-model="(form.link as Link).del"
      :id="`del-link-${link.pk}`"
      label="삭제"
      @click="handleDelete"
    />
  </CInputGroupText>
</template>
