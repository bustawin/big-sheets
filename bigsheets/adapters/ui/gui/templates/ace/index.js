function startEditor (sheetName, headers) {
  // Only way for our ace package to get to these variables
  window._bigsheetEditor = {headers, sheetName}

  // Init editor
  const queryEditor = ace.edit('query-editor', {
    autoScrollEditorIntoView: true,
    maxLines: 20
  })
  queryEditor.renderer.setScrollMargin(2, 2, 2, 2)
  queryEditor.setTheme('ace/theme/xcode')
  queryEditor.session.setMode('ace/mode/sql-bigsheet')
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
    exec: () => window.query.submitQuery(),
    readOnly: true // false if this command should not apply in readOnly mode
  })
  return queryEditor
}
window.startEditor = startEditor
