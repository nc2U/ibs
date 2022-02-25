export default {
  methods: {
    numFormat(value = 0, n?: number) {
      const parts = n
        ? Number(value).toFixed(n).split('.')
        : value.toString().split('.')
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',')
      return !value || value === 0 ? '-' : parts.join('.')
    },
  },
}
