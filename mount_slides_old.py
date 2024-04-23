#старый вариант монтирования

import os
import subprocess
from itertools import groupby
import time
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
)


def init_directory(name_directory):
    os.makedirs(name_directory, exist_ok=True)


def get_video_type(filename):
    filename = filename.lstrip("/app/downloads/")
    return filename.split("_")[-1].split(".")[0]


# есть ли в папке с загрузками картинки, или только запись экрана и вебка
def check_slides(files):
    for file in files:
        if get_video_type(file) == "slide":
            return True


def check_slide(file):
    if get_video_type(file) == "slide":
        return True


def get_start_time(filename):
    if 'FILE' not in filename:
        filename = filename.lstrip("/app/downloads/")
        return float(filename.split("_")[0])

def concatenate_conference(file_group, temp_folder):
    conference_list_file = f"{temp_folder}/conference_list.txt"
    global conference_count
    with open(conference_list_file, "a") as file:
        file.write("\n".join(
            f"file '{os.getcwd()}/{element}'" for element in file_group))

    conference_conc_mp4 = f"{temp_folder}/conference_conc_{conference_count}.mp4"
    slides_conc_ffmpeg = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        conference_list_file,
        "-preset",
        "ultrafast",
        conference_conc_mp4,
    ]
    subprocess.run(slides_conc_ffmpeg, check=True)
    conference_count += 1
    return conference_conc_mp4

# возвращает список формата "путь до файла - длина файла"
def get_main_duration(files, audio_files, temp_folder="temp"):
    # берется длина аудиофайла (файл conference без видео), иногда его почему-то нет
    try:
        find_end = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
         audio_files[-1]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        audio_from_conf = None
    except IndexError:
        audio_from_conf = concatenate_conference([file for file in files if get_video_type(file) in "conference"], temp_folder)
        find_end = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
         audio_from_conf], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    content_files = [file for file in files if 'conference' not in file]
    end = float(find_end.stdout)
    main_duration = dict()
    start_file = get_start_time(content_files[0])
    for i in range(1, len(content_files)):
        end_file = get_start_time(content_files[i])
        time_delta = end_file - start_file
        # if i == len(content_files)-1:
        #     time_delta = end - end_file
        main_duration[content_files[i - 1]] = time_delta
        start_file = end_file
    main_duration[content_files[-1]] = end - end_file
    return main_duration, audio_from_conf


def process_files(files, temp_folder, name):
    conference_files = []
    screensharing_files = []
    audio_files = []
    slides_files = []

    flag = 0
    for file in files:
        video_type = get_video_type(file)
        if video_type in "conference, screensharing":
            try:
                video = VideoFileClip(file)
                video_type = get_video_type(file)

                if video_type == "conference":
                    conference_files.append(file)
                elif video_type == "screensharing":
                    screensharing_files.append(file)
            except KeyError:
                # Здесь определяется, что файл без видеоряда (пришлось через moviepy -- иначе через ffmpeg не работало определение, либо было очень долгим)
                audio = AudioFileClip(file)
                audio_files.append(file)
        if video_type == "slide":
            slides_files.append(file)

    # список всех видеофайлов
    files_video = [file for file in files if file not in audio_files and file not in conference_files]

    # на всякий случай, если происходит чередование презентации и показа экрана, видеофайлы разделяются на группы
    subsequences = [list(file_types) for key, file_types in groupby(files_video, get_video_type)]

    # slides_list_file = f"{os.getcwd()}/{temp_folder}/slides_list.txt"
    # txt файлы для хранения списка соединяемых групп слайдов, видео и аудио
    slides_list_file = f"/app/{temp_folder}/slides_list.txt"
    screensharing_list_file = f"/app/{temp_folder}/screensharing_list.txt"

    all_vid_list_file = f"/app/{temp_folder}/all_vid_list.txt"
    all_vid = f"/app/{temp_folder}/all_vid.mp4"

    # куда сохранять итог
    final_mp4 = f"{name}.mp4"

    duration_dict, audio_from_conf = get_main_duration(files, audio_files)

    # для нумерации, если несколько групп видео/слайдов
    slides_count = 0
    screensharing_count = 0

    for file_group in subsequences:
        file_path = ''
        
        if get_video_type(file_group[0]) == "slide":
            # проходит по всем элементам, берет продолжительность (если слайд) и создает кусочки видео
            with open(slides_list_file, "w") as file:
                file.write("\n".join(
                    f"file '{element}'\nduration {duration_dict[element]}" for element in file_group))
            slides_count += 1
            slides_conc_mp4 = f"/app/slides_conc_{slides_count}.mp4"
            slides_conc_ffmpeg = [
                "ffmpeg",
                "-hwaccel",
                "cuda",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                slides_list_file,
                "-c:v",
                "h264_nvenc",
                "-preset",
                "ultrafast",
                slides_conc_mp4,
            ]
            subprocess.run(slides_conc_ffmpeg, check=True)
            file_path = slides_conc_mp4
        if get_video_type(file_group[0]) == "screensharing":
            with open(screensharing_list_file, "w") as file:
                file.write("\n".join(
                    f"file '{element}'" for element in file_group))
            screensharing_count += 1
            screensharing_conc_mp4 = f"{temp_folder}/screensharing_conc_{screensharing_count}.mp4"
            slides_conc_ffmpeg = [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                screensharing_list_file,
                "-preset",
                "ultrafast",
                screensharing_conc_mp4,
            ]
            subprocess.run(slides_conc_ffmpeg, check=True)
            file_path = screensharing_conc_mp4
        if get_video_type(file_group[0]) == "conference" and audio_from_conf is None:
            file_path = concatenate_conference(file_group, temp_folder)
        if get_video_type(file_group[0]) == "conference" and audio_from_conf:
            all_audio = audio_from_conf

        # записывает пути до всех получившихся кусочков
        with open(all_vid_list_file, "a") as file:
            file.write(f"file '/app/{file_path}'\n")

    # получение цельного видеоряда без звука
    all_videos_conc_ffmpeg = [
        "ffmpeg",
        "-hwaccel",
        "cuda",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        all_vid_list_file,
        "-c:v",
        "h264_nvenc",
        "-preset",
        "ultrafast",
        all_vid,
    ]
    subprocess.run(all_videos_conc_ffmpeg, check=True)



    # получение цельного аудиоряда ?? надо ли, учитывая, что такой файл вроде как 1, либо его нет
    if len(audio_files) != 0:
        audio_list_file = f"{temp_folder}/audio_list.txt"
        all_audio = f"{temp_folder}/audios_conc.mp4"

        with open(audio_list_file, "w") as file:
            file.write("\n".join(f"file '{os.getcwd()}/{path}'" for path in audio_files))
        all_audios_ffmpeg = [
            "ffmpeg",
            "-hwaccel",
            "cuda",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            audio_list_file,
            "-c:v",
            "h264_nvenc",
            "-preset",
            "ultrafast",
            all_audio,
        ]
        subprocess.run(all_audios_ffmpeg, check=True)


    # наконец, склеивание аудио и видео
    final_mp4_ffmpeg = [
        "ffmpeg",
        "-hwaccel",
        "cuda",
        "-i",
        all_vid,
        "-i",
        all_audio,
        "-c:v",
        "h264_nvenc",
        "-preset",
        "ultrafast",
        final_mp4,
    ]
    subprocess.run(final_mp4_ffmpeg,  check=True)


def main():
    c_dir = os.getcwd() + '/' + 'downloads'
    files = [f"/app/downloads/{file}" for file in os.listdir("downloads")]
    files.sort(key=get_start_time)

conference_count = 0
init_directory('temp')

subprocess.call("nvidia-smi")
for file in os.listdir("/app/downloads"):
    if "FILE" in file:
        os.remove(f"/app/downloads/{file}")
files = [f"/app/downloads/{file}" for file in os.listdir("/app/downloads")]
files.sort(key=get_start_time)
process_files(files, temp_folder="temp", name="lecture1")
os.remove("temp")
