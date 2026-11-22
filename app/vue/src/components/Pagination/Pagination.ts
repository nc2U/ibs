import { computed, defineComponent, h, ref, watch } from 'vue'

import { CPagination, CPaginationItem } from '@coreui/vue'

const Pagination = defineComponent({
  name: 'CSmartPagination',
  props: {
    /**
     * Horizontally align
     *
     * @default 'start'
     */
    align: {
      type: String,
      default: 'start',
      required: false,
      validator: (value: string) => {
        return ['start', 'center', 'end'].includes(value)
      },
    },
    /**
     * Current page number
     *
     * @default 1
     */
    activePage: {
      type: Number,
      default: 1,
      required: false,
    },
    /**
     * Show/hide arrows
     *
     * @default true
     */
    arrows: {
      type: Boolean,
      default: true,
      required: false,
    },
    /**
     * Show/hide dots
     *
     * @default true
     */
    dots: {
      type: Boolean,
      default: true,
      required: false,
    },

    /**
     * Show double arrows buttons
     *
     * @default true
     */
    doubleArrows: {
      type: Boolean,
      default: true,
      required: false,
    },
    /**
     * The content of 'firstButton' button
     *
     * @default '&laquo;'
     */
    firstButton: {
      type: String,
      default: '&laquo;',
      required: false,
    },
    /**
     * The content of 'lastButton' button
     *
     * @default '&raquo;'
     */
    lastButton: {
      type: String,
      default: '&raquo;',
      required: false,
    },
    /**
     * Maximum items number
     *
     * @default 5
     */
    limit: {
      type: Number,
      default: 5,
      required: false,
    },
    /**
     * The content of 'nextButton' button
     *
     * @default '&rsaquo;'
     */
    nextButton: {
      type: String,
      default: '&rsaquo;',
      required: false,
    },
    /**
     * Number of pages
     */
    pages: {
      type: Number,
      default: 1000,
      required: false,
    },
    /**
     * The content of 'previousButton' button
     *
     * @default '&lsaquo;'
     */
    previousButton: {
      type: String,
      default: '&lsaquo;',
      required: false,
    },
    /**
     * Size of pagination, valid values: 'sm', 'lg'
     */
    size: {
      type: String,
      default: undefined,
      required: false,
      validator: (value: string) => {
        return ['sm', 'lg'].includes(value)
      },
    },
  },
  emits: [
    /**
     * On the active page change callback.
     */
    'activePageChange',
  ],
  setup(props, { emit }) {
    const activePage = ref(props.activePage)
    const limit = ref(props.limit)
    const pages = ref(props.pages)
    const isItem = computed(() => !!Number(pages.value))

    watch(
      () => [props.activePage, props.limit, props.pages] as const,
      ([newActive, newLimit, newPages]) => {
        activePage.value = newActive
        limit.value = newLimit
        pages.value = newPages
      },
    )

    const showDots = computed(() => {
      return props.dots && limit.value > 4 && limit.value < pages.value
    })

    const maxPrevItems = computed(() => {
      return Math.floor((limit.value - 1) / 2)
    })

    const maxNextItems = computed(() => {
      return Math.ceil((limit.value - 1) / 2)
    })

    const beforeDots = computed(() => {
      return showDots.value && activePage.value > maxPrevItems.value + 1
    })

    const afterDots = computed(() => {
      return showDots.value && activePage.value < pages.value - maxNextItems.value
    })

    const computedLimit = computed(() => {
      return limit.value - (afterDots.value ? 1 : 0) - (beforeDots.value ? 1 : 0)
    })

    const range = computed(() => {
      return activePage.value + maxNextItems.value
    })

    const lastItem = computed(() => {
      return range.value >= pages.value ? pages.value : range.value - (afterDots.value ? 1 : 0)
    })

    const itemsAmount = computed(() => {
      return pages.value < computedLimit.value ? pages.value : computedLimit.value
    })

    const items = computed(() => {
      if (activePage.value - maxPrevItems.value <= 1) {
        return Array.from(
          {
            length: itemsAmount.value,
          },
          (_v, i) => i + 1,
        )
      } else {
        return Array.from(
          {
            length: itemsAmount.value,
          },
          (_v, i) => {
            return lastItem.value - i
          },
        ).reverse()
      }
    })

    const setPage = (number: number): void => {
      if (number !== activePage.value) {
        activePage.value = number
        emit('activePageChange', number)
      }
    }

    return () =>
      h(
        CPagination,
        {
          class: [`justify-content-${props.align}`],
          'aria-label': 'pagination',
          size: props.size,
        },
        {
          default: () => [
            props.doubleArrows &&
              h(
                CPaginationItem,
                {
                  onClick: () => {
                    if (isItem.value) setPage(1)
                  },
                  'aria-label': 'Go to first page',
                  ...((!isItem.value || activePage.value <= 1) && {
                    'aria-disabled': true,
                    disabled: true,
                  }),
                },
                {
                  default: () =>
                    h('span', {
                      innerHTML: props.firstButton,
                    }),
                },
              ),
            props.arrows &&
              h(
                CPaginationItem,
                {
                  onClick: () => {
                    if (isItem.value && activePage.value > 1) setPage(activePage.value - 1)
                  },
                  'aria-label': 'Go to previous page',
                  ...((!isItem.value || activePage.value <= 1) && {
                    'aria-disabled': true,
                    disabled: true,
                  }),
                },
                {
                  default: () =>
                    h('span', {
                      innerHTML: props.previousButton,
                    }),
                },
              ),
            beforeDots.value &&
              h(
                CPaginationItem,
                {
                  role: 'separator',
                  disabled: true,
                },
                {
                  default: () => '...',
                },
              ),
            items.value.map((i: number) => {
              return h(
                CPaginationItem,
                {
                  key: i,
                  onClick: () => setPage(i),
                  'aria-label': activePage.value === i ? `Current page ${i}` : `Go to page ${i}`,
                  active: activePage.value === i,
                },
                {
                  default: () => i,
                },
              )
            }),
            afterDots.value &&
              h(
                CPaginationItem,
                {
                  role: 'separator',
                  disabled: true,
                },
                {
                  default: () => '...',
                },
              ),
            props.arrows &&
              h(
                CPaginationItem,
                {
                  onClick: () => {
                    if (isItem.value && activePage.value < pages.value)
                      setPage(activePage.value + 1)
                  },
                  'aria-label': 'Go to next page',
                  ...((!isItem.value || activePage.value >= pages.value) && {
                    'aria-disabled': true,
                    disabled: true,
                  }),
                },
                {
                  default: () =>
                    h('span', {
                      innerHTML: props.nextButton,
                    }),
                },
              ),
            props.doubleArrows &&
              h(
                CPaginationItem,
                {
                  onClick: () => {
                    if (isItem.value) setPage(pages.value)
                  },
                  'aria-label': 'Go to last page',
                  ...((!isItem.value || activePage.value >= pages.value) && {
                    'aria-disabled': true,
                    disabled: true,
                  }),
                },
                {
                  default: () =>
                    h('span', {
                      innerHTML: props.lastButton,
                    }),
                },
              ),
          ],
        },
      )
  },
})

export { Pagination }
