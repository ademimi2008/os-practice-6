#!/usr/bin/env python3
"""ИСПРАВЛЕННАЯ ВЕРСИЯ: тот же код, но чтение-изменение-запись защищены мьютексом."""
import threading
import time

N_THREADS = 4
N_ITER = 10_000
counter = 0
lock = threading.Lock()


def worker():
    global counter
    for _ in range(N_ITER):
        with lock:               # критическая секция: только то, что трогает общие данные
            tmp = counter        # 1. прочитали
            time.sleep(0)        # 2. отдали процессор (теперь это безопасно)
            counter = tmp + 1    # 3. записали


threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
t0 = time.perf_counter()
for t in threads:
    t.start()
for t in threads:
    t.join()
elapsed = time.perf_counter() - t0

expected = N_THREADS * N_ITER
print(f"ожидалось: {expected}")
print(f"получено:  {counter}")
print(f"потеряно обновлений: {expected - counter}")
print(f"время: {elapsed:.2f} с")
print("РЕЗУЛЬТАТ:", "OK" if counter == expected else "ГОНКА ОБНАРУЖЕНА")
