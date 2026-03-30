
import os
import subprocess
import datetime

telegram_token = 'your_botfather_token_here'
telegram_users = [0, 1, 2]

downloads = os.path.join('.', 'downloads')

version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--long']).strip().decode('utf-8')
startup = datetime.datetime.now()
