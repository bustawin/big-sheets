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
      const domRow = this.el.tBodies[0].insertRow()
      domRow.innerHTML = `<th class="row">${i}</th>`
      for (let c of row) {
        const domCell = domRow.insertCell()
        domCell.innerHTML = `${c}`
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
      this.submitQuery()
    }
    /**
     *
     * @type {HTMLFormElement}
     * @private
     */
    this._queryForm = document.getElementById('query-form')
    this._queryForm.onsubmit = event => {
      if (event) event.preventDefault()
      this.submitQuery()
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
      this.submitQuery(false)
    }
  }

  init (sheetName, headers) {
    // Init this after setting the table
    this.queryEditor = startEditor(sheetName, darkMode)
    this._queryForm.hidden = false
  }

  submitQuery (resetPage = true) {
    if (this._disabled) throw Error('Cannot query while disabled.')
    if (resetPage) this.page = 0
    this.message.innerText = ''
    pywebview.api.query(this.query, this.limit, this.page)
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

  /**
   * Sets the opened sheets to the query editor keywords.
   * @param {Object.<string, string[]>} sheets
   */
  setOpenedSheets (sheets) {
    this.queryEditor.setVariables(
      [...Object.keys(sheets), ...Object.values(sheets).flat()]
    )
  }

  get query () {
    return this.queryEditor.getValue()
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
    this._openWindowBtn = document.getElementById('open-window')
    this._openWindowBtn.onclick = () => {
      pywebview.api.open_window()
    }
    this._sheetsBtn = document.getElementById('sheets-button')
    this._openSheetBtn = document.getElementById('open-sheet-button')
    this._openSheetBtn.onclick = () => {
      pywebview.api.open_sheet()
    }
    this._exportViewBtn = document.getElementById('export-view-button')
    this._exportViewBtn.onclick = () => {
      pywebview.api.export_view(window.query.query)
    }
    this._saveWorkspaceBtn = document.getElementById('save-workspace-button')
    this._saveWorkspaceBtn.onclick = () => {
      pywebview.api.save_workspace()
    }
    this.disable()
  }

  disable () {
    this._openWindowBtn.disabled = this._sheetsBtn.disabled = this._openSheetBtn.disabled =
      this._exportViewBtn.disabled = this._saveWorkspaceBtn.disabled
        = true
  }

  enable () {
    this._openWindowBtn.disabled = this._sheetsBtn.disabled = this._openSheetBtn.disabled =
      this._exportViewBtn.disabled = this._saveWorkspaceBtn.disabled
        = false
  }
}

class SheetsButton {
  constructor () {
    this.sheets = []
    this._tippy = tippy('#sheets-button', {
      content: this._content.bind(this),
      trigger: 'click',
      hideOnClick: 'toggle',
      interactive: true,
      theme: 'ours',
      animation: 'scale',
      inertia: true
    })[0]
  }

  _content () {
    const sheets = this.sheets.map(({filename, name}) => {
      const delElementButton = document.createElement('button')
      delElementButton.className = 'close-button'
      delElementButton.innerHTML = '<i class=\'fa fa-lg fa-times\'></i>'
      delElementButton.onclick = () => this.removeSheet(name)
      delElementButton.style = 'margin-right:1em'
      const text = document.createElement('span')
      text.innerHTML = `${filename}&nbsp;<em>as</em>&nbsp;<strong>${name}</strong>`
      const div = document.createElement('div')
      div.appendChild(delElementButton)
      div.appendChild(text)
      return div
    })
    const content = document.createElement('div')
    content.className = 'sheets-button-line'
    content.append(...sheets)
    return content
  }

  set (sheets) {
    this.sheets = sheets
    this._tippy.setContent(this._content())
  }

  removeSheet (name) {
    pywebview.api.remove_sheet(name)
  }
}

const darkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches

window.progress = new Progress()
window.info = new Info()
window.table = new Table()
window.query = new Query()
window.nav = new Nav()
window.sheetsButton = new SheetsButton()

/**
 * @type {HTMLDivElement}
 */

document.onkeypress = function (e) {
  const ctrl = e.metaKey || e.ctrlKey
  if (ctrl && e.key === 't') {  // ctrl/cmd + t = new tab
    e.preventDefault()
    pywebview.api.open_window()
  }
  if (ctrl && e.key === 'w') { // ctrl/cmd + w = close tab
    e.preventDefault()
    pywebview.api.close_window()
  }
}
