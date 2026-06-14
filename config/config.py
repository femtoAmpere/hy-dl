
import os
import subprocess
import datetime

from config import secrets

telegram_token = secrets.TELEGRAM_TOKEN
telegram_users = secrets.TELEGRAM_USERS

downloads = os.path.join('.', 'downloads')

version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--long']).strip().decode('utf-8')
startup = datetime.datetime.now()
