<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { usePerms } from '@/composables/usePerms'
import { useWork } from '@/store/pinia/work_project'
import { isValidate, message } from '@/utils/helper'
import type { Member } from '@/store/types/work_project'
import NoData from '@/components/NoData/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

const props = defineProps({ userPk: { type: Number, required: true } })

const { can, canGlobal, PERM } = usePerms()
const canGlobalProjectMember = computed(() => canGlobal(PERM.PROJECT_MEMBER))

// ────────────────────────────────────────────────────
// 스토어 & 데이터
// ────────────────────────────────────────────────────
const confirmModal = ref<InstanceType<typeof ConfirmModal> | null>(null)
const formModal = ref<InstanceType<typeof FormModal> | null>(null)

const accStore = useAccount()
const workStore = useWork()

// 이 유저가 소속된 멤버십 목록 (Member[]): { pk, user, project, roles, created }
const memberList = computed<Member[]>(() => workStore.memberList)

// 전체 역할 목록 (편집/추가 모달에서 선택용) - 시스템 역할(1: 익명, 2: 일반사용자) 및 비슈퍼유저의 보안 격리 역할 제외
const roleList = computed(() =>
  workStore.roleList.filter(
    r => r.pk !== 1 && r.pk !== 2 && (accStore.superAuth || !r.is_confidential),
  ),
)

const manageableActiveProjects = computed(() =>
  workStore.allActiveProjects.filter(p => can(PERM.PROJECT_MEMBER, p.slug)),
)

const getProjectStatus = (mem: Member) =>
  mem.project?.status ??
  workStore.allReadableProjects.find(p => Number(p.pk) === Number(mem.project.pk))?.status

const isProjectActive = (mem: Member) => getProjectStatus(mem) === '1'

const canManageMemberRow = (mem: Member) =>
  isProjectActive(mem) && can(PERM.PROJECT_MEMBER, mem.project.slug)

const hasAnyManageableRow = computed(() => memberList.value.some(m => canManageMemberRow(m)))

// ────────────────────────────────────────────────────
// 인라인 편집
// ────────────────────────────────────────────────────
const editMode = ref<number | null>(null) // 편집 중인 member.pk
const memberRole = ref<number[]>([])

const toEdit = (mem: Member) => {
  if (!canManageMemberRow(mem)) return
  editMode.value = mem.pk
  memberRole.value = mem.roles.map(r => r.pk)
}

const cancelEdit = () => {
  editMode.value = null
  memberRole.value = []
}

const syncAfterSelfEdit = async () => {
  if (props.userPk === accStore.userInfo?.pk) {
    await workStore.fetchMyProjectsList()
  }
}

const editSubmit = async (mem: Member, roles: number[]) => {
  if (!roles.length) {
    message('warning', '입력 확인', '최소 1개 이상의 역할을 선택해야 합니다.')
    return
  }
  const updated = await workStore.patchMember({ pk: mem.pk, roles })
  if (!updated) return
  if (props.userPk) await workStore.fetchMemberList(props.userPk)
  await syncAfterSelfEdit()
  cancelEdit()
}

// ────────────────────────────────────────────────────
// 삭제
// ────────────────────────────────────────────────────
const deleteMemberPk = ref<number | null>(null)

const toDelete = (pk: number) => {
  confirmModal.value?.callModal(
    '',
    '이 사용자를 해당 워크스페이스에서 제거하시겠습니까?',
    '',
    'warning',
  )
  deleteMemberPk.value = pk
}

const deleteSubmit = async () => {
  if (deleteMemberPk.value !== null) {
    const ok = await workStore.deleteMember(deleteMemberPk.value, props.userPk)
    if (!ok) return
    await syncAfterSelfEdit()
  }
  confirmModal.value?.close()
}

// ────────────────────────────────────────────────────
// 새 워크스페이스 추가 모달
// ────────────────────────────────────────────────────
const validated = ref(false)
const selectedProject = ref<number | null>(null)
const selectedRoles = ref<number[]>([])

const activeProject = computed(() =>
  manageableActiveProjects.value.find(p => Number(p.pk) === Number(selectedProject.value)),
)
const allowedRoleIds = computed<number[]>(
  () => activeProject.value?.allowed_roles?.map((r: { pk: number }) => r.pk) ?? [],
)

watch(selectedProject, () => {
  selectedRoles.value = []
})

const resetModalForm = () => {
  validated.value = false
  selectedProject.value = null
  selectedRoles.value = []
}

const callModal = () => {
  resetModalForm()
  formModal.value?.callModal()
}

const closeModal = () => {
  resetModalForm()
  formModal.value?.close()
}

const onSubmit = async (event: Event) => {
  if (isValidate(event)) {
    validated.value = true
  } else {
    const ok = await modalAction()
    if (ok) {
      closeModal()
    }
  }
}

const modalAction = async () => {
  if (!props.userPk || !selectedProject.value) return false
  if (!selectedRoles.value.length) {
    message('warning', '입력 확인', '최소 1개 이상의 역할을 선택해야 합니다.')
    return false
  }
  const proj = manageableActiveProjects.value.find(p => p.pk === selectedProject.value)
  if (!proj) return false
  const created = await workStore.createMember({
    user: props.userPk,
    roles: selectedRoles.value,
    slug: proj.slug,
  })
  if (!created) return false
  // 전체 목록 갱신
  await workStore.fetchMemberList(props.userPk)
  await syncAfterSelfEdit()
  selectedProject.value = null
  selectedRoles.value = []
  return true
}

// ────────────────────────────────────────────────────
// 유틸
// ────────────────────────────────────────────────────
const addComma = (total: number, i: number) => total > i + 1

const getAllowedRoleIdsByProject = (projPk: number) => {
  const proj = workStore.allReadableProjects.find(p => Number(p.pk) === Number(projPk))
  return proj?.allowed_roles?.map((r: { pk: number }) => Number(r.pk)) ?? []
}

// ────────────────────────────────────────────────────
// 초기화 및 userPk 변경 감시
// ────────────────────────────────────────────────────
watch(
  () => props.userPk,
  async pk => {
    cancelEdit()
    if (pk) await workStore.fetchMemberList(pk)
  },
)

onBeforeMount(async () => {
  await Promise.all([
    workStore.allReadableProjects.length ? Promise.resolve() : workStore.fetchAllProjectList(),
    workStore.roleList.length ? Promise.resolve() : workStore.fetchRoleList(),
    props.userPk ? workStore.fetchMemberList(props.userPk) : Promise.resolve(),
  ])
})
</script>

<template>
  <CCol>
    <!-- 헤더 액션 -->
    <CRow v-if="canGlobalProjectMember" class="py-2">
      <CCol>
        <span class="me-2 form-text">
          <TextButton name="워크스페이스 추가" @click="callModal" />
        </span>
      </CCol>
    </CRow>

    <!-- 데이터 없음 -->
    <NoData v-if="!memberList.length" />

    <!-- 워크스페이스-역할 테이블 -->
    <CRow v-else>
      <CCol>
        <v-divider class="my-0" />
        <CTable hover small striped responsive>
          <colgroup>
            <col style="width: 35%" />
            <col style="width: 40%" />
            <col v-if="hasAnyManageableRow" style="width: 25%" />
          </colgroup>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell class="ps-5" scope="col">워크스페이스</CTableHeaderCell>
              <CTableHeaderCell class="ps-3" scope="col">역할</CTableHeaderCell>
              <CTableHeaderCell v-if="hasAnyManageableRow" scope="col"></CTableHeaderCell>
            </CTableRow>
          </CTableHead>

          <CTableBody>
            <CTableRow v-for="mem in memberList" :key="mem.pk" align="middle">
              <!-- 워크스페이스명 -->
              <CTableDataCell class="ps-5">
                <router-link
                  v-if="getProjectStatus(mem) !== '9'"
                  :to="{ name: '(개요)', params: { projId: mem.project.slug } }"
                >
                  {{ mem.project.name }}
                </router-link>
                <span v-else class="text-muted">{{ mem.project.name }}</span>
                <span v-if="getProjectStatus(mem) === '9'" class="text-caption text-danger ms-2">
                  [잠금보관]
                </span>
                <span v-else-if="!isProjectActive(mem)" class="text-caption text-grey ms-2">
                  [닫힘]
                </span>
              </CTableDataCell>

              <!-- 역할 (편집 모드 or 표시 모드) -->
              <CTableDataCell class="ps-3">
                <div v-if="editMode === mem.pk">
                  <div v-for="role in roleList" :key="role.pk">
                    <CFormCheck
                      v-model="memberRole"
                      :label="role.name"
                      :value="role.pk"
                      :id="'user-proj-role-' + mem.pk + '-' + role.pk"
                      class="text-start"
                      :disabled="
                        !getAllowedRoleIdsByProject(mem.project.pk).includes(Number(role.pk))
                      "
                    />
                  </div>

                  <v-btn
                    color="success"
                    size="x-small"
                    type="button"
                    class="mt-2"
                    @click="editSubmit(mem, memberRole)"
                  >
                    저장
                  </v-btn>
                  <v-btn
                    color="grey"
                    variant="outlined"
                    size="x-small"
                    type="button"
                    @click="cancelEdit"
                    class="mt-2 ms-1"
                  >
                    취소
                  </v-btn>
                </div>

                <div v-else>
                  <span v-for="(role, i) in mem.roles" :key="role.pk">
                    {{ role.name }}<span v-if="addComma(mem.roles.length, i)">, </span>
                  </span>
                </div>
              </CTableDataCell>

              <!-- 액션 버튼 -->
              <CTableDataCell v-if="hasAnyManageableRow" class="px-3">
                <template v-if="canManageMemberRow(mem)">
                  <span v-if="editMode === null || editMode !== mem.pk" class="me-2">
                    <v-icon icon="mdi-pencil" color="amber" size="small" />
                    <a href="#" @click.prevent="toEdit(mem)">편집</a>
                  </span>
                  <span v-else-if="editMode === mem.pk" class="me-2">
                    <v-icon
                      icon="mdi-close-octagon-outline"
                      color="grey"
                      size="small"
                      class="me-1"
                    />
                    <a href="#" @click.prevent="cancelEdit">취소</a>
                  </span>

                  <span>
                    <v-icon icon="mdi-trash-can-outline" color="grey" size="small" class="me-1" />
                    <a href="#" @click.prevent="toDelete(mem.pk)">삭제</a>
                  </span>
                </template>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>

    <!-- 새 워크스페이스 추가 모달 -->
    <FormModal ref="formModal" size="xl" @close="resetModalForm">
      <template #icon></template>
      <template #header>워크스페이스 추가</template>
      <template #default>
        <CForm
          class="needs-validation"
          novalidate
          :validated="validated"
          @submit.prevent="onSubmit"
        >
          <CModalBody class="text-body">
            <!-- 워크스페이스 선택 -->
            <CCard class="mb-3">
              <CCardHeader>
                <v-icon icon="mdi-check" color="success" size="small" />
                추가할 워크스페이스 선택
              </CCardHeader>
              <CCardBody class="pb-5">
                <span v-if="!manageableActiveProjects.length" class="text-grey-darken-1">
                  추가 가능한 워크스페이스가 없습니다.
                </span>
                <div v-else class="d-flex flex-wrap gap-2">
                  <div
                    v-for="p in manageableActiveProjects"
                    :key="p.pk"
                    class="form-check form-check-inline"
                  >
                    <input
                      type="radio"
                      name="selectedProject"
                      :id="'proj-' + p.pk"
                      :value="p.pk"
                      class="form-check-input"
                      :disabled="
                        p.pk !== undefined && memberList.map(m => m.project.pk).includes(p.pk)
                      "
                      v-model="selectedProject"
                      required
                    />
                    <label :for="'proj-' + p.pk" class="form-check-label">{{ p.name }}</label>
                  </div>
                </div>
              </CCardBody>
            </CCard>

            <!-- 역할 선택 -->
            <CCard>
              <CCardHeader>
                <v-icon icon="mdi-check" color="success" size="small" />
                역할
              </CCardHeader>
              <CCardBody>
                <span v-if="!selectedProject" class="text-grey-darken-1">
                  먼저 워크스페이스를 선택해주세요.
                </span>
                <span v-else-if="selectedProject && !allowedRoleIds.length" class="text-warning">
                  이 워크스페이스에 허용된 역할이 없습니다.
                </span>
                <template v-else>
                  <CFormCheck
                    inline
                    v-for="r in roleList"
                    :key="r.pk"
                    :value="r.pk"
                    :id="'modal-role-' + r.pk"
                    :label="r.name"
                    v-model="selectedRoles"
                    :disabled="!allowedRoleIds.map(Number).includes(Number(r.pk))"
                    :required="!selectedRoles.length"
                  />
                </template>
              </CCardBody>
            </CCard>
          </CModalBody>

          <CModalFooter>
            <v-btn color="primary" size="small" type="submit">추가</v-btn>
            <v-btn color="grey" variant="tonal" size="small" @click="closeModal">닫기</v-btn>
          </CModalFooter>
        </CForm>
      </template>
    </FormModal>

    <!-- 삭제 확인 모달 -->
    <ConfirmModal ref="confirmModal">
      <template #header>구성원 제거</template>
      <template #footer>
        <v-btn color="warning" size="small" @click="deleteSubmit">삭제</v-btn>
      </template>
    </ConfirmModal>
  </CCol>
</template>
