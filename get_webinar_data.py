import os
import asyncio
from datetime import datetime
import httpx
import requests
from anyio.streams.file import FileWriteStream
from rich.pretty import pprint as print
from rich.traceback import install
from time import sleep
import json

install(show_locals=True)

DOWNLOAD_DIR = "downloads"
SKIP_MODULES = [
    "cut.end",
    "conference.add",  #
    "conference.delete",  #
    "eventsession.stop",  #
    "screensharing.stream.delete",  #
    "mediasession.update",
    "screensharing.update",  #
    "userlist.offline",
    "userlist.online",
    "conference.update",  #
    "conference.stream.delete",  #
    "eventSession.raisingHand.lowered",
    "eventSession.raisingHand.raised",
]


def fetch_event_data(event_id):
    params = {"withoutCuts": "false"}
    response = requests.get(
        f"https://events.webinar.ru/api/eventsessions/{event_id}/record",
        params=params,
    )
    data = response.json()
    return data


def process_mediasession(mediasession, start_time):
    media_type = list(mediasession["stream"].keys())[1] + ".mp4"
    time = mediasession["time"] - start_time
    url = mediasession["url"]
    return time, media_type, url


def process_message(message, start_time):
    create_at = datetime.strptime(
        message["createAt"], "%Y-%m-%dT%H:%M:%S%z"
    ).timestamp()
    time = create_at - start_time
    author_name = message["authorName"]
    text = message["text"]
    return time, author_name, text


def process_event_logs(event_logs):
    chunks = []
    files = []
    del event_logs[0]["snapshot"]

    new_event_logs = []

    for idx, event in enumerate(event_logs):
        if event["module"] != "cut.end":
            continue

        mediasessions = event["snapshot"]["data"]["mediasession"]
        for x in mediasessions:
            new_event_logs.insert(
                0, {"id": 1, "time": x["time"], "data": x, "module": "mediasession.add"}
            )

        message = event["snapshot"]["data"]["message"]
        for x in message:
            new_event_logs.insert(
                0,
                {
                    "id": 1,
                    "time": datetime.fromisoformat(x["createAt"]).timestamp(),
                    "data": x,
                    "module": "message.add",
                },
            )
        del event_logs[idx]

    event_logs.extend(new_event_logs)

    # -2 это мы чтоб не учитывали 0 элемент (старт, его пре-файером делаем), -1 -1 нужны чтобы с конца прогонять список, чтобы удалять модули лишние
    for i in range(len(event_logs) - 1, -1, -1):
        event = event_logs[i]
        module = event["module"]
        data = event["data"]
        del event["id"]

        if module in SKIP_MODULES:
            del event
            del event_logs[i]
            continue

        match module:
            case "message.add":
                keys = ["text", "authorName", "createAt"]
                event["data"] = {k: v for k, v in data.items() if k in keys}
                continue
            case "mediasession.add":
                media_type = list(data["stream"].keys())[1]
                data.update(
                    {"id": data["stream"][media_type]["id"], "media_type": media_type}
                )
                chunks.append(data["url"])
                data["file"] = data["url"].split("/")[-1]
                del data["stream"], data["time"], data["url"]
                event["data"] = data
                continue
            case "presentation.update":
                reference = data["fileReference"]
                file = reference["file"]
                slide = reference["slide"]
                event["data"] = {"file": slide["url"].split("/")[-1]}
                files.append((file["name"], file["url"]))
                chunks.append(slide["url"])
                continue
            case _:
                pass
    event_logs = sorted(event_logs, key=lambda x: x["time"], reverse=False)
    return chunks, files, event_logs


async def download_file(path, url, client):
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
        "Введите ссылку вебинара (пример: https://events.webinar.ru/j/21390906/100137538/record-new/1122397272) Важно без слеша в конце. Вообще нужен просто последний год, можно и его ввести"
    )
    sleep(0.1)

    event_id = int(input("Ссылка: ").split("/")[-1])
    # event_id = 1122397272
    # event_id = 1794592932
    data = fetch_event_data(event_id)
    event_logs = data["eventLogs"]
    name = data["name"]
    web_dir = f"{DOWNLOAD_DIR}/{name}"

    chunks, files, event_logs = process_event_logs(event_logs)

    os.makedirs(f"{web_dir}/chunks", exist_ok=True)

    if files:
        os.makedirs(f"{web_dir}/files", exist_ok=True)

    with open(f"{web_dir}/script.json", "w") as f:
        json.dump(event_logs, f, ensure_ascii=False, indent=4)

    files = list(set(files))
    chunks = list(set(chunks))

    async with httpx.AsyncClient(timeout=600) as client:
        tasks = [
            asyncio.create_task(
                download_file(f"{web_dir}/chunks/{url.split('/')[-1]}", url, client)
            )
            for url in chunks
        ]

        tasks.extend(
            [
                asyncio.create_task(
                    download_file(f"{web_dir}/files/{name}", url, client)
                )
                for name, url in files
            ]
        )
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
