import os
from collections import namedtuple
import asyncio
from datetime import datetime
import httpx
import requests
from anyio.streams.file import FileWriteStream
from rich.pretty import pprint as print
from rich.traceback import install
from time import sleep

install(show_locals=True)

DOWNLOAD_DIR = "downloads"
SKIP_MODULES = [
    "eventsession.stop",
    "screensharing.stream.delete",
    "mediasession.update",
    "screensharing.update",
    "userlist.offline",
    "userlist.online",
    "conference.update",
    "conference.stream.delete",
    "eventSession.raisingHand.lowered",
    "eventSession.raisingHand.raised",
]


def dict_to_object(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = dict_to_object(v)
    return namedtuple("object", d.keys())(*d.values())


def fetch_event_data(event_id):
    params = {"withoutCuts": "false"}
    response = requests.get(
        f"https://events.webinar.ru/api/eventsessions/{event_id}/record",
        params=params,
    )
    data = response.json()
    return dict_to_object(data)


def process_mediasession(mediasession, start_time):
    if isinstance(mediasession, dict):
        mediasession = dict_to_object(mediasession)
    media_type = mediasession.stream._fields[1]
    time = mediasession.time - start_time
    url = mediasession.url
    return time, media_type, url


def process_message(message, start_time):
    if isinstance(message, dict):
        message = dict_to_object(message)
    create_at = datetime.strptime(message.createAt, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    time = create_at - start_time
    author_name = message.authorName
    text = message.text
    return time, author_name, text


def process_event_logs(event_logs):
    urls = []
    messages = []
    start_time = event_logs.pop(0).get("time")

    for event in event_logs:
        event = dict_to_object(event)
        data = event.data
        module = event.module

        if module in SKIP_MODULES:
            continue

        if module == "cut.end":
            mediasession = event.snapshot.data.mediasession
            urls.extend(process_mediasession(x, start_time) for x in mediasession)
            message = event.snapshot.data.message
            messages.extend(process_message(x, start_time) for x in message)
            continue

        match module:
            case "message.add":
                messages.append(process_message(data, start_time))
            case "mediasession.add":
                urls.append(process_mediasession(data, start_time))
            case _:
                print(event)

    return urls, messages


async def download_file(time, media_type, url, client):
    path = f"{DOWNLOAD_DIR}/{time}_{media_type}.mp4"
    print(f"Старт {path}")
    async with client.stream("GET", url) as response:
        response.raise_for_status()
        async with await FileWriteStream.from_path(path) as stream:
            async for chunk in response.aiter_bytes():
                await stream.send(chunk)
    print(f"Файл {path} загружен успешно.")


async def main():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print(
        "Введите ссылку вебинара (пример: https://events.webinar.ru/21390906/1068308362/record-new/1285041197) Важно без слеша в конце. Вообще нужен просто последний год, можно и его ввести"
    )
    sleep(0.1)

    event_id = int(input("Ссылка: ").split("/")[-1])
    data = fetch_event_data(event_id)
    event_logs = data.eventLogs

    urls, messages = process_event_logs(event_logs)

    urls = list(set(urls))
    min_value = min(row[0] for row in urls)
    urls = [(row[0] - min_value, row[1], row[2]) for row in urls]

    messages = list({tuple(t): t for t in messages}.values())
    messages = [(int(max(row[0] - min_value, 0)), row[1], row[2]) for row in messages]

    with open("chat.txt", "w") as f:
        for message in messages:
            f.write(f"{str(message)}\n")

    async with httpx.AsyncClient(timeout=600) as client:
        tasks = [
            asyncio.create_task(download_file(time, media_type, url, client))
            for time, media_type, url in urls
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
