<script lang="ts" setup>
import { type PropType, ref } from 'vue'
import type { Link } from '@/store/types/docs'
import { timeFormat } from '@/utils/baseMixins'

defineProps({ links: { type: Array as PropType<Link[]>, default: () => [] } })

const isEditForm = ref(false)
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
              <!--              <router-link to="#" @click.prevent="delFileConfirm(link.pk as number)">-->
              <v-icon icon="mdi-trash-can-outline" size="16" color="secondary" class="mr-2" />
              <v-tooltip activator="parent" location="top">삭제</v-tooltip>
              <!--              </router-link>-->
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
</template>
