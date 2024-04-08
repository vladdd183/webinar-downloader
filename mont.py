from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)
import os
from rich.traceback import install
from rich.pretty import pprint as print

install(show_locals=True)


def get_video_type(filename):
    filename = filename.lstrip("downloads/")
    return filename.split("_")[-1].split(".")[0]


def get_start_time(filename):
    filename = filename.lstrip("downloads/")
    return float(filename.split("_")[0])


# Получаем список файлов в папке downloads
files = [f"downloads/{file}" for file in os.listdir("downloads")]
# files = [
#     "downloads/3115.106999874115_conference.mp4",
#     "downloads/4828.925999879837_screensharing.mp4",
#     # ... остальные файлы
# ]

# Сортируем файлы по времени начала
files.sort(key=get_start_time)

# Создаем списки для хранения клипов конференции и скриншеринга
conference_clips = []
screensharing_clips = []
audio_clips = []


# Обрабатываем каждый файл
for file in files:
    try:
        video = VideoFileClip(file)
        video_type = get_video_type(file)

        if video_type == "conference":
            conference_clips.append(video)
        elif video_type == "screensharing":
            screensharing_clips.append(video)

        if video.audio is not None:
            audio_clips.append(video.audio)
    except KeyError:
        audio = AudioFileClip(file)
        audio_clips.append(audio)

# Определяем размеры финального видео
final_width = 1280
final_height = 720

# Создаем композицию для каждого момента времени
final_clips = []
current_time = 0

while conference_clips or screensharing_clips or audio_clips:
    current_time = min(
        get_start_time(clip.filename)
        for clip in conference_clips + screensharing_clips + audio_clips
    )

    current_conference_clip = None
    current_screensharing_clip = None
    current_audio_clip = None

    for clip in conference_clips:
        if get_start_time(clip.filename) == current_time:
            current_conference_clip = clip
            conference_clips.remove(clip)
            break

    for clip in screensharing_clips:
        if get_start_time(clip.filename) == current_time:
            current_screensharing_clip = clip
            screensharing_clips.remove(clip)
            break

    for clip in audio_clips:
        if get_start_time(clip.filename) == current_time:
            current_audio_clip = clip
            audio_clips.remove(clip)
            break
    # Проверяем, есть ли клипы для создания коллажа
    if current_conference_clip is None and current_screensharing_clip is None:
        continue

    # Определяем длительность текущего коллажа
    durations = [
        clip.duration
        for clip in [
            current_conference_clip,
            current_screensharing_clip,
            current_audio_clip,
        ]
        if clip is not None
    ]
    current_duration = min(durations) if durations else 0

    # Создаем список клипов для текущего коллажа
    current_clips = []

    if current_screensharing_clip:
        current_screensharing_clip = current_screensharing_clip.subclip(
            0, current_duration
        )
        current_screensharing_clip = current_screensharing_clip.set_position(
            (
                (final_width - current_screensharing_clip.w) // 2,
                (final_height - current_screensharing_clip.h) // 2,
            )
        )
        current_clips.append(current_screensharing_clip)

    if current_conference_clip:
        current_conference_clip = current_conference_clip.subclip(0, current_duration)
        current_conference_clip = current_conference_clip.set_position(
            (final_width // 2, 0)
        )
        current_clips.append(current_conference_clip)

    # Создаем текущий коллаж
    current_collage = CompositeVideoClip(
        current_clips, size=(final_width, final_height), bg_color=(0, 0, 0)
    )

    # Добавляем аудио к текущему коллажу
    if current_audio_clip:
        current_audio_clip = current_audio_clip.subclip(0, current_duration)
        current_collage = current_collage.set_audio(current_audio_clip)

    # Добавляем текущий коллаж в список финальных клипов
    final_clips.append(current_collage)

# Объединяем все коллажи в один финальный видеоклип
final_video = concatenate_videoclips(final_clips)

# Сохраняем финальное видео
final_video.write_videofile("output.mp4")
