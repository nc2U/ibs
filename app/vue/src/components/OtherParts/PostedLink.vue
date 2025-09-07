<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Link } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import { timeFormat } from '@/utils/baseMixins'
import { bgLight, btnLight } from '@/utils/cssMixins'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const props = defineProps({
  docs: { type: Number, required: true },
  links: { type: Array as PropType<Link[]>, default: () => [] },
})

const docStore = useDocs()

// 링크 폼 핸들링 로직
const addLinkForm = ref(false)

// 링크 생성 로직
const newLink = ref<Link>({
  docs: null,
  link: '',
  description: '',
})

const createLink = () => {
  newLink.value.docs = props.docs as number
  if (newLink.value.link) {
    if (!/^(https?:\/\/)/.test(newLink.value.link))
      newLink.value.link = `https://${newLink.value.link}`
    docStore.createLink({ ...newLink.value })
    clearLink()
  } else return
}

const clearLink = (mode: 'new' | 'edit' | 'all' = 'all') => {
  newLink.value.docs = null
  newLink.value.link = ''
  newLink.value.description = ''
  addLinkForm.value = false
  resetLink(mode)
}

// 링크 변경 로직
const isEditForm = ref<number | null>(null)
const editLink = ref<Link>({
  // pk: undefined,
  docs: null,
  link: '',
  description: '',
})

const resetLink = (mode: 'new' | 'edit' | 'all' = 'all') => {
  if (mode !== 'new') addLinkForm.value = false
  if (mode !== 'edit') isEditForm.value = null
  newLink.value.link = ''
  newLink.value.description = ''
  editLink.value.pk = undefined
  editLink.value.link = ''
  editLink.value.description = ''
}
const editFormSet = (pk: number) => {
  editLink.value.pk = pk
  isEditForm.value = isEditForm.value === pk ? null : pk
  resetLink('edit')
}

const linkUpdate = (pk: number) => {
  isEditForm.value = null
  if (editLink.value.link || editLink.value.description) {
    const link: { docs?: number; link?: string; description?: string } = {}
    link.docs = props.docs as number
    if (editLink.value.link) link.link = editLink.value.link
    if (editLink.value.description) link.description = editLink.value.description
    docStore.patchLink(pk, { ...link })
    console.log({ ...link })
  }
  resetLink()
}

// 링크 삭제 로직
const refDelLink = ref()
const delLinkPk = ref<number | null>(null)
const delLinkConfirm = (pk: number) => {
  delLinkPk.value = pk
  refDelLink.value.callModal()
}
const linkDelete = () => {
  if (delLinkPk.value) {
    docStore.deleteLink(delLinkPk.value as number, props.docs as number)
    delLinkPk.value = null
    refDelLink.value.close()
  }
}
</script>

<template>
  <CRow class="mb-3">
    <CCol>
      <table>
        <tr v-for="link in links" :key="link.pk as number">
          <td>
            <v-icon icon="mdi-link" size="sm" class="mr-2" />
            <a :href="link.link" target="_blank">{{ link.link }}</a>
          </td>
          <td class="px-2">{{ link.description }}</td>
          <td class="text-secondary">
            <span>{{ link.creator }}, {{ timeFormat(link.created as string, false, '/') }}</span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="editFormSet(link.pk as number)">
                <v-icon icon="mdi-pencil" size="16" color="secondary" />
                <v-tooltip activator="parent" location="top">변경</v-tooltip>
              </router-link>
            </span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="delLinkConfirm(link.pk as number)">
                <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
                <v-tooltip activator="parent" location="top">삭제</v-tooltip>
              </router-link>
            </span>
            <span v-if="isEditForm === link.pk">
              <CRow>
                <CCol xs>
                  <CFormInput
                    v-model="editLink.link"
                    size="sm"
                    inline
                    placeholder="변경할 파일링크"
                    @keydown.enter="linkUpdate(link.pk as number)"
                  />
                </CCol>
                <CCol xs>
                  <CFormInput
                    v-model="editLink.description"
                    inline
                    placeholder="부가적인 설명"
                    size="sm"
                    @keydown.enter="linkUpdate(link.pk as number)"
                  />
                </CCol>
                <CCol xs>
                  <v-btn color="success" size="small" @click="linkUpdate(link.pk as number)">
                    변경
                  </v-btn>
                  <v-btn :color="btnLight" size="small" @click="clearLink()"> 취소 </v-btn>
                </CCol>
              </CRow>
            </span>
          </td>
        </tr>
      </table>
    </CCol>
  </CRow>

  <CRow class="mb-2">
    <CCol>
      <router-link to="#" @click.prevent="addLinkForm = !addLinkForm">링크추가</router-link>
    </CCol>
  </CRow>

  <CRow v-if="addLinkForm" class="p-3 mb-3" :class="bgLight">
    <CCol>
      <CFormInput
        v-model="newLink.link"
        @keydown.enter="createLink"
        size="sm"
        placeholder="새 파일 링크"
      />
    </CCol>

    <CCol>
      <CFormInput
        v-model="newLink.description"
        @keydown.enter="createLink"
        size="sm"
        placeholder="부가적인 설명"
      />
    </CCol>
  </CRow>

  <CRow v-if="addLinkForm">
    <CCol>
      <v-btn color="success" size="small" @click="createLink">추가</v-btn>
      <v-btn :color="btnLight" size="small" @click="clearLink">취소</v-btn>
    </CCol>
  </CRow>

  <ConfirmModal ref="refDelLink">
    <template #default>이 링크를 삭제 하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="linkDelete">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
