
import subprocess

version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--long']).strip().decode('utf-8')

with open('.telegram_bot_token', 'r') as f:
    telegram_token = f.read().strip()
