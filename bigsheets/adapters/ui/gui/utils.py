# Fixes being stuck when closing the window while JS is running
import json
import logging
import threading

import AppKit
import Foundation
from PyObjCTools import AppHelper
from webview import FOLDER_DIALOG, SAVE_DIALOG
from webview.localization import localization
from webview.platforms import cocoa

import bigsheets.service.utils

log = logging.getLogger(__name__)

#####
# Fixes being able to close the window pressing the 'x'
#####


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


#####
# Fixes being able to save a file
#####

def create_file_dialog(self, dialog_type, directory, allow_multiple, save_filename,
                       file_filter, main_thread=False):
    def create_dialog(*args):
        dialog_type = args[0]

        if dialog_type == SAVE_DIALOG:
            save_filename = args[2]

            save_dlg = AppKit.NSSavePanel.savePanel()
            save_dlg.setTitle_(localization['global.saveFile'])

            if directory:  # set initial directory
                save_dlg.setDirectoryURL_(Foundation.NSURL.fileURLWithPath_(directory))

            if save_filename:  # set file name
                save_dlg.setNameFieldStringValue_(save_filename)

            if save_dlg.runModal() == AppKit.NSFileHandlingPanelOKButton:
                self._file_name = save_dlg.filename(),
            else:
                self._file_name = None
        else:
            allow_multiple = args[1]

            open_dlg = AppKit.NSOpenPanel.openPanel()

            # Enable the selection of files in the dialog.
            open_dlg.setCanChooseFiles_(dialog_type != FOLDER_DIALOG)

            # Enable the selection of directories in the dialog.
            open_dlg.setCanChooseDirectories_(dialog_type == FOLDER_DIALOG)

            # Enable / disable multiple selection
            open_dlg.setAllowsMultipleSelection_(allow_multiple)

            # Set allowed file extensions
            if file_filter:
                open_dlg.setAllowedFileTypes_(file_filter[0][1])

                # Add a menu to choose between multiple file filters
                if len(file_filter) > 1:
                    filter_chooser = cocoa.BrowserView.FileFilterChooser.alloc().initWithFilter_(
                        file_filter)
                    open_dlg.setAccessoryView_(filter_chooser)
                    open_dlg.setAccessoryViewDisclosed_(True)

            if directory:  # set initial directory
                open_dlg.setDirectoryURL_(Foundation.NSURL.fileURLWithPath_(directory))

            if open_dlg.runModal() == AppKit.NSFileHandlingPanelOKButton:
                files = open_dlg.filenames()
                self._file_name = tuple(files)
            else:
                self._file_name = None

        if not main_thread:
            self._file_name_semaphore.release()

    if main_thread:
        create_dialog(dialog_type, allow_multiple, save_filename)
    else:
        AppHelper.callAfter(create_dialog, dialog_type, allow_multiple, save_filename)
        self._file_name_semaphore.acquire()

    return self._file_name


cocoa.BrowserView.create_file_dialog = create_file_dialog


#####
# Manages opening files
#####


class ApplicationDelegate(AppKit.NSObject):
    def application_openFile_(self, application, fileName):
        log.debug('Passed-in file is %s', fileName)
        # todo handle file
        return Foundation.YES


cocoa.BrowserView.app.setDelegate_(ApplicationDelegate.alloc().init().retain())
# Drag-and-drop event (ex. file from finder dragged-in window) is handled in
# BrowserView.webView_decidePolicyForNavigationAction_decisionHandler_
