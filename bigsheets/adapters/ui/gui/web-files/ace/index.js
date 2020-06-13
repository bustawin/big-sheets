/**
 * Initiates the query editor.
 * @param {string} sheetName - The name of the sheet to open.
 * @param {boolean} darkMode - Whether to use dark or light editor modes.
 * @param {function} onSubmit - Callback to execute when user submits the editor.
 */
function startEditor (sheetName, darkMode, onSubmit) {
  // Only way for our ace package to get to these variables
  const queryEditor = ace.edit('query-editor', {
    autoScrollEditorIntoView: true,
    maxLines: 20
  })
  queryEditor.renderer.setScrollMargin(2, 2, 2, 2)
  queryEditor.setTheme(darkMode ? 'ace/theme/dracula' : 'ace/theme/xcode')
  queryEditor.setOptions({
    enableLiveAutocompletion: true,
    showLineNumbers: false,
    showGutter: false,
    highlightGutterLine: false,
    tabSize: 2,
    showPrintMargin: false,
    highlightActiveLine: false,
    fontFamily: 'monospace'
  })
  queryEditor.session.setValue(`select * from ${sheetName}`)
  queryEditor.commands.addCommand({
    name: 'submit-query',
    bindKey: {win: 'Ctrl-Return', mac: 'Command-Return'},
    exec: onSubmit,
    readOnly: true // false if this command should not apply in readOnly mode
  })
  /**
   * Sets the highlighter and completions with the passed-in vars, plus
   * the pre-defined SQL ones (removing other vars previously set
   * with this method, but not the pre-defined SQL ones).
   * @param {string[]} vars
   */
  queryEditor.setVariables = (vars = []) => {
    queryEditor.session.setMode({path: 'ace/mode/sql-bigsheet', variables: vars})
  }
  queryEditor.setVariables()
  return queryEditor
}

window.startEditor = startEditor
