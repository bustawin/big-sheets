Bigsheet
########


This is an app with only one domain: Sheet. If we are
to add more domains we should create a subfolder in bigsheet
like bigsheet/sheet/<move everything here> so we can add 
/bigsheet/domain2/<new stuff> and
a bigsheet/bigsheet.py as the bootstrapper of everything.

Architecture
************

Main thread (pywebview), after init -> "bootstrap" thread (runs first command)

bus for events has a threadpool of max 5 threads, bus for commands uses the same thread as the caller.

pywebview stays in the main thread running the event loop.
pywebview creates a new thread per python call from the JS bridge -> command handler in bus (same thread as before)



Generate icons
==============

Export the affinity designer using the export persona selecting the
folder where the affinity designer file is.
Then execute `make icons`, generating the files pyinstaller requires.
