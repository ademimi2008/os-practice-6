#!/usr/bin/env python3
"""Барьер на условной переменной: 4 потока, 3 фазы.
Запуск:  python3 barrier.py                (с барьером)
         python3 barrier.py --no-barrier   (контроль: без барьера проверка должна сработать)"""
import random
import sys
import threading
import time

PARTIES = 4
PHASES = 3


class Barrier:
    """Многоразовый барьер на мьютексе и условной переменной."""

    def __init__(self, parties, action=None):
        self.parties = parties
        self.action = action                  # вызывается ровно один раз за круг, последним потоком
        self.cond = threading.Condition()     # внутри есть мьютекс
        self.waiting = 0                      # сколько потоков уже пришли на барьер
        self.generation = 0                   # номер «круга», чтобы барьер можно было переиспользовать

    def wait(self):
        with self.cond:
            gen = self.generation
            self.waiting += 1
            if self.waiting == self.parties:      # пришёл последний
                self.waiting = 0
                self.generation += 1              # начинается новый круг
                if self.action:
                    self.action()
                self.cond.notify_all()            # будим всех ожидающих
            else:
                while gen == self.generation:     # while: защита от ложных пробуждений
                    self.cond.wait()


class NoBarrier:
    """Заглушка: ничего не ждёт. Нужна, чтобы показать, что проверка инварианта работает."""
    def wait(self):
        pass


start = time.perf_counter()
state_lock = threading.Lock()
finished = [0] * PHASES        # сколько потоков закончили каждую фазу
violations = []
print_lock = threading.Lock()


def say(text):
    with print_lock:
        print(f"[{time.perf_counter() - start:5.2f} с] {text}")


def worker(tid, barrier):
    for phase in range(PHASES):
        if phase > 0:
            # ИНВАРИАНТ: к началу фазы все потоки обязаны закончить предыдущую
            with state_lock:
                done = finished[phase - 1]
            if done != PARTIES:
                msg = (f"НАРУШЕНИЕ: поток T{tid} начал фазу {phase + 1}, "
                       f"а предыдущую закончили только {done} из {PARTIES}")
                violations.append(msg)
                say(msg)
        say(f"T{tid} начал фазу {phase + 1}")
        time.sleep(random.uniform(0.05, 0.4))      # работа разной длительности
        with state_lock:
            finished[phase] += 1
        say(f"T{tid} закончил фазу {phase + 1}, ждёт на барьере")
        barrier.wait()


if __name__ == "__main__":
    use_barrier = "--no-barrier" not in sys.argv
    rounds = [0]

    def action():
        rounds[0] += 1
        say(f"=== все {PARTIES} потока закончили фазу {rounds[0]}, барьер открыт ===")

    barrier = Barrier(PARTIES, action) if use_barrier else NoBarrier()
    print("Режим:", "С БАРЬЕРОМ" if use_barrier else "БЕЗ БАРЬЕРА (контрольный)")
    threads = [threading.Thread(target=worker, args=(i, barrier), name=f"T{i}", daemon=True)
               for i in range(PARTIES)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    if any(t.is_alive() for t in threads):
        print("ИТОГ: потоки зависли (взаимная блокировка)")
        raise SystemExit(1)
    print(f"\nнарушений инварианта: {len(violations)}")
    print("ИТОГ:", "ВСЁ КОРРЕКТНО" if not violations else "ЕСТЬ НАРУШЕНИЯ")
    raise SystemExit(0 if not violations else 1)
