ace.define('ace/mode/sql-bigsheet', ['require', 'exports', 'module', 'ace/lib/oop', 'ace/mode/sql', 'ace/mode/sql_highlight_rules'], function (require, exports, module) {
    'use strict'

    var oop = require('../lib/oop')
    var SqlMode = require('./sql').Mode
    var SqlHighlightRules = require('./sql_highlight_rules').SqlHighlightRules

    class MyNewHighlightRules extends SqlHighlightRules {
      constructor () {
        super()
        const old = this.$rules.start[6].token
        const oldList = this.$keywordList

        const newKeyWordMapper = this.createKeywordMapper({
          'variable': (
            `${window._bigsheetEditor.sheetName}|${window._bigsheetEditor.headers.join('|')}`
          )
        }, 'identifier', true)
        this.$varList = this.$keywordList
        this.$keywordList = oldList

        this.$rules.start[6].token = v => {
          const t = old(v)
          return t === 'identifier' ? newKeyWordMapper(v) : t
        }
      }

    }

    class Mode extends SqlMode {
      constructor () {
        super()
        this.HighlightRules = MyNewHighlightRules
        this.$behaviour = this.$defaultBehaviour
      }

      getCompletions (...args) {
        return this.$highlightRules.$varList.map(word => ({
          name: word,
          value: word,
          score: 1,
          meta: word === window._bigsheetEditor.sheetName ? 'Name of this sheet' : 'Column in this sheet'
        })).concat(super.getCompletions(...args))
      }

    }

    (function () {

      this.lineCommentStart = '--'

      this.$id = 'ace/mode/sql-bigsheet'
      this.snippetFileId = 'ace/snippets/sql-bigsheet'
    }).call(Mode.prototype)

    exports.Mode = Mode

  }
);
(function () {
  ace.require(['ace/mode/sql-bigsheet'], function (m) {
    if (typeof module == 'object' && typeof exports == 'object' && module) {
      module.exports = m
    }
  })
})()
