#!/usr/bin/env python3
"""Производитель-потребитель: кольцевой буфер на 5 элементов, два семафора + мьютекс."""
import threading

from common import BUFFER_SIZE, RingBuffer, run_experiment

buffer = RingBuffer()
mutex = threading.Lock()                       # взаимное исключение для буфера
empty = threading.Semaphore(BUFFER_SIZE)       # число свободных мест
full = threading.Semaphore(0)                  # число занятых мест


def put(item):
    empty.acquire()            # 1. ждём свободное место (ВНЕ мьютекса!)
    with mutex:                # 2. критическая секция: только работа с буфером
        buffer.put(item)
    full.release()             # 3. сообщаем: появился элемент


def get():
    full.acquire()             # 1. ждём элемент (ВНЕ мьютекса!)
    with mutex:                # 2. критическая секция
        item = buffer.get()
    empty.release()            # 3. сообщаем: освободилось место
    return item


if __name__ == "__main__":
    ok = run_experiment("Семафоры + мьютекс", buffer, put, get)
    raise SystemExit(0 if ok else 1)
