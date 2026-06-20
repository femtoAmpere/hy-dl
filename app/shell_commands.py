
import subprocess
import os

import config.config as config


def sh_mount(fspath=config.downloads):
    cmd = ''

    try:
        cmd += subprocess.check_output(['umount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f'*WARNING* Failed to unmount target with {e.returncode}. Output: {e.output}')
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to unmount target with {e.returncode}', e.output
    
    try:
        cmd += subprocess.check_output(['mount', fspath], shell=False, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return e.returncode, f'*WARNING* Failed to mount target with {e.returncode}', e.output
    except Exception as e:
        return e.returncode, f'*ERROR* Failed to mount target with {e.returncode}', e.output

    return 0, cmd, ''

def sh_download_gallery_dl(url: str, update_downloader=False) -> str:
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/gallery-dl/bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'gallery-dl'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['downloaders/gallery-dl/bin/gallery-dl', '--config', 'config/.gallery-dl.conf', '--dest', f'{config.downloads}/gallery-dl', url], shell=False, text=True, stderr=subprocess.STDOUT)
        return 0, f'+**gallery-dl**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**gallery-dl** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**gallery-dl** error {e}\n', e.output

def sh_download_yt_dlp(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'yt-dlp'), exist_ok=True)
    try:
        cmd = ''
        if update_downloader:
            cmd += subprocess.check_output(['downloaders/yt-dlp', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
        cmd += subprocess.check_output(['../../downloaders/yt-dlp', url], shell=False, text=True, cwd=os.path.join(config.downloads, 'yt-dlp'), stderr=subprocess.STDOUT)
        return 0, f'+**yt-dlp**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**yt-dlp** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**yt-dlp** error {e}\n', e.output

def sh_download_megadl(url: str, update_downloader=False) -> str:
    os.makedirs(os.path.join(config.downloads, 'megadl'), exist_ok=True)
    try:
        cmd = ''
        if update_downloader:
        #     cmd += subprocess.check_output(['downloaders/megadl', '--update-to', 'nightly'], shell=False, text=True, stderr=subprocess.STDOUT)
            cmd += "No update possible for megadl.\n"
        cmd += subprocess.check_output(f'megadl {url}', shell=True, text=True, cwd=os.path.join(config.downloads, 'megadl'), stderr=subprocess.STDOUT)
        return 0, f'+**megadl**\n', cmd
    except subprocess.CalledProcessError as e:
        return e.returncode, f'-**megadl** error {e.returncode}\n', e.output
    except Exception as e:
        return e.returncode, f'-**megadl** error {e}\n', e.output
