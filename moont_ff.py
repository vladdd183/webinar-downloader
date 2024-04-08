import os
import subprocess
from rich.traceback import install
from rich.pretty import pprint as print

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
)

install(show_locals=True)


def get_video_type(filename):
    filename = filename.lstrip("downloads/")
    return filename.split("_")[-1].split(".")[0]


def get_start_time(filename):
    filename = filename.lstrip("downloads/")
    return float(filename.split("_")[0])


# Получаем список файлов в папке downloads
files = [f"downloads/{file}" for file in os.listdir("downloads")]

# Сортируем файлы по времени начала
files.sort(key=get_start_time)

# Создаем списки для хранения путей к файлам конференции и скриншеринга
conference_files = []
screensharing_files = []
audio_files = []

# Обрабатываем каждый файл
for file in files:
    video_type = get_video_type(file)
    try:
        video = VideoFileClip(file)
        video_type = get_video_type(file)

        if video_type == "conference":
            conference_files.append(file)
        elif video_type == "screensharing":
            screensharing_files.append(file)

        # if video.audio is not None:
        #     audio_files.append(file)
    except KeyError:
        # Здесь определяется, что файл без видеоряда (пришлось через moviepy -- иначе через ffmpeg не работало определение, либо было очень долгим)
        audio = AudioFileClip(file)
        audio_files.append(file)

# Определяем размеры финального видео
final_width = 1280
final_height = 720

# Создаем временную папку для промежуточных файлов
temp_folder = "."
os.makedirs(temp_folder, exist_ok=True)

# Создаем файлы для списков файлов
conference_list_file = f"{temp_folder}/conference_list.txt"
screensharing_list_file = f"{temp_folder}/screensharing_list.txt"
audio_list_file = f"{temp_folder}/audio_list.txt"

# Записываем пути к файлам в соответствующие списки
with open(conference_list_file, "w") as file:
    file.write("\n".join(f"file '{path}'" for path in conference_files))

with open(screensharing_list_file, "w") as file:
    file.write("\n".join(f"file '{path}'" for path in screensharing_files))

with open(audio_list_file, "w") as file:
    file.write("\n".join(f"file '{path}'" for path in audio_files))

# Путь к выходному файлу
output_file = "output.mp4"

# Команда FFmpeg для объединения видео с использованием GPU
ffmpeg_command = [
    "ffmpeg",
    # "-hwaccel",
    # "cuda",  # Использование GPU
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    conference_list_file,
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    screensharing_list_file,
    # "-f",
    # "concat",
    # "-safe",
    # "0",
    # "-i",
    # audio_list_file,
    # "-filter_complex",
    # f"[0:v]scale={final_width//2}:{final_height}[conf];"
    # f"[1:v]scale={final_width}:{final_height}[screen];"
    # f"[screen][conf]overlay=main_w/2:0[v];"
    # f"[2:a]amerge[a]",
    # "-map",
    # "[v]",
    # "-map",
    # "[a]",
    "-c:v",
    "libx264",
    # "h264_nvenc",  # Использование GPU для кодирования видео
    "-preset",
    "fast",  # Быстрый пресет для кодирования
    "-c:a",
    "aac",
    "-b:a",
    "128k",
    output_file,
]

# Запускаем FFmpeg с помощью subprocess
subprocess.run(ffmpeg_command, check=True)

# Удаляем временную папку
os.remove(conference_list_file)
os.remove(screensharing_list_file)
os.remove(audio_list_file)
