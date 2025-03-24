<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Link } from '@/store/types/docs'
import { useDocs } from '@/store/pinia/docs'
import { timeFormat } from '@/utils/baseMixins'
import { bgLight } from '@/utils/cssMixins'
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

const clearLink = () => {
  newLink.value.docs = null
  newLink.value.link = ''
  newLink.value.description = ''
  addLinkForm.value = false
}

// 파일 삭제 로직
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
            <span>{{ link.user }}, {{ timeFormat(link.created as string, false, '/') }}</span>
            <span class="ml-2">
              <!--              <router-link to="#" @click.prevent="editFormSet(link.pk as number)">-->
              <v-icon icon="mdi-pencil" size="16" color="secondary" />
              <v-tooltip activator="parent" location="top">변경</v-tooltip>
              <!--              </router-link>-->
            </span>
            <span class="ml-2">
              <router-link to="#" @click.prevent="delLinkConfirm(link.pk as number)">
                <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
                <v-tooltip activator="parent" location="top">삭제</v-tooltip>
              </router-link>
            </span>
            <!--            <span v-if="isEditForm === link.pk">-->
            <!--              <CRow>-->
            <!--                <CCol xs>-->
            <!--                  <CInputGroup size="sm" style="width: 250px">-->
            <!--                    <CFormInput :aria-describedby="`link-edit-${link.pk}`" />-->
            <!--                    &lt;!&ndash;                    @input="editFileChange($event)"&ndash;&gt;-->
            <!--                    <CInputGroupText :id="`link-edit-${link.pk}`"> 취소 </CInputGroupText>-->
            <!--                    &lt;!&ndash;                    :color="editFile.file ? 'info' : 'secondary'"&ndash;&gt;-->
            <!--                    &lt;!&ndash;                      @click="clearFile"&ndash;&gt;-->
            <!--                  </CInputGroup>-->
            <!--                </CCol>-->
            <!--                &lt;!&ndash;                <CCol v-if="editLink.file" xs>&ndash;&gt;-->
            <!--                &lt;!&ndash;                  <CInputGroup size="sm" style="width: 250px">&ndash;&gt;-->
            <!--                &lt;!&ndash;                    <CFormInput&ndash;&gt;-->
            <!--                &lt;!&ndash;                      v-model="editLink.description"&ndash;&gt;-->
            <!--                &lt;!&ndash;                      placeholder="부가적인 설명"&ndash;&gt;-->
            <!--                &lt;!&ndash;                      size="sm"&ndash;&gt;-->
            <!--                &lt;!&ndash;                    />&ndash;&gt;-->
            <!--                &lt;!&ndash;                    <CInputGroupText>&ndash;&gt;-->
            <!--                &lt;!&ndash;                      <v-icon icon="mdi-trash-can-outline" size="16" @click="clearLink('edit')" />&ndash;&gt;-->
            <!--                &lt;!&ndash;                    </CInputGroupText>&ndash;&gt;-->
            <!--                &lt;!&ndash;                  </CInputGroup>&ndash;&gt;-->
            <!--                &lt;!&ndash;                </CCol>&ndash;&gt;-->
            <!--                &lt;!&ndash;                <CCol v-if="editLink.file" xs>&ndash;&gt;-->
            <!--                &lt;!&ndash;                  <CButton color="success" size="sm" @click="linkChange(link.pk as number)">&ndash;&gt;-->
            <!--                &lt;!&ndash;                    변경&ndash;&gt;-->
            <!--                &lt;!&ndash;                  </CButton>&ndash;&gt;-->
            <!--                &lt;!&ndash;                  <CButton color="light" size="sm" @click="clearLink"> 취소 </CButton>&ndash;&gt;-->
            <!--                &lt;!&ndash;                </CCol>&ndash;&gt;-->
            <!--              </CRow>-->
            <!--            </span>-->
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
      <CButton color="success" size="sm" @click="createLink">추가</CButton>
      <CButton color="light" size="sm" @click="clearLink">취소</CButton>
    </CCol>
  </CRow>

  <ConfirmModal ref="refDelLink">
    <template #default>이 링크를 삭제 하시겠습니까?</template>
    <template #footer>
      <CButton color="warning" @click="linkDelete">삭제</CButton>
    </template>
  </ConfirmModal>
</template>
