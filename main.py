"""Замер скорости скачивания.
Использование: python speedtest.py <url> [-n 10] [--timeout 30]
"""

import argparse
import statistics as st
import sys
import time
import urllib.request


def fetch(url, timeout):
    """Возвращает (полное время, время до первого байта, время передачи, байты)."""
    req = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "User-Agent": "speedtest/1.0",
        },
    )
    start = time.perf_counter()
    size = 0
    with urllib.request.urlopen(req, timeout=timeout) as r:
        first = time.perf_counter()  # заголовки получены = первый байт ответа
        while chunk := r.read(64 * 1024):
            size += len(chunk)
    end = time.perf_counter()
    return end - start, first - start, end - first, size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("-n", type=int, default=10, help="число замеров (без прогрева)")
    p.add_argument("--timeout", type=float, default=30)
    a = p.parse_args()

    try:
        fetch(a.url, a.timeout)
        print("Прогрев: ок (не учитывается)")
    except Exception as e:
        sys.exit(f"Прогрев не удался: {e}")

    totals, ttfbs, speeds, total_bytes = [], [], [], 0
    for i in range(1, a.n + 1):
        try:
            total, ttfb, transfer, size = fetch(a.url, a.timeout)
        except Exception as e:
            print(f"#{i}: ошибка — {e}", file=sys.stderr)
            continue
        speed = size / transfer / 1e6 if transfer > 0 else 0
        totals.append(total)
        ttfbs.append(ttfb)
        speeds.append(speed)
        total_bytes += size
        print(
            f"#{i}: {size / 1e6:.2f} МБ, задержка {ttfb * 1000:.0f} мс, "
            f"передача {transfer:.3f} с, {speed:.2f} МБ/с"
        )

    if not speeds:
        sys.exit("Ни одного успешного запроса")

    sd = st.stdev(speeds) if len(speeds) > 1 else 0
    print("-" * 50)
    print(f"Успешных запросов:    {len(speeds)}/{a.n}")
    print(f"Скачано всего:        {total_bytes / 1e6:.2f} МБ")
    print(f"Среднее время запр.:  {st.mean(totals):.3f} с")
    print(f"Медиана задержки:     {st.median(ttfbs) * 1000:.0f} мс")
    print(
        f"Скорость (медиана):   {st.median(speeds):.2f} МБ/с "
        f"({st.median(speeds) * 8:.2f} Мбит/с)"
    )
    print(f"  среднее ± откл.:    {st.mean(speeds):.2f} ± {sd:.2f} МБ/с")
    print(f"  мин / макс:         {min(speeds):.2f} / {max(speeds):.2f} МБ/с")


if __name__ == "__main__":
    main()
