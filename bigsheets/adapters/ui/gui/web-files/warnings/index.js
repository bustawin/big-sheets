class Warnings {
  /**
   * @typedef SheetError
   * @property {string} - filename
   * @property {object} - type
   */
  /**
   * @typedef WrongRow
   * @extends SheetError
   * @property {string} - sheet_name
   * @property {Array.<string|number|null>} - row
   */
  /**
   * @typedef OpeningFileFailed
   * @extends SheetError
   * @property {string} - error
   */

  constructor () {
    /**
     *
     * @type {HTMLElement}
     */
    this.el = document.getElementById('main')
    console.assert(this.el)
  }

  async getErrors () {
    try {
      const errors = await pywebview.api.errors()
      console.info(errors)
      this.set(errors)
    } catch (e) {
      console.error(e)
      throw e
    }
  }

  /**
   * @param {Object.<string, SheetError[]>} errors
   */
  set (errors) {
    if (Object.keys(errors).length === 0) {
      this.el.innerHTML = "Hooray! No errors in here."
      return
    }
    let html = ''
    for (let [filename, _errors] of Object.entries(errors)) {
      html += `<h3>File ${filename}</h3>`
      const els = _errors.map(e => `<li>${this.printError(e)}</li>`)
      html += `<ul>${els}</ul>`
    }
    this.el.innerHTML = html
  }

  /**
   *
   * @param {SheetError} e
   */
  printError (e) {
    if (e.type === 'WrongRow') {
      return `The row is wrong: <code>${e.row}</code>.`
    } else {
      return `The file could not be opened because of <code>${e.error}</code>.`
    }
  }

}

window.addEventListener('pywebviewready', () => {
  window.warnings = new Warnings()
  window.warnings.getErrors()
})
