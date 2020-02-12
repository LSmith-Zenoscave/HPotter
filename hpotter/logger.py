"""Global logger configured by hpotter/logging.conf
"""
import logging
import logging.config

logging.config.fileConfig('hpotter/logging.conf')
LOGGER = logging.getLogger('hpotter')
