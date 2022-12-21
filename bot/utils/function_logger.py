import codecs
import io
import logging

FORMAT = '[%(asctime)s] [%(account_id)s] %(levelname)s - %(message)s'


def get_logger():
    file = io.BytesIO()
    file.name = 'log.txt'

    defaults = {'account_id': 0}

    logger = logging.getLogger('function_logger')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(codecs.getwriter('utf-8')(file))
    formatter = logging.Formatter(FORMAT, '%m-%d %H:%M:%S', defaults=defaults)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def update_account(id_):
        defaults['account_id'] = id_

    logger.update_account = update_account
    return logger, file

