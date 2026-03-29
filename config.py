
import os
import subprocess

telegram_token = 'your_botfather_token_here'
telegram_users = [0, 1, 2]

cifs_user = 'smb_user'
cifs_pass = 'smb_pass'
cifs_endpoint = '//some-server.domain/share/downloads'

downloads = os.path.join('.', 'downloads')

version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--long']).strip().decode('utf-8')
last_updated_hour = -1
