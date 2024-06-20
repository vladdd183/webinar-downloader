import subprocess

# Команда для получения информации о GPU
nvidia_smi_cmd = [
    "/usr/bin/nvidia-smi",
    # "--query-gpu=gpu_name,memory.total,memory.used,utilization.gpu",
    # "--format=csv,noheader",
]

try:
    # Запуск команды и получение ее выхода
    output = subprocess.check_output(nvidia_smi_cmd, universal_newlines=True)

    # Разбиение выхода на строки
    lines = output.strip().split("\n")

    # Обработка каждой строки (каждой GPU)
    for line in lines:
        print(line)

except subprocess.CalledProcessError as e:
    print("Error executing nvidia-smi:", e.output)
#================================================


from moviepy.editor import CompositeVideoClip, VideoFileClip
import os

from rich.traceback import install
install(show_locals=True)



# Загружаем ваши клипы
clips = [VideoFileClip(f'./clips/{x}') for x in os.listdir('./clips')]


# Объединяем клипы в один
video = CompositeVideoClip(clips)


settings_list = [
    {
        "codec": "libx264",
        "preset": "ultrafast",
        "bitrate": "2K",
        "threads": 64,
        "audio_codec": "aac",
        "ffmpeg_params": None#['-progress']
    },
    # {
    #     "codec": "mpeg4",
    #     "preset": "fast",
    #     "bitrate": "2000k",
    #     "threads": 5,
    #     "audio_codec": "aac",
    #     "ffmpeg_params": ['-loglevel', 'info']
    # },
    # Добавьте другие комбинации параметров здесь
]

# Лучшие настройки для NVIDIA (предполагаемый пресет)
nvidia_best_settings = {
    "codec": "mpeg4",
    "preset": "ultrafast",
    "bitrate": "4M",
    "threads": 64,
    "audio_codec": "aac",
    "ffmpeg_params": ['-loglevel', 'panic']
}


import time
import os

output_dir = "optimized_videos"
os.makedirs(output_dir, exist_ok=True)
print(os.popen('ffmpeg -encoders').read())
# Функция для записи видео с заданными параметрами
def export_video(settings, filename):
    start_time = time.time()
    video.write_videofile(
        filename,
        logger=None,
        codec=settings["codec"],
        preset=settings["preset"],
        bitrate=settings["bitrate"],
        threads=settings["threads"],
        audio_codec=settings["audio_codec"],
        ffmpeg_params=settings["ffmpeg_params"]
    )
    end_time = time.time()
    return end_time - start_time

# Тестируем каждый набор настроек
for i, settings in enumerate(settings_list):
    filename = os.path.join(output_dir, f"output_{i}.mp4")
    duration = export_video(settings, filename)
    print(f"Settings {i}: Time taken: {duration:.2f} seconds")

# Тестируем лучший пресет для NVIDIA
nvidia_filename = os.path.join(output_dir, "output_nvidia.mp4")
nvidia_duration = export_video(nvidia_best_settings, nvidia_filename)
print(f"NVIDIA Best Settings: Time taken: {nvidia_duration:.2f} seconds")

