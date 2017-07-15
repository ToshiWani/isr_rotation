#!/bin/sh
python <<EOF
from flask_rotation.mail_sender import *
send()
EOF