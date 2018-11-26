#!/usr/bin/python3.6
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/isr_rotation/")

from isr_rotation import app as application

