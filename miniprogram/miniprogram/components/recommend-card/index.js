const { toCardView } = require('./model')

Component({
  properties: { item: Object },
  data: { view: toCardView() },
  observers: {
    item(value) { this.setData({ view: toCardView(value) }) }
  },
  methods: {
    open() { this.triggerEvent('open', { id: this.data.view.destinationId }) },
    setStatus(event) {
      this.triggerEvent('status', {
        destinationId: this.data.view.destinationId,
        status: event.currentTarget.dataset.status
      })
    }
  }
})
