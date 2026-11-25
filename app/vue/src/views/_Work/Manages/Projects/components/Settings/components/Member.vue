<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { usePerms } from '@/composables/usePerms'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project'
import { isValidate, message } from '@/utils/helper'
import type { IssueProject, SimpleMember } from '@/store/types/work_project'
import NoData from '@/components/NoData/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const memberConfirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const memberFormModal = ref<InstanceType<typeof FormModal> | null>(null)

const { can, canViewUser, PERM } = usePerms()
const canManageMembers = computed(() => can(PERM.PROJECT_MEMBER))

const workStore = useWork()
const currentProject = computed(() => workStore.currentProject as IssueProject)
const memberList = computed<SimpleMember[]>(
  () => (workStore.currentProject as IssueProject)?.members ?? [],
)
const allMembers = computed<SimpleMember[]>(
  () => (workStore.currentProject as IssueProject)?.all_members ?? [],
)

const updateMembers = async (payload: {
  slug: string
  users: number[]
  roles: number[]
  del_mem?: number
}) => await workStore.updateMembers(payload)

const createMember = async (payload: { user?: number; roles?: number[]; slug: string }) =>
  await workStore.createMember(payload)

const patchMember = async (payload: {
  pk: number
  user?: number
  roles?: number[]
  slug?: string
}) => await workStore.patchMember(payload)

const accStore = useAccount()
const userList = computed(() => {
  const memPkList = allMembers.value.map(m => m.user.pk) // 멤버(상속시 부모 멤버 포함)로 등록된 사용자 id 배열

  // 전체 회원 중 이 프로젝트 구성원을 제외한 목록
  return accStore.usersList.filter(u => !memPkList.includes(u.pk as number))
})

const memberRole = ref<number[]>([]) // 업데이트할 멤버의 권한

const getLocalMemberPk = (userPk: number) =>
  memberList.value.find(m => m.user.pk === userPk)?.pk ?? null

const canDeleteMem = (mem: SimpleMember) =>
  getLocalMemberPk(mem.user.pk) !== null && !mem.roles.some(r => r.inherited)

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

const editSubmit = async (mem: SimpleMember, roles: number[]) => {
  const slug = currentProject?.value.slug as string
  const parent_roles = mem.roles.filter(r => r.inherited).map(r => r.pk)
  const calc_roles = roles.filter(r => !parent_roles.includes(r))
  const me = getLocalMemberPk(mem.user.pk)
  let ok: unknown = true

  if (me !== null) {
    if (calc_roles.length === 0) {
      if (parent_roles.length > 0) {
        ok = await updateMembers({ slug, users: [], roles: [], del_mem: me })
      } else {
        message('warning', '입력 확인', '최소 1개 이상의 역할을 선택해야 합니다.')
        return
      }
    } else {
      ok = await patchMember({ pk: me, roles: calc_roles })
    }
  } else {
    if (calc_roles.length === 0) {
      cancelEdit()
      return
    }
    ok = await createMember({ user: mem.user.pk, roles: calc_roles, slug })
  }

  if (ok) cancelEdit()
}

const toDelete = (mem: SimpleMember) => {
  const localPk = getLocalMemberPk(mem.user.pk)
  if (localPk === null) return
  memberConfirmModal.value?.callModal(
    '',
    '이 구성원을 워크스페이스에서 삭제하시겠습니까?',
    '',
    'warning',
  )
  deleteMember.value = localPk
}

const deleteMember = ref<number | null>(null)

const deleteSubmit = async () => {
  const ok = await updateMembers({
    slug: currentProject?.value.slug as string,
    users: [],
    roles: [],
    del_mem: deleteMember.value ?? undefined,
  })
  if (ok) memberConfirmModal.value?.close()
}

const mergedMembers = (
  mem1: { pk: number; name: string }[],
  mem2: { pk: number; name: string }[],
) => [...mem1, ...mem2].sort((a, b) => a.pk - b.pk)

const addComma = (n: number, i: number) => n > i + 1

const isInherit = (memRoles: SimpleMember['roles'], role: number) =>
  memRoles
    .filter(r => r.pk === role)
    .map(r => r.inherited)
    .some(i => i === true)

// FormModal Start ------------------

const validated = ref(false)

const users = ref<number[]>([])
const roles = ref<number[]>([])

const editMode = ref<number | null>(null)

const callModal = () => memberFormModal.value?.callModal()

const onSubmit = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const ok = await modalAction()
    if (ok) {
      validated.value = false
      memberFormModal.value?.close()
    }
  }
}

const modalAction = async () => {
  const _memList = [...users.value.sort((a, b) => a - b)]
  const _roles = [...roles.value.sort((a, b) => a - b)]
  const res = await updateMembers({
    slug: currentProject?.value.slug as string,
    users: _memList,
    roles: _roles,
  })
  if (res) {
    users.value = []
    roles.value = []
    return true
  }
  return false
}
// FormModal End ------------------

onBeforeMount(() => accStore.fetchUsersList())
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <span v-if="canManageMembers" class="me-2 form-text">
        <TextButton name="새 구성원" @click="callModal" />
      </span>
    </CCol>

    <CCol v-if="accStore.workManager" class="text-end">
      <span class="form-text">
        <TextButton name="관리" :to="{ name: '사용자' }" icon="mdi-cog" icon-color="grey" />
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
            <CTableHeaderCell class="ps-5" scope="col">사용자</CTableHeaderCell>
            <CTableHeaderCell class="ps-3" scope="col">역할</CTableHeaderCell>
            <CTableHeaderCell scope="col"></CTableHeaderCell>
          </CTableRow>
        </CTableHead>

        <CTableBody>
          <CTableRow v-for="mem in allMembers" :key="mem.pk" align="middle">
            <CTableDataCell class="ps-5">
              <router-link
                v-if="canViewUser(mem.user.pk)"
                :to="{ name: '사용자 - 보기', params: { userId: mem.user.pk } }"
              >
                {{ mem.user.username }}
              </router-link>
              <span v-else>{{ mem.user.username }}</span>
            </CTableDataCell>

            <CTableDataCell class="ps-3">
              <div v-if="editMode === mem.pk">
                <div v-for="role in currentProject?.allowed_roles" :key="role.pk">
                  <CFormCheck
                    v-model="memberRole"
                    :label="role.name"
                    :value="role.pk"
                    :id="'role-' + mem.pk + '-' + role.pk"
                    :disabled="isInherit(mem.roles, role.pk)"
                    class="text-start"
                  />
                  <span v-if="isInherit(mem.roles, role.pk)" class="form-text">
                    상위 워크스페이스로부터 상속
                  </span>
                </div>

                <v-btn
                  color="success"
                  size="x-small"
                  type="button"
                  class="mt-2"
                  :disabled="!canManageMembers"
                  @click="editSubmit(mem, memberRole)"
                >
                  저장
                </v-btn>
                <v-btn
                  color="secondary"
                  variant="outlined"
                  size="x-small"
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
              <span
                v-if="canManageMembers && (editMode === null || editMode !== mem.pk)"
                class="me-2"
              >
                <v-icon icon="mdi-pencil" color="amber" size="small" />
                <a href="#" @click.prevent="toEdit(mem)">편집</a>
              </span>
              <span v-else-if="editMode === mem.pk" class="me-2">
                <v-icon icon="mdi-close-octagon-outline" color="grey" size="small" class="me-1" />
                <a href="#" @click.prevent="cancelEdit">취소</a>
              </span>

              <span v-if="canManageMembers && canDeleteMem(mem)">
                <v-icon icon="mdi-trash-can-outline" color="grey" size="small" class="me-1" />
                <a href="#" @click.prevent="toDelete(mem)">삭제</a>
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
              <v-icon icon="mdi-check" color="success" size="small" />
              추가할 사용자 선택
            </CCardHeader>
            <CCardBody class="pb-5">
              <CFormCheck
                inline
                v-for="u in userList"
                :key="u.pk"
                :value="u.pk"
                :id="'user-' + u.pk"
                :label="u.username"
                v-model="users"
                :required="!users.length"
              />
            </CCardBody>
          </CCard>

          <CCard>
            <CCardHeader>
              <v-icon icon="mdi-check" color="success" size="small" />
              역할
            </CCardHeader>
            <CCardBody>
              <CFormCheck
                inline
                v-for="r in currentProject?.allowed_roles"
                :key="r.pk"
                :value="r.pk"
                :id="'add-role-' + r.pk"
                :label="r.name"
                v-model="roles"
                :required="!roles.length"
              />
            </CCardBody>
          </CCard>
        </CModalBody>
        <CModalFooter>
          <v-btn :disabled="!canManageMembers" color="primary" size="small" type="submit">
            추가
          </v-btn>
          <v-btn color="grey" variant="tonal" size="small" @click="memberFormModal?.close()">
            닫기</v-btn
          >
        </CModalFooter>
      </CForm>
    </template>
  </FormModal>

  <ConfirmModal ref="memberConfirmModal">
    <template #header>구성원 삭제</template>
    <template #footer>
      <v-btn color="warning" size="small" :disabled="!canManageMembers" @click="deleteSubmit">
        삭제
      </v-btn>
    </template>
  </ConfirmModal>
</template>
