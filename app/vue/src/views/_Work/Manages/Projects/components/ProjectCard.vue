<script lang="ts" setup>
import { type ComputedRef, inject, type PropType } from 'vue'
import { VueMarkdownIt } from '@f3ve/vue-markdown-it'
import type { User } from '@/store/types/accounts.ts'
import type { IssueProject } from '@/store/types/work.ts'

defineProps({
  project: {
    type: Object as PropType<IssueProject>,
    required: true,
  },
})

const userInfo = inject<ComputedRef<User>>('userInfo')

const hasVisible = (project: IssueProject) => {
  if (project.visible) return true
  if (project.sub_projects && project.sub_projects.length > 0)
    for (let sub of project.sub_projects) {
      if (hasVisible(sub)) return true
    }
  return false
}

const isOwnProject = (project: IssueProject) =>
  project.all_members?.map(m => m.user.pk).includes(userInfo?.value?.pk as number)
</script>

<template>
  <CCard v-if="hasVisible(project)" class="my-2">
    <CCardBody class="project-set">
      <span v-if="project.visible">
        <router-link
          :to="{ name: '(개요)', params: { projId: project.slug } }"
          :class="{ 'text-grey': project.status === '9' }"
        >
          {{ project.name }}
        </router-link>
        <v-icon
          v-if="isOwnProject(project)"
          icon="mdi-account-tag"
          color="success"
          size="15"
          class="ml-1"
        />
        <VueMarkdownIt :source="project.description" />
      </span>

      <!-- c1 -->
      <div
        v-if="!!project.sub_projects?.length"
        :class="{ child: project.visible, 'project-set': !project.visible }"
      >
        <blockquote v-for="c1 in project.sub_projects" :key="c1.pk">
          <span v-if="c1.visible">
            <router-link :to="{ name: '(개요)', params: { projId: c1.slug } }">
              {{ c1.name }}
            </router-link>
            <v-icon
              v-if="isOwnProject(c1)"
              icon="mdi-account-tag"
              color="success"
              size="15"
              class="ml-1"
            />
            <VueMarkdownIt :source="c1.description" />
          </span>

          <!-- c2 -->
          <div
            v-if="!!c1.sub_projects?.length"
            :class="{ child: c1.visible, 'project-set': !c1.visible }"
          >
            <blockquote v-for="c2 in c1.sub_projects" :key="c2.pk">
              <span v-if="c2.visible">
                <router-link :to="{ name: '(개요)', params: { projId: c2.slug } }">
                  {{ c2.name }}
                </router-link>
                <v-icon
                  v-if="isOwnProject(c2)"
                  icon="mdi-account-tag"
                  color="success"
                  size="15"
                  class="ml-1"
                />
                <VueMarkdownIt :source="c2.description" />
              </span>

              <!-- c3 -->
              <div
                v-if="!!c2.sub_projects?.length"
                :class="{ child: c2.visible, 'project-set': !c2.visible }"
              >
                <blockquote v-for="c3 in c2.sub_projects" :key="c3.pk">
                  <span v-if="c3.visible">
                    <router-link :to="{ name: '(개요)', params: { projId: c3.slug } }">
                      {{ c3.name }}
                    </router-link>
                    <v-icon
                      v-if="isOwnProject(c3)"
                      icon="mdi-account-tag"
                      color="success"
                      size="15"
                      class="ml-1"
                    />
                    <VueMarkdownIt :source="c3.description" />
                  </span>

                  <!-- c4 -->
                  <div
                    v-if="!!c3.sub_projects?.length"
                    :class="{ child: c3.visible, 'project-set': !c3.visible }"
                  >
                    <blockquote v-for="c4 in c3.sub_projects" :key="c4.pk">
                      <span v-if="c4.visible">
                        <router-link :to="{ name: '(개요)', params: { projId: c4.slug } }">
                          {{ c4.name }}
                        </router-link>
                        <v-icon
                          v-if="isOwnProject(c4)"
                          icon="mdi-account-tag"
                          color="success"
                          size="15"
                          class="ml-1"
                        />
                        <VueMarkdownIt :source="c4.description" />
                      </span>

                      <!-- c5 -->
                      <div
                        v-if="!!c4.sub_projects?.length"
                        :class="{ child: c4.visible, 'project-set': !c4.visible }"
                      >
                        <blockquote v-for="c5 in c4.sub_projects" :key="c5.pk">
                          <span v-if="c5.visible">
                            <router-link :to="{ name: '(개요)', params: { projId: c5.slug } }">
                              {{ c5.name }}
                            </router-link>
                            <v-icon
                              v-if="isOwnProject(c5)"
                              icon="mdi-account-tag"
                              color="success"
                              size="15"
                              class="ml-1"
                            />
                            <VueMarkdownIt :source="c5.description" />
                          </span>
                        </blockquote>
                      </div>
                    </blockquote>
                  </div>
                </blockquote>
              </div>
            </blockquote>
          </div>
        </blockquote>
      </div>
    </CCardBody>
  </CCard>
</template>
