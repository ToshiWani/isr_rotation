import sys

activate_this = '/var/www/html/rotation/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, '/var/www/html/rotation')
from isr_rotation import app as application
