import csv
from icmplib import ping

results_file_name = "ping_results.csv"

hosts_names = [
    "google.com",
    "yandex.ru",
    "github.com",
    "rutracker-net.ru",
    "wikipedia.org",
    "nsu.ru",
    "nstu.ru",
    "apple.com",
    "vk.com",
    "mail.ru",
]

results = []

for host_name in hosts_names:
    try:
        status = ping(host_name, count=5, timeout=2)
        if not status.is_alive:
            raise RuntimeError(f"{host_name}: недоступен")
        results.append(
            {
                "Host_name": host_name,
                "Address": status.address,
                "Jitter": status.jitter,
                "Packet loss": status.packet_loss,
                "Avg RTT": status.avg_rtt,
                "Min RTT": status.min_rtt,
                "Max RTT": status.max_rtt,
            }
        )
        print(f"{host_name}: OK")
    except Exception as e:
        print(f"{host_name}: ошибка ({e})")
        results.append(
            {
                "Host_name": host_name,
                "Address": None,
                "Jitter": None,
                "Packet loss": None,
                "Avg RTT": None,
                "Min RTT": None,
                "Max RTT": None,
            }
        )

try:
    with open(results_file_name, "w", encoding="utf-8", newline="") as f:
        writter = csv.DictWriter(
            f,
            fieldnames=[
                "Host_name",
                "Address",
                "Jitter",
                "Packet loss",
                "Avg RTT",
                "Min RTT",
                "Max RTT",
            ],
        )
        writter.writeheader()
        writter.writerows(results)
        print(f"Результаты записаны в {results_file_name}")
except Exception as e:
    print(f"Ошибка при записи в файл: {e}")
