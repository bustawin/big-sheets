# Fixes being stuck when closing the window while JS is running
import json
import threading

from webview.platforms import cocoa

import bigsheets.service.utils

cocoa._debug = bigsheets.service.utils.debug()


def evaluate_js(self: cocoa.BrowserView, script):
    from PyObjCTools import AppHelper
    import weakref

    self._js_waiters = getattr(self, "_js_waiters", weakref.WeakSet())

    def eval():
        self.webkit.evaluateJavaScript_completionHandler_(script, handler)

    def handler(result, error):
        JSResult.result = (
            None if result is None or result == "null" else json.loads(result)
        )
        JSResult.result_semaphore.set()

    class JSResult:
        result = None
        result_semaphore = threading.Event()

    self._js_waiters.add(JSResult.result_semaphore)

    self.loaded.wait()
    AppHelper.callAfter(eval)

    JSResult.result_semaphore.wait()
    return JSResult.result


cocoa.BrowserView.evaluate_js = evaluate_js

super_window_will_close = cocoa.BrowserView.WindowDelegate.windowWillClose_


def window_will_close(self, notification):
    i = cocoa.BrowserView.get_instance("window", notification.object())
    super_window_will_close(self, notification)
    i.release_js()


cocoa.BrowserView.WindowDelegate.windowWillClose_ = window_will_close


def release_js(self):
    for w in self._js_waiters:
        w.set()


cocoa.BrowserView.release_js = release_js
