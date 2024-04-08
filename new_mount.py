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
