<script lang="ts" setup>
import { ref, computed, onBeforeMount, inject, type ComputedRef } from 'vue'
import { btnLight } from '@/utils/cssMixins.ts'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import type { IssueProject, SimpleMember } from '@/store/types/work_project.ts'
import NoData from '@/views/_Work/components/NoData.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'

const memberConfirmModal = ref()
const memberFormModal = ref()

const iProject = inject<ComputedRef<IssueProject>>('iProject')

const workStore = useWork()
const memberList = computed<SimpleMember[]>(() => workStore.issueProject?.members ?? [])
const allMembers = computed<SimpleMember[]>(() => workStore.issueProject?.all_members ?? [])

const patchIssueProject = (payload: {
  slug: string
  users: number[]
  roles: number[]
  del_mem?: number
}) => workStore.patchIssueProject(payload)

const createMember = (payload: { user?: number; roles?: number[]; slug: string }) =>
  workStore.createMember(payload)

const patchMember = (payload: { pk: number; user?: number; roles?: number[]; slug?: string }) =>
  workStore.patchMember(payload)

const accStore = useAccount()
const userList = computed(() => {
  const memPkList = allMembers.value.map(m => m.user.pk) // 멤버(상속시 부모 멤버 포함)로 등록된 사용자 id 배열

  // 전체 회원 중 이 프로젝트 구성원을 제외한 목록
  return accStore.usersList.filter(u => !memPkList.includes(u.pk as number))
})

const memberRole = ref<number[]>([]) // 업데이트할 멤버의 권한

const noInheritMem = (mem: number) => {
  const member = memberList.value.filter(m => m.pk === mem)[0]
  const duplicate = allMembers.value.filter(m => m.pk === mem)[0]
  return !!member && member.roles.length === duplicate.roles.length
}

const toEdit = (member: SimpleMember) => {
  editMode.value = member.pk
  const pRoles = member.roles.map((r: { pk: number; name: string }) => r.pk)
  const mRoles = member.add_roles?.map(r => r.pk) ?? []
  memberRole.value = [...pRoles, ...mRoles]
}

const cancelEdit = () => {
  editMode.value = null
  memberRole.value = []
}

const editSubmit = (mem: SimpleMember, roles: number[]) => {
  const slug = iProject?.value.slug as string
  const parent_roles = mem.roles.filter(r => r.inherited).map(r => r.pk)
  const calc_roles = roles.filter(r => !parent_roles.includes(r))
  const me = memberList.value.filter(m => m.user.pk === mem.user.pk).map(m => m.pk)[0]

  if (!!me) patchMember({ pk: me, roles: calc_roles })
  else createMember({ user: mem.user.pk, roles: calc_roles, slug })

  cancelEdit()
}

const toDelete = (memPk: number) => {
  memberConfirmModal.value.callModal(
    '',
    '이 구성원을 프로젝트에서 삭제하시겠습니까?',
    '',
    'warning',
  )
  deleteMember.value = memPk
}

const deleteMember = ref<number | null>(null)

const deleteSubmit = () => {
  patchIssueProject({
    slug: iProject?.value.slug as string,
    users: [],
    roles: [],
    del_mem: deleteMember.value ?? undefined,
  })
  memberConfirmModal.value.close()
}

const mergedMembers = (
  mem1: { pk: number; name: string }[],
  mem2: { pk: number; name: string }[],
) => [...mem1, ...mem2].sort((a, b) => a.pk - b.pk)

const addComma = (n: number, i: number) => n > i + 1

const isInherit = (memRoles: any[], role: number) =>
  memRoles
    .filter(r => r.pk === role)
    .map(r => r.inherited)
    .some(i => i === true)

// FormModal Start ------------------

const validated = ref(false)

const users = ref([])
const roles = ref([])

const editMode = ref<number | null>(null)

const callModal = () => memberFormModal.value.callModal()

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
  } else {
    modalAction()
    validated.value = false
    memberFormModal.value.close()
  }
}

const modalAction = () => {
  const _memList = [...users.value.sort((a, b) => a - b)]
  const _roles = [...roles.value.sort((a, b) => a - b)]
  patchIssueProject({ slug: iProject?.value.slug as string, users: _memList, roles: _roles })
  users.value = []
  roles.value = []
}
// FormModal End ------------------

onBeforeMount(() => accStore.fetchUsersList())
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span class="mr-2 form-text">
        <v-icon icon="mdi-plus-circle" color="success" size="15" />
        <router-link to="" class="ml-1" @click="callModal"> 새 구성원 </router-link>
      </span>
    </CCol>

    <CCol class="text-right">
      <span class="form-text">
        <v-icon icon="mdi-cog" color="grey" size="15" />
        <router-link :to="{ name: '사용자' }" class="ml-1">관리</router-link>
      </span>
    </CCol>
  </CRow>

  <NoData v-if="!allMembers.length" />

  <CRow v-else>
    <CCol>
      <v-divider class="my-0" />
      <CTable hover small striped responsive>
        <colgroup>
          <col style="width: 30%" />
          <col style="width: 45%" />
          <col style="width: 25%" />
        </colgroup>
        <CTableHead>
          <CTableRow>
            <CTableHeaderCell class="pl-5" scope="col">사용자</CTableHeaderCell>
            <CTableHeaderCell class="pl-3" scope="col">역할</CTableHeaderCell>
            <CTableHeaderCell scope="col"></CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="mem in allMembers" :key="mem.pk" align="middle">
            <CTableDataCell class="pl-5">
              <router-link :to="{ name: '사용자 - 보기', params: { userId: mem.user.pk } }">
                {{ mem.user.username }}
              </router-link>
            </CTableDataCell>

            <CTableDataCell class="pl-3">
              <div v-if="editMode === mem.pk">
                <div v-for="role in iProject?.allowed_roles" :key="role.pk">
                  <CFormCheck
                    v-model="memberRole"
                    :label="role.name"
                    :value="role.pk"
                    :id="'role-' + role.pk"
                    :disabled="isInherit(mem.roles, role.pk)"
                    class="text-left"
                  />
                  <span v-if="isInherit(mem.roles, role.pk)" class="form-text">
                    상위 프로젝트로부터 상속
                  </span>
                </div>

                <v-btn
                  color="success"
                  size="small"
                  type="button"
                  class="mt-2"
                  @click="editSubmit(mem, memberRole)"
                >
                  저장
                </v-btn>
                <v-btn
                  color="secondary"
                  variant="outlined"
                  size="small"
                  type="button"
                  @click="cancelEdit"
                  class="mt-2"
                >
                  취소
                </v-btn>
              </div>
              <div v-else>
                <span
                  v-for="(mr, i) in mergedMembers(mem.roles, mem?.add_roles ?? [])"
                  :key="mr.pk"
                >
                  {{ mr.name
                  }}<span v-if="addComma(mem.roles.length + (mem?.add_roles?.length ?? 0), i)"
                    >,
                  </span>
                </span>
              </div>
            </CTableDataCell>
            <CTableDataCell class="px-3">
              <span v-if="editMode === null || editMode !== mem.pk" class="mr-2">
                <v-icon icon="mdi-pencil" color="amber" size="sm" />
                <router-link to="" @click="toEdit(mem)">편집</router-link>
              </span>
              <span v-else class="mr-2">
                <v-icon icon="mdi-close-octagon-outline" color="grey" size="sm" class="mr-1" />
                <router-link to="" @click="cancelEdit">취소</router-link>
              </span>

              <span v-if="noInheritMem(mem.pk)">
                <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" class="mr-1" />
                <router-link to="" @click="toDelete(mem.pk)">삭제</router-link>
              </span>
            </CTableDataCell>
          </CTableRow>
        </CTableBody>
      </CTable>
    </CCol>
  </CRow>

  <FormModal ref="memberFormModal" size="xl">
    <template #icon></template>
    <template #header>새 구성원</template>
    <template #default>
      <CForm class="needs-validation" novalidate :validated="validated" @submit.prevent="onSubmit">
        <CModalBody class="text-body">
          <CCard class="mb-3">
            <CCardHeader>
              <v-icon icon="mdi-check" color="success" size="sm" />
              추가할 사용자 선택
            </CCardHeader>
            <CCardBody class="pb-5">
              <CFormCheck
                inline
                v-for="u in userList"
                :key="u.pk"
                :value="u.pk"
                :id="u.username"
                :label="u.username"
                v-model="users"
                :required="!users.length"
              />
            </CCardBody>
          </CCard>

          <CCard>
            <CCardHeader>
              <v-icon icon="mdi-check" color="success" size="sm" />
              역할
            </CCardHeader>
            <CCardBody>
              <CFormCheck
                inline
                v-for="r in iProject?.allowed_roles"
                :key="r.pk"
                :value="r.pk"
                :id="r.name"
                :label="r.name"
                v-model="roles"
                :required="!roles.length"
              />
            </CCardBody>
          </CCard>
        </CModalBody>
        <CModalFooter>
          <v-btn :color="btnLight" @click="memberFormModal.close"> 닫기</v-btn>
          <v-btn color="primary" type="submit">추가</v-btn>
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="memberConfirmModal">
    <template #footer>
      <v-btn color="warning" size="small" @click="deleteSubmit">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>
