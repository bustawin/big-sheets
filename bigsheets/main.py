from bigsheets.service.utils import setup_logging

setup_logging()

from bigsheets.app import BigSheets

bs = BigSheets()
bs.start()
