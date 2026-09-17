<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { type SiteContract } from '@/store/types/project'
import { numFormat, humanizeFileSize } from '@/utils/baseMixins'
import { usePerms } from '@/composables/usePerms.ts'
import FormModal from '@/components/Modals/FormModal.vue'
import SiteContractForm from './SiteContractForm.vue'

const props = defineProps({
  contract: { type: Object as PropType<SiteContract>, required: true },
  isHighlight: { type: Boolean, default: false },
})

const emit = defineEmits(['multi-submit', 'on-delete'])

const { can, PERM } = usePerms()
const canSiteUpdate = computed(() => can(PERM.SITE_UPDATE))

const updateFormModal = ref()

const showDetail = () => updateFormModal.value.callModal()
const multiSubmit = (payload: SiteContract) => emit('multi-submit', payload)
const onDelete = (payload: { pk: number; project: number }) => emit('on-delete', payload)
</script>

<template>
  <CTableRow
    v-if="contract"
    class="text-center"
    :class="{ 'table-warning': props.isHighlight }"
    :data-site-contract-id="contract.pk"
  >
    <CTableDataCell>{{ contract.owner_desc?.own_sort_desc }}</CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">
        {{ contract.owner_desc?.owner }}
      </a>
    </CTableDataCell>
    <CTableDataCell>
      <a href="javascript:void(0);" @click="showDetail">
        {{ contract.contract_date }}
      </a></CTableDataCell
    >
    <CTableDataCell class="text-right">
      {{ numFormat(contract.contract_area as number, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right" color="warning">
      {{ numFormat((contract.contract_area as number) * 0.3025, 2) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.total_price as number) }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.down_pay1 as number) }}
    </CTableDataCell>
    <CTableDataCell :class="{ 'bg-success': contract.down_pay1_is_paid }">
      {{ contract.down_pay1_is_paid ? '완료' : '' }}
    </CTableDataCell>
    <CTableDataCell class="text-right">
      {{ numFormat(contract.remain_pay as number) }}
    </CTableDataCell>
    <CTableDataCell :class="{ 'bg-success': contract.remain_pay_is_paid }">
      {{ contract.remain_pay_is_paid ? '완료' : '' }}
    </CTableDataCell>
    <CTableDataCell>
      <!-- 파일이 없는 경우 -->
      <span v-if="!contract.site_cont_files || contract.site_cont_files.length === 0">
        <v-icon icon="mdi-download-box-outline" color="secondary" />
        <v-tooltip activator="parent" location="top">미등록</v-tooltip>
      </span>
      <!-- 파일이 1개인 경우 -->
      <span v-else-if="contract.site_cont_files.length === 1" class="pointer">
        <a :href="contract.site_cont_files[0].file" target="_blank">
          <v-icon icon="mdi-download-box" color="primary" />
        </a>
        <v-tooltip activator="parent" location="top">
          {{ contract.site_cont_files[0]?.file_name }} ({{
            humanizeFileSize(contract.site_cont_files[0]?.file_size)
          }}) 다운로드
        </v-tooltip>
      </span>
      <!-- 파일이 복수(2개 이상)인 경우 -->
      <span v-else class="pointer">
        <v-menu location="bottom end">
          <template #activator="{ props: menuProps }">
            <v-badge
              :content="contract.site_cont_files.length"
              color="info"
              offset-x="-2"
              offset-y="-2"
            >
              <v-icon
                v-bind="menuProps"
                icon="mdi-folder-download"
                color="primary"
                class="cursor-pointer"
              />
            </v-badge>
            <v-tooltip activator="parent" location="top">
              첨부파일 {{ contract.site_cont_files.length }}개 (클릭하여 선택 다운로드)
            </v-tooltip>
          </template>
          <v-list density="compact" class="py-1">
            <v-list-item
              v-for="f in contract.site_cont_files"
              :key="f.pk"
              :href="f.file"
              target="_blank"
              class="px-3"
            >
              <template #prepend>
                <v-icon icon="mdi-file-document-outline" size="18" color="primary" class="mr-2" />
              </template>
              <v-list-item-title class="text-caption">
                {{ f.file_name }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption text-grey">
                {{ humanizeFileSize(f.file_size) }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-menu>
      </span>
    </CTableDataCell>
    <CTableDataCell v-if="canSiteUpdate">
      <v-btn color="info" size="x-small" @click="showDetail">확인</v-btn>
    </CTableDataCell>
  </CTableRow>

  <FormModal ref="updateFormModal" size="lg">
    <template #header>부지 매입 계약 등록</template>
    <template #default>
      <SiteContractForm
        :contract="contract"
        @multi-submit="multiSubmit"
        @on-delete="onDelete"
        @close="updateFormModal.close()"
      />
    </template>
  </FormModal>
</template>
