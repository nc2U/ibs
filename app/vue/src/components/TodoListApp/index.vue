<script lang="ts" setup>
import { ref, computed, onBeforeMount, onUnmounted, watch } from 'vue'
import { useAccount } from '@/store/pinia/account.ts'
import type { Todo as T, TodoIssueInfo } from '@/store/types/accounts.ts'
import Todo from './Todo.vue'
import ConvertModal from './ConvertModal.vue'

type FilterKey = 'all' | 'active' | 'completed'

const todos = ref<T[]>([])
const visibility = ref<FilterKey>('all')

const account = useAccount()
const userId = computed(() => account.userInfo?.pk)
const myTodos = computed(() => account.myTodos)
watch(myTodos, val => (todos.value = val), { immediate: true })

const filters: Record<FilterKey, (items: T[]) => T[]> = {
  all: (items: T[]) => items,
  active: (items: T[]) => items.filter(todo => !todo.completed),
  completed: (items: T[]) => items.filter(todo => todo.completed),
}

const allChecked = computed(
  () => todos.value.length > 0 && todos.value.every(todo => todo.completed),
)

const filteredTodos = computed(() => filters[visibility.value](todos.value))

const remaining = computed(() => todos.value.filter(todo => !todo.completed).length)

const convertModalVisible = ref(false)
const selectedTodoForConvert = ref<T | null>(null)
const successNotice = ref<{
  visible: boolean
  issue: TodoIssueInfo
} | null>(null)

const openConvertModal = (todo: T) => {
  selectedTodoForConvert.value = todo
  convertModalVisible.value = true
}

let noticeTimer: ReturnType<typeof setTimeout> | undefined

const onConverted = (payload: { todo: T; issue: TodoIssueInfo }) => {
  successNotice.value = { visible: true, issue: payload.issue }
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => {
    if (successNotice.value) successNotice.value.visible = false
  }, 8000)
}

const addTodo = (e: Event) => {
  if ((e as KeyboardEvent).isComposing) return
  const input = e.target as HTMLInputElement
  const title = input.value.trim()
  if (userId.value && title) {
    account.createTodo({ user: userId.value, title })
  }
  input.value = ''
}

const toggleTodo = (todo: T) => {
  if (todo.pk) {
    todo.completed = !todo.completed
    account.patchTodo({ pk: todo.pk, completed: todo.completed })
  }
}

const delTodo = (pk: number) => {
  account.patchTodo({ pk, soft_deleted: true })
}

const editTodo = (pk: number, title: string) => {
  account.patchTodo({ pk, title })
}

const clearCompleted = () => {
  todos.value.forEach((todo: T) => {
    if (todo.completed && todo.pk) {
      account.patchTodo({ pk: todo.pk, soft_deleted: true })
    }
  })
}

const toggleAll = ({ completed }: { completed: boolean }) => {
  todos.value.forEach((todo: T) => {
    if (todo.pk && todo.completed !== completed) {
      todo.completed = completed
      account.patchTodo({ pk: todo.pk, completed })
    }
  })
}

const pluralize = (n: number, w: string) => (n === 1 ? w : w + 's')
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

onBeforeMount(() => account.fetchTodoList())
onUnmounted(() => clearTimeout(noticeTimer))
</script>

<template>
  <CAlert
    v-if="successNotice?.visible"
    color="success"
    dismissible
    class="mb-3 py-2 px-3 small d-flex justify-content-between align-items-center"
    @close="successNotice.visible = false"
  >
    <div class="me-2 text-truncate">
      <CIcon name="cilCheckCircle" class="me-1 text-success align-middle" />
      <strong>[#{{ successNotice.issue.pk }}] {{ successNotice.issue.subject }}</strong>
      (으)로 전환되었습니다.
    </div>
    <router-link
      :to="{
        name: '(업무) - 보기',
        params: {
          projId: successNotice.issue.project_slug || successNotice.issue.project_id,
          issueId: successNotice.issue.pk,
        },
      }"
      class="btn btn-sm btn-outline-success py-0 flex-shrink-0"
    >
      업무 바로가기
    </router-link>
  </CAlert>

  <section class="todoapp mb-4">
    <!-- header -->
    <header class="header">
      <input
        class="new-todo"
        autofocus
        autocomplete="off"
        placeholder="여기에 할 일을 메모 하세요."
        @keyup.enter="addTodo"
      />
    </header>
    <!-- main section -->
    <section v-show="todos.length" class="main">
      <input
        id="toggle-all"
        :checked="allChecked"
        class="toggle-all"
        type="checkbox"
        @change="toggleAll({ completed: !allChecked })"
      />
      <label for="toggle-all" />
      <ul class="todo-list">
        <Todo
          v-for="todo in filteredTodos"
          :key="todo.pk"
          :todo="todo"
          @toggle-todo="toggleTodo"
          @edit-todo="editTodo"
          @del-todo="delTodo"
          @convert-todo="openConvertModal"
        />
      </ul>
    </section>
    <!-- footer -->
    <footer v-show="todos.length" class="footer">
      <span class="todo-count">
        <strong>{{ remaining }}</strong> {{ pluralize(remaining, 'item') }} left
      </span>
      <ul class="filters">
        <li v-for="(_, key) in filters" :key="key">
          <a :class="{ selected: visibility === key }" @click.prevent="visibility = key">
            {{ capitalize(key) }}
          </a>
        </li>
      </ul>

      <button v-show="todos.length > remaining" class="clear-completed" @click="clearCompleted">
        Clear completed
      </button>
    </footer>
  </section>

  <ConvertModal
    v-model:visible="convertModalVisible"
    :todo="selectedTodoForConvert"
    @converted="onConverted"
  />

  <footer class="info text-center bottom-footer" style="font-size: 0.875rem">
    <p v-if="todos.length">할 일 목록을 수정하려면 더블클릭 하세요.</p>
    <p v-else>첫 번째 할 일 목록을 메모해 보세요.</p>
  </footer>
</template>

<style lang="scss">
@import 'index';

.bottom-footer {
  color: #ccc;
}

.dark-theme {
  .bottom-footer {
    color: #3e4853;
  }
}
</style>
