<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useWork } from '@/store/pinia/work_project.ts'
import type { Member } from '@/store/types/work_project.ts'
import NoData from '@/components/NoData/Index.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import TextButton from '@/views/_Work/components/atomics/TextButton.vue'

// ────────────────────────────────────────────────────
// 스토어 & 데이터
// ────────────────────────────────────────────────────
const confirmModal = ref()
const formModal = ref()

const accStore = useAccount()
const workStore = useWork()

// 현재 편집 대상 유저 (AdminUserManage 에서 accStore.user 로 관리)
const userPk = computed(() => accStore.user?.pk as number | undefined)

// 이 유저가 소속된 멤버십 목록 (Member[]): { pk, user, project, roles, created }
const memberList = computed<Member[]>(() => workStore.memberList)

// 전체 역할 목록 (편집/추가 모달에서 선택용) - 시스템 역할(1: 익명, 2: 일반사용자)은 제외
const roleList = computed(() => workStore.roleList.filter(r => r.pk !== 1 && r.pk !== 2))

// ────────────────────────────────────────────────────
// 인라인 편집
// ────────────────────────────────────────────────────
const editMode = ref<number | null>(null) // 편집 중인 member.pk
const memberRole = ref<number[]>([])

const toEdit = (mem: Member) => {
  editMode.value = mem.pk
  memberRole.value = mem.roles.map(r => r.pk)
}

const cancelEdit = () => {
  editMode.value = null
  memberRole.value = []
}

const editSubmit = (mem: Member, roles: number[]) => {
  workStore.patchMember({ pk: mem.pk, roles }).then(() => {
    if (userPk.value) workStore.fetchMemberList(userPk.value)
  })
  cancelEdit()
}

// ────────────────────────────────────────────────────
// 삭제
// ────────────────────────────────────────────────────
const deleteMemberPk = ref<number | null>(null)

const toDelete = (pk: number) => {
  confirmModal.value.callModal('', '이 사용자를 해당 프로젝트에서 제거하시겠습니까?', '', 'warning')
  deleteMemberPk.value = pk
}

const deleteSubmit = () => {
  if (deleteMemberPk.value !== null) {
    workStore.deleteMember(deleteMemberPk.value, userPk.value)
  }
  confirmModal.value.close()
}

// ────────────────────────────────────────────────────
// 새 프로젝트 추가 모달
// ────────────────────────────────────────────────────
const validated = ref(false)
const selectedProject = ref<number | null>(null)
const selectedRoles = ref<number[]>([])

const activeProject = computed(() =>
  workStore.allProjects.find(p => Number(p.pk) === Number(selectedProject.value)),
)
const allowedRoleIds = computed<number[]>(
  () => activeProject.value?.allowed_roles?.map((r: any) => r.pk) ?? [],
)

watch(selectedProject, () => {
  selectedRoles.value = []
})

const callModal = () => formModal.value.callModal()

const onSubmit = (event: Event) => {
  const el = event.currentTarget as HTMLFormElement
  if (!el.checkValidity()) {
    event.preventDefault()
    event.stopPropagation()
    validated.value = true
  } else {
    modalAction()
    validated.value = false
    formModal.value.close()
  }
}

const modalAction = async () => {
  if (!userPk.value || !selectedProject.value) return
  const proj = workStore.allProjects.find(p => p.pk === selectedProject.value)
  if (proj) {
    await workStore.createMember({
      user: userPk.value,
      roles: selectedRoles.value,
      slug: proj.slug,
    })
  }
  // 전체 목록 갱신
  await workStore.fetchMemberList(userPk.value)
  selectedProject.value = null
  selectedRoles.value = []
}

// ────────────────────────────────────────────────────
// 유틸
// ────────────────────────────────────────────────────
const addComma = (total: number, i: number) => total > i + 1

const getAllowedRoleIdsByProject = (projPk: number) => {
  const proj = workStore.allProjects.find(p => Number(p.pk) === Number(projPk))
  return proj?.allowed_roles?.map((r: any) => Number(r.pk)) ?? []
}

// ────────────────────────────────────────────────────
// 초기화
// ────────────────────────────────────────────────────
onBeforeMount(async () => {
  await workStore.fetchAllProjectList()
  await workStore.fetchRoleList()
})

watch(
  userPk,
  async newVal => {
    if (newVal) await workStore.fetchMemberList(newVal)
  },
  { immediate: true },
)
</script>

<template>
  <CCol>
    <!-- 헤더 액션 -->
    <CRow class="py-2">
      <CCol>
        <span class="mr-2 form-text">
          <TextButton name="프로젝트 추가" @click="callModal" />
        </span>
      </CCol>
    </CRow>

    <!-- 데이터 없음 -->
    <NoData v-if="!memberList.length" />

    <!-- 프로젝트-역할 테이블 -->
    <CRow v-else>
      <CCol>
        <v-divider class="my-0" />
        <CTable hover small striped responsive>
          <colgroup>
            <col style="width: 35%" />
            <col style="width: 40%" />
            <col style="width: 25%" />
          </colgroup>
          <CTableHead>
            <CTableRow>
              <CTableHeaderCell class="pl-5" scope="col">프로젝트</CTableHeaderCell>
              <CTableHeaderCell class="pl-3" scope="col">역할</CTableHeaderCell>
              <CTableHeaderCell scope="col"></CTableHeaderCell>
            </CTableRow>
          </CTableHead>

          <CTableBody>
            <CTableRow v-for="mem in memberList" :key="mem.pk" align="middle">
              <!-- 프로젝트명 -->
              <CTableDataCell class="pl-5">
                <router-link :to="{ name: '(개요)', params: { projId: mem.project.slug } }">
                  {{ mem.project.name }}
                </router-link>
              </CTableDataCell>

              <!-- 역할 (편집 모드 or 표시 모드) -->
              <CTableDataCell class="pl-3">
                <div v-if="editMode === mem.pk">
                  <div v-for="role in roleList" :key="role.pk">
                    <CFormCheck
                      v-model="memberRole"
                      :label="role.name"
                      :value="role.pk"
                      :id="'user-proj-role-' + role.pk"
                      class="text-left"
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
                    class="mt-2"
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
              <CTableDataCell class="px-3">
                <span v-if="editMode === null || editMode !== mem.pk" class="mr-2">
                  <v-icon icon="mdi-pencil" color="amber" size="sm" />
                  <router-link to="" @click="toEdit(mem)">편집</router-link>
                </span>
                <span v-else-if="editMode === mem.pk" class="mr-2">
                  <v-icon icon="mdi-close-octagon-outline" color="grey" size="sm" class="mr-1" />
                  <router-link to="" @click="cancelEdit">취소</router-link>
                </span>

                <span>
                  <v-icon icon="mdi-trash-can-outline" color="grey" size="sm" class="mr-1" />
                  <router-link to="" @click="toDelete(mem.pk)">삭제</router-link>
                </span>
              </CTableDataCell>
            </CTableRow>
          </CTableBody>
        </CTable>
      </CCol>
    </CRow>

    <!-- 새 프로젝트 추가 모달 -->
    <FormModal ref="formModal" size="xl">
      <template #icon></template>
      <template #header>프로젝트 추가</template>
      <template #default>
        <CForm
          class="needs-validation"
          novalidate
          :validated="validated"
          @submit.prevent="onSubmit"
        >
          <CModalBody class="text-body">
            <!-- 프로젝트 선택 -->
            <CCard class="mb-3">
              <CCardHeader>
                <v-icon icon="mdi-check" color="success" size="sm" />
                추가할 프로젝트 선택
              </CCardHeader>
              <CCardBody class="pb-5">
                <span v-if="!workStore.allProjects.length" class="text-grey-darken-1">
                  추가 가능한 프로젝트가 없습니다.
                </span>
                <div v-else class="d-flex flex-wrap gap-2">
                  <div
                    v-for="p in workStore.allProjects"
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
                <v-icon icon="mdi-check" color="success" size="sm" />
                역할
              </CCardHeader>
              <CCardBody>
                <span v-if="!selectedProject" class="text-grey-darken-1">
                  먼저 프로젝트를 선택해주세요.
                </span>
                <span v-else-if="selectedProject && !allowedRoleIds.length" class="text-warning">
                  이 프로젝트에 허용된 역할이 없습니다.
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
            <v-btn color="light" size="small" @click="formModal.close" flat>닫기</v-btn>
          </CModalFooter>
        </CForm>
      </template>
    </FormModal>

    <!-- 삭제 확인 모달 -->
    <ConfirmModal ref="confirmModal">
      <template #footer>
        <v-btn color="warning" size="small" @click="deleteSubmit">삭제</v-btn>
      </template>
    </ConfirmModal>
  </CCol>
</template>
