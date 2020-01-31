import logging
import logging.config

logging.config.fileConfig('hpotter/logging.conf')
logger = logging.getLogger('hpotter')
