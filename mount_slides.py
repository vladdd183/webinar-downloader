#тестовый вариант для проверки работы ffmpeg с gpu

import os
import subprocess
import time


def get_video_type(filename):
    filename = filename.lstrip('/app/downloads/')
    return filename.split('_')[-1].split('.')[0]


def check_slide(file):
    if get_video_type(file) == 'slide':
        return True


def test(files):
    conc_f = '/app/downloads/conc.txt'
    with open(conc_f, 'w') as f:
        for file in files:
            if check_slide(file):
                f.write(f"file '{file}'\nduration 10\n")

    
        

    slides_conc_ffmpeg = [
        'ffmpeg',
        '-y',
        '-hwaccel',
        'cuda',
        '-f',
        'concat',
        '-safe',
        '0',
        '-i',
        conc_f,
        # '-c:v',
        # 'h264_nvenc',
        # '-b:a',
        # '128k',
        # '-preset',
        # 'ultrafast',
        '/app/downloads/test_vid.mp4'
    ]
    subprocess.run(slides_conc_ffmpeg, check=True)


time.sleep(600)
# subprocess.call('nvidia-smi')
subprocess.call(['which', 'ffmpeg'])
subprocess.call('ffmpeg')
time.sleep(30)
for file in os.listdir('/app/downloads'):
    if 'FILE' in file:
        os.remove(f'/app/downloads/{file}')
files = [f'/app/downloads/{file}' for file in os.listdir('/app/downloads')]

test(files)
