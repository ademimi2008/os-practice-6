#!/usr/bin/env python3
"""Производитель-потребитель: кольцевой буфер на 5 элементов, мьютекс + условные переменные."""
import threading

from common import BUFFER_SIZE, RingBuffer, run_experiment

buffer = RingBuffer()
mutex = threading.Lock()
not_full = threading.Condition(mutex)     # «в буфере есть место»  (обе условные переменные
not_empty = threading.Condition(mutex)    # «в буфере есть данные»  используют один мьютекс)


def put(item):
    with not_full:                                 # захватывает mutex
        while buffer.count == BUFFER_SIZE:         # ВСЕГДА while, не if
            not_full.wait()                        # отпускает mutex и спит
        buffer.put(item)
        not_empty.notify()                         # будим одного потребителя


def get():
    with not_empty:
        while buffer.count == 0:                   # ВСЕГДА while, не if
            not_empty.wait()
        item = buffer.get()
        not_full.notify()                          # будим одного производителя
    return item


if __name__ == "__main__":
    ok = run_experiment("Мьютекс + условные переменные", buffer, put, get)
    raise SystemExit(0 if ok else 1)
