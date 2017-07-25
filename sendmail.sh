#!/bin/sh
cd /var/www/html/isr_rotation
python <<EOF
from isr_rotation.mail_sender import send
send()
EOF
