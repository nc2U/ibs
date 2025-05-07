<script lang="ts" setup>
import { type PropType, ref, watchEffect } from 'vue'
import { useRouter } from 'vue-router'
import { cutString } from '@/utils/baseMixins'
import type { IssueRelation } from '@/store/types/work'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

defineProps({
  addRIssue: { type: Boolean, default: false },
  relatedIssues: { type: Array as PropType<IssueRelation[]>, default: () => [] },
  getIssues: { type: Array as PropType<{ value: number; label: string }[]>, default: () => [] },
})

const emit = defineEmits(['delete-relation'])

const selected = ref<number | null>(null)

const router = useRouter()

const handleClickOutside = (event: any) => {
  if (!event.target.closest('.rel-issue')) selected.value = null
}

watchEffect(() => {
  if (selected.value) document.addEventListener('click', handleClickOutside)
  else document.removeEventListener('click', handleClickOutside)
})

const delRelRef = ref()
const relationPk = ref<number | null>(null)

const deleteRelation = (pk: number) => {
  relationPk.value = pk
  delRelRef.value.callModal()
}

const deleteRelConfirm = () => {
  emit('delete-relation', relationPk.value)
  relationPk.value = null
  delRelRef.value.close()
}
</script>

<template>
  <div class="mt-2">
    <CRow
      v-for="rel in relatedIssues"
      :key="rel.pk"
      :class="{ 'bg-info-lighten': selected === rel.pk }"
      class="rel-issue cursor-menu"
      @click="selected = rel.pk as number"
    >
      <CCol md="6" class="pt-1">
        <span>{{ rel.type_display }} : </span>
        <span>
          <router-link :to="{ name: '(업무) - 보기', params: { issueId: rel.issue_to?.pk } }">
            기능 #{{ rel.issue_to?.pk }}
          </router-link>
          : {{ rel.issue_to?.subject }}
        </span>
      </CCol>
      <CCol class="col-sm-8 col-md-3 text-right pt-1">
        <span class="mr-3">{{ rel.issue_to?.status }}</span>
        <span v-if="rel.issue_to" class="mr-3">
          <router-link
            :to="{ name: '사용자 - 보기', params: { userId: rel.issue_to.assigned_to.pk } }"
          >
            {{ cutString(rel.issue_to.assigned_to.username, 9) }}
          </router-link>
        </span>
        <span class="mr-3">{{ rel.issue_to?.start_date }}</span>
      </CCol>
      <CCol class="col-sm-4 col-md-3 text-right">
        <span>
          <CProgress
            color="green-lighten-3"
            :value="rel.issue_to?.done_ratio"
            style="width: 100px; float: left; margin-top: 7px"
            height="14"
          />
        </span>
        <span class="mr-3" @click="deleteRelation(rel.pk as number)">
          <v-icon icon="mdi-link-variant-off" size="sm" color="grey" class="pointer" />
          <v-tooltip activator="parent" location="top"> 관계 지우기 </v-tooltip>
        </span>
        <span>
          <CDropdown color="secondary" variant="input-group" placement="bottom-end">
            <CDropdownToggle
              :caret="false"
              color="light"
              variant="ghost"
              size="sm"
              shape="rounded-pill"
            >
              <v-icon icon="mdi-dots-horizontal" class="pointer" color="grey-darken-1" />
              <v-tooltip activator="parent" location="top">Actions</v-tooltip>
            </CDropdownToggle>
            <CDropdownMenu>
              <CDropdownItem
                class="form-text"
                @click="
                  router.push({
                    name: '(업무) - 보기',
                    params: { issueId: rel.issue_to?.pk },
                    query: { edit: '1' },
                  })
                "
              >
                <router-link to="">
                  <v-icon icon="mdi-pencil" color="amber" size="sm" />
                  편집
                </router-link>
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon color="amber" size="sm" />
                유형
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <v-icon color="amber" size="sm" />
                <!--                    <router-link to=""> -->
                우선순위
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <v-icon color="amber" size="sm" />
                <!--                    <router-link to=""> -->
                담당자
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <v-icon color="amber" size="sm" />
                <!--                    <router-link to=""> -->
                진척도
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon icon="mdi-star" color="secondary" size="sm" />
                지켜보기
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon icon="mdi-timer-edit-outline" color="grey" size="sm" />
                작업시간 기록
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon icon="mdi-link-plus" color="grey" size="sm" />
                링크 복사
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon icon="mdi-content-copy" color="grey" size="sm" />
                복사
                <!--                    </router-link>-->
              </CDropdownItem>
              <CDropdownItem class="form-text" disabled>
                <!--                    <router-link to="">-->
                <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" />
                업무 삭제
                <!--                    </router-link>-->
              </CDropdownItem>
            </CDropdownMenu>
          </CDropdown>
        </span>
      </CCol>
    </CRow>
  </div>

  <ConfirmModal ref="delRelRef">
    <template #header>연결된 업무 관계 지우기</template>
    <template #default> 계속 진행하시겠습니까?</template>
    <template #footer>
      <v-btn color="warning" @click="deleteRelConfirm">확인</v-btn>
    </template>
  </ConfirmModal>
</template>

<style lang="scss" scoped>
.closed {
  color: #999;
  text-decoration: line-through;
}
</style>
