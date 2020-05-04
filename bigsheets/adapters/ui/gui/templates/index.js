/**
 * @param {string[][]} sheet
 */
function setSampleSheet (sheet) {
  console.log(sheet)
}

class Progress {
  constructor () {
    /**
     * @type {HTMLProgressElement}
     */
    this.el = document.getElementById('progress')
    console.assert(this.el)
    this.el.hidden = true
  }

  startProcessing (total) {
    this.el.hidden = false
    this.el.max = total
    if (total === null) {
      this.el.removeAttribute('value')
      this.el.indeterminate = true
    } else {
      this.el.value = 0
      this.el.indeterminate = false
    }
  }

  update (completed) {
    this.el.value = completed
  }

  finish () {
    this.el.hidden = true
  }
}

class Info {
  constructor () {
    /**
     * @type {HTMLSpanElement}
     */
    this.el = document.getElementById('info')
    console.assert(this.el)
  }

  set (message) {
    this.el.innerHTML = message
  }

  unset () {
    this.el.innerHTML = ''
  }
}

class Table {
  constructor () {
    /**
     *
     * @type {HTMLTableElement}
     */
    this.el = document.getElementById('table')
    console.assert(this.el)
  }

  init () {
    this.el.innerHTML = ''
    this.el.createTHead()
    this.el.createTBody()
  }

  /**
   *
   * @param {string[][]} rows
   * @param {string[]?} header
   */
  set (rows, header = null) {
    this.init()
    if (header) {
      const row = this.el.tHead.insertRow()
      let html = '<th></th>'
      for (let h of header) {
        html += `<th class="col"><div>&nbsp;&nbsp;${h}&nbsp;&nbsp;</div></th>`
      }
      row.innerHTML = html
    }
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i]
      const domRow = this.el.insertRow()
      domRow.innerHTML = `<th class="row">${i}</th>`
      for (let c of row) {
        const domCell = domRow.insertCell()
        domCell.innerHTML = `<div>${c}</div>`
      }
    }
  }

}

class Query {
  constructor () {
    this.queryEditor = null
    this._disabled = false
    this.message = document.getElementById('query-message')
    console.assert(this.message)
    /**
     * @type {HTMLInputElement}
     */
    this._limit = document.getElementById('limit')
    console.assert(this._limit)
    this.limit = 100 // Set limit before being able to handle changes
    this._limit.onchange = () => {
      this.query()
    }
    /**
     *
     * @type {HTMLFormElement}
     * @private
     */
    this._queryForm = document.getElementById('query-form')
    this._queryForm.onsubmit = event => {
      if (event) event.preventDefault()
      this.query()
    }
    this._queryForm.hidden = true
    /**
     * @type {HTMLInputElement}
     * @private
     */
    this._queryFormSubmit = document.getElementById('query-submit')

    /**
     * @type {HTMLInputElement}
     */
    this._page = document.getElementById('page')
    this.page = 0
    this._page.onchange = () => {
      this.query(false)
    }
  }

  init (sheetName, headers) {
    // Init this after setting the table
    console.log(sheetName, headers)
    this.queryEditor = startEditor(sheetName, headers)
    this._queryForm.hidden = false
  }

  query (resetPage = true) {
    if (this._disabled) throw Error("Cannot query while disabled.")
    if (resetPage) this.page = 0
    this.message.innerText = ''
    const query = this.queryEditor.getValue()
    console.log(query)
    pywebview.api.query(query, this.limit, this.page)
  }

  setMessage (message) {
    this.message.innerText = message
  }

  onQueryChanged () {
    this.queryEditor.getValue()
  }

  enable () {
    this._disabled = this._limit.disabled = this._page.disabled = this._queryFormSubmit.disabled = false
  }

  disable () {
    this._disabled = this._limit.disabled = this._page.disabled = this._queryFormSubmit.disabled = true
  }

  get limit () {
    return parseInt(this._limit.value)
  }

  set limit (v) {
    this._limit.value = v
  }

  get page () {
    return parseInt(this._page.value)
  }

  set page (v) {
    this._page.value = v
  }

}

class Nav {
  constructor () {
    /**
     * @type {HTMLButtonElement}
     * @private
     */
    this._openWindowButton = document.getElementById("open-window")
    this._openWindowButton.onclick = () => {
      console.log('fooobar')
      pywebview.api.open_window()
    }
    this.disable()
  }

  disable () {
    this._openWindowButton.disabled = true
  }

  enable () {
    this._openWindowButton.disabled = false
  }

}

window.progress = new Progress()
window.info = new Info()
window.table = new Table()
window.query = new Query()
window.nav = new Nav()

/**
 * @type {HTMLDivElement}
 */
const d = document.createElement('div')
const c = document.createElement('div')
c.style = 'vertical-align: middle'
c.innerHTML = '<button class=\'close-button\'><i class=\'fa fa-lg fa-times\'></i></button>filename1 <em>as</em> <strong>sheet1</strong>'
d.appendChild(c)

tippy('#sheets-button', {
  content: d,
  trigger: 'click',
  hideOnClick: 'toggle',
  interactive: true,
  theme: 'ours',
  animation: 'scale',
  inertia: true
})
