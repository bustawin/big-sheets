from bigsheets.service.utils import ensure_utf8, setup_logging

setup_logging()
ensure_utf8()

from bigsheets.app import BigSheets

bs = BigSheets()
bs.start()
