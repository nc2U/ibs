import { computed, ref, type PropType } from 'vue'
import { useSales } from '@/store/pinia/sales'
import { usePerms } from '@/composables/usePerms'
import type { SalesAgency, SalesTeam } from '@/store/types/sales'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import { CCard } from '@coreui/vue'

const props = defineProps({
  project: { type: Number, required: true },
  selectedTeamId: { type: Number as PropType<number | null>, default: null },
  selectedAgencyId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits([
  'select-team',
  'select-agency',
  'add-agency',
  'edit-agency',
  'add-team',
  'edit-team',
])

const { can, PERM } = usePerms()
const salesStore = useSales()
const agencyList = computed(() => salesStore.agencyList)
const teamList = computed(() => salesStore.teamList)

const getTeamsForAgency = (agencyId: number) => teamList.value.filter(t => t.agency === agencyId)

const selectAgency = (agency: SalesAgency) => {
  emit('select-agency', agency.id)
}

const selectTeam = (team: SalesTeam) => {
  emit('select-team', team.id)
}

const confirmModalRef = ref()
const pendingDelete = ref<{ type: 'agency' | 'team'; id: number; name: string } | null>(null)

const deleteAgency = (agency: SalesAgency) => {
  pendingDelete.value = { type: 'agency', id: agency.id, name: agency.name }
  confirmModalRef.value?.callModal()
}

const deleteTeam = (team: SalesTeam) => {
  pendingDelete.value = { type: 'team', id: team.id, name: team.name }
  confirmModalRef.value?.callModal()
}

const executeDelete = async () => {
  if (!pendingDelete.value) return
  confirmModalRef.value?.close()

  if (pendingDelete.value.type === 'agency') {
    await salesStore.deleteAgency(pendingDelete.value.id)
    if (props.project) {
      await salesStore.fetchAgencyList(props.project)
      await salesStore.fetchTeamList(undefined, props.project)
    }
  } else if (pendingDelete.value.type === 'team') {
    await salesStore.deleteTeam(pendingDelete.value.id)
    if (props.project) {
      await salesStore.fetchTeamList(undefined, props.project)
    }
  }
  pendingDelete.value = null
}
</script>

<template>
  <CCard class="mb-4 shadow-sm">
    <CCardHeader class="d-flex justify-content-between align-items-center bg-light">
      <div class="fw-bold">
        <v-icon icon="mdi-sitemap" size="small" class="mr-1 text-primary" />
        영업 조직 체계
      </div>
      <v-btn
        v-if="can(PERM.SALES_MANAGE)"
        color="primary"
        size="small"
        variant="tonal"
        @click="emit('add-agency')"
      >
        <v-icon icon="mdi-plus" size="small" class="mr-1" />
        대행사 추가
      </v-btn>
    </CCardHeader>

    <CCardBody class="p-2">
      <!-- 전체 보기 선택 -->
      <div
        class="tree-item p-2 mb-2 rounded cursor-pointer d-flex justify-content-between align-items-center"
        :class="{
          'bg-indigo-lighten-2 text-white': !selectedAgencyId && !selectedTeamId,
          'bg-more-secondary': selectedAgencyId || selectedTeamId,
        }"
        @click="emit('select-team', null)"
      >
        <span class="fw-bold">
          <v-icon icon="mdi-account-group" size="small" class="mr-1" />
          전체 인력 보기
        </span>
        <v-chip color="secondary" variant="flat" size="x-small">전체</v-chip>
      </div>

      <!-- 대행사가 없는 경우 -->
      <div v-if="agencyList.length === 0" class="py-4 text-center text-muted">
        등록된 분양 대행사가 없습니다.<br />
        <span v-if="can(PERM.SALES_MANAGE)">상단의 [대행사 추가]를 눌러 등록하세요.</span>
      </div>

      <!-- 대행사 및 팀 목록 -->
      <div
        v-for="agency in agencyList"
        :key="agency.id"
        class="agency-block mb-3 border rounded p-2"
      >
        <div class="d-flex justify-content-between align-items-center mb-2 pb-1 border-bottom">
          <div
            class="fw-bold cursor-pointer text-truncate"
            :class="{ 'text-primary': selectedAgencyId === agency.id }"
            @click="selectAgency(agency)"
          >
            <v-chip
              :color="agency.is_direct_managed ? 'info' : 'warning'"
              variant="flat"
              size="x-small"
              class="mr-1"
            >
              {{ agency.is_direct_managed ? '직영' : '외주' }}
            </v-chip>
            {{ agency.name }}
          </div>
          <div v-if="can(PERM.SALES_MANAGE)">
            <v-btn
              icon="mdi-pencil"
              size="x-small"
              variant="text"
              color="success"
              @click.stop="emit('edit-agency', agency)"
            />
            <v-btn
              icon="mdi-delete"
              size="x-small"
              variant="text"
              color="danger"
              @click.stop="deleteAgency(agency)"
            />
            <v-btn
              icon="mdi-plus"
              size="x-small"
              variant="tonal"
              color="primary"
              title="팀 추가"
              @click.stop="emit('add-team', agency.id)"
            />
          </div>
        </div>

        <!-- 하위 팀 목록 -->
        <div class="team-list pl-2">
          <div
            v-for="team in getTeamsForAgency(agency.id)"
            :key="team.id"
            class="team-item py-1 px-2 mb-1 rounded cursor-pointer d-flex justify-content-between align-items-center"
            :class="{
              'bg-indigo-lighten-2 text-white': selectedTeamId === team.id,
              'hover-bg': selectedTeamId !== team.id,
            }"
            @click="selectTeam(team)"
          >
            <span class="text-truncate">
              <v-icon icon="mdi-subdirectory-arrow-right" size="x-small" class="mr-1 opacity-75" />
              <span v-if="team.parent_name" class="opacity-75">{{ team.parent_name }} &gt; </span>
              <strong>{{ team.name }}</strong>
            </span>
            <div class="d-flex align-items-center">
              <v-chip color="light" variant="flat" size="x-small" class="mr-3 text-body">
                {{ team.members_count ?? 0 }}명
              </v-chip>
              <template v-if="can(PERM.SALES_MANAGE)">
                <v-btn
                  icon="mdi-pencil"
                  size="x-small"
                  variant="text"
                  :color="selectedTeamId === team.id ? 'white' : 'success'"
                  @click.stop="emit('edit-team', team)"
                />
                <v-btn
                  icon="mdi-close"
                  size="x-small"
                  variant="text"
                  :color="selectedTeamId === team.id ? 'white' : 'danger'"
                  @click.stop="deleteTeam(team)"
                />
              </template>
            </div>
          </div>

          <div v-if="getTeamsForAgency(agency.id).length === 0" class="text-muted pl-3 py-1">
            등록된 팀이 없습니다.
          </div>
        </div>
      </div>
  </CCard>

  <ConfirmModal ref="confirmModalRef">
    <template #header>삭제 확인</template>
    <template #default>
      <p class="mb-0">
        <strong>[{{ pendingDelete?.name }}]</strong> {{ pendingDelete?.type === 'agency' ? '대행사를' : '조직을' }} 삭제하시겠습니까?
      </p>
      <small v-if="pendingDelete?.type === 'agency'" class="text-danger">
        (하위 조직 및 인력이 함께 삭제되거나 데이터 무결성 오류가 발생할 수 있습니다)
      </small>
    </template>
    <template #footer>
      <v-btn size="small" color="danger" @click="executeDelete">삭제</v-btn>
    </template>
  </ConfirmModal>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.hover-bg:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
