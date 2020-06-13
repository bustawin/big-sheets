Bigsheets
#########
Open many huge CSV files in a click and query them with the power of
SQL —group by, joins, etc.

This app is for convenience; just click "open" and select a sheet,
headers are auto-detected and numbers and dates just work.

Each sheet is added as a table in a SQLite in RAM, so you can keep
opening sheets and query them as regular SQL tables.

.. image:: assets/app.readme.png

The UI is a native webview, which means that is smooth and
native-feeling while being mlutiplatform.

Built as an useful and real exercise to master Domain Driven Design
with Python —if many find it useful though we can make it *more* real.

Download
********
The software is multiplatform, but I have only built it on Mac, and
there is some care to be taken before building it for Windows and Linux:
set the style for Windows and Linux, setup py2exe for them, and optionally
find a way how to use tabs in those systems.

The Mac version is here. Just download it an place it in your
``Applications`` folder.

Installation for developers
***************************
Theoretically it should work on Windows and Linux –but not tested!

Requirements: ``Python 3.8+`` and not a very old ``nodejs``.

``pip install bigsheets``

Or clone this project and ``pip install -e . -r requirements.txt``.

Building
========
The software is multiplatform, but I have only built it on Mac, and
there is some care to be taken before building it for Windows and Linux:
set the style for Windows and Linux, and setup py2exe for them.

Mac
---
Clone this project and install it with pip.

To create the icons you will need Affinity Designer. Open the icon
file and export them at the folder where the file is, then execute
`make icons` in a terminal, generating the files pyinstaller requires.

Finally execute ``make build``.

Tested in MacOS Catalina.

Architecture
************
Explained in `my blog post <https://www.bustawin.com/big-sheets>`_.

*Yes, the name is a childish sad pun.*
