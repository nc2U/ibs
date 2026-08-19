<script setup lang="ts">
import type { Staff } from '@/store/types/company'
import type { OrgNode } from './OrgTreeNode.vue'

defineProps<{
  visible: boolean
  node: OrgNode | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()
</script>

<template>
  <CModal
    size="lg"
    alignment="center"
    :visible="visible"
    @close="emit('update:visible', false)"
  >
    <CModalHeader>
      <CModalTitle class="d-flex align-items-center">
        <CIcon name="cilBuilding" class="me-2 text-primary" />
        <span>{{ node?.name }}</span>
        <span class="badge bg-secondary ms-2 small">Lv.{{ node?.level }}</span>
      </CModalTitle>
    </CModalHeader>
    <CModalBody v-if="node">
      <!-- 부서 기본 정보 -->
      <div v-if="node.task" class="alert alert-light border mb-3">
        <strong class="d-block mb-1 text-secondary">
          <CIcon name="cilTask" class="me-1" />주요 담당 업무
        </strong>
        <div class="text-body small">{{ node.task }}</div>
      </div>

      <!-- 부서원 목록 -->
      <div class="d-flex align-items-center justify-content-between mb-2">
        <h6 class="mb-0 fw-bold">
          <CIcon name="cilPeople" class="me-1 text-info" />소속 직원 명단
        </h6>
        <span class="text-muted small">총 <strong>{{ node.members.length }}</strong>명</span>
      </div>

      <div v-if="!node.members.length" class="text-center text-muted py-4 border rounded bg-light">
        등록된 소속 직원이 없습니다.
      </div>

      <div v-else class="row g-3">
        <div
          v-for="member in node.members"
          :key="member.pk"
          class="col-md-6"
        >
          <div
            class="p-3 border rounded h-100 shadow-xs position-relative"
            :class="{ 'border-primary bg-primary-subtle': node.manager_name === member.name || member.duty?.includes('장') || member.duty?.includes('대표') }"
          >
            <div class="d-flex align-items-center mb-2">
              <div class="avatar bg-primary text-white rounded-circle me-3 d-flex align-items-center justify-content-center fw-bold" style="width: 40px; height: 40px">
                {{ member.name.charAt(0) }}
              </div>
              <div>
                <div class="fw-bold d-flex align-items-center">
                  {{ member.name }}
                  <span
                    v-if="member.duty"
                    class="badge bg-primary ms-1"
                    style="font-size: 0.7rem"
                  >
                    {{ member.duty }}
                  </span>
                  <span
                    v-if="member.position"
                    class="badge bg-secondary ms-1"
                    style="font-size: 0.7rem"
                  >
                    {{ member.position }}
                  </span>
                </div>
                <div v-if="member.grade" class="text-muted small">
                  직급: {{ member.grade }}
                </div>
              </div>
            </div>

            <div class="small text-muted mt-2 border-top pt-2">
              <div v-if="member.email" class="text-truncate mb-1">
                <v-icon icon="mdi-email-outline" size="x-small" class="me-1 text-secondary" />
                <a :href="`mailto:${member.email}`" class="text-decoration-none text-muted">
                  {{ member.email }}
                </a>
              </div>
              <div v-if="member.personal_phone" class="text-truncate mb-1">
                <v-icon icon="mdi-phone-outline" size="x-small" class="me-1 text-secondary" />
                <a :href="`tel:${member.personal_phone}`" class="text-decoration-none text-muted">
                  {{ member.personal_phone }}
                </a>
              </div>
              <div v-if="member.date_join" class="text-muted" style="font-size: 0.75rem">
                입사일: {{ member.date_join }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </CModalBody>
    <CModalFooter>
      <CButton color="secondary" variant="outline" @click="emit('update:visible', false)">
        닫기
      </CButton>
    </CModalFooter>
  </CModal>
</template>
