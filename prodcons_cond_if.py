#!/usr/bin/env python3
"""НЕВЕРНАЯ ВЕРСИЯ: то же, что prodcons_cond.py, но while заменён на if (потерянное пробуждение)."""
import threading

from common import BUFFER_SIZE, RingBuffer, run_experiment

buffer = RingBuffer()
mutex = threading.Lock()
not_full = threading.Condition(mutex)     # «в буфере есть место»  (обе условные переменные
not_empty = threading.Condition(mutex)    # «в буфере есть данные»  используют один мьютекс)


def put(item):
    with not_full:                                 # захватывает mutex
        if buffer.count == BUFFER_SIZE:            # ОШИБКА: if вместо while
            not_full.wait()                        # отпускает mutex и спит
        buffer.put(item)
        not_empty.notify()                         # будим одного потребителя


def get():
    with not_empty:
        if buffer.count == 0:                      # ОШИБКА: if вместо while
            not_empty.wait()
        item = buffer.get()
        not_full.notify()                          # будим одного производителя
    return item


if __name__ == "__main__":
    ok = run_experiment("Условные переменные: if вместо while (НЕВЕРНО)", buffer, put, get)
    raise SystemExit(0 if ok else 1)
