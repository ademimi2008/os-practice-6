"""Общий код для работы 6: константы, кольцевой буфер с проверкой инвариантов,
запуск эксперимента «производитель-потребитель» и проверка результата."""
import logging
import random
import threading
import time
from collections import Counter

BUFFER_SIZE = 5
N_PRODUCERS = 3
N_CONSUMERS = 2
N_ITEMS = 1000
TIMEOUT = 20              # сек: если потоки не завершились, считаем, что программа зависла

STOP = "STOP"             # «ядовитая таблетка»: потребитель, получив её, завершается
EMPTY = object()          # что вернёт get() при чтении из пустого буфера (нарушение)

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(threadName)s] %(message)s")
log = logging.getLogger("lab6")


class RingBuffer:
    """Кольцевой буфер БЕЗ собственной синхронизации: его защищает тот, кто им пользуется.
    Внутри проверяются инварианты 0 <= count <= size, нарушения логируются."""

    def __init__(self, size=BUFFER_SIZE):
        self.size = size
        self.slots = [None] * size
        self.head = 0           # откуда читаем
        self.tail = 0           # куда пишем
        self.count = 0
        self.max_count = 0
        self.violations = []

    def _violation(self, msg):
        self.violations.append(msg)
        if len(self.violations) <= 10:          # чтобы не засорять вывод тысячами строк
            log.error(msg)

    def put(self, item):
        if self.count >= self.size:
            self._violation(f"ПЕРЕПОЛНЕНИЕ буфера: put({item}) при count={self.count}")
            return False                        # элемент потерян
        self.slots[self.tail] = item
        self.tail = (self.tail + 1) % self.size
        self.count += 1
        self.max_count = max(self.max_count, self.count)
        return True

    def get(self):
        if self.count <= 0:
            self._violation("ЧТЕНИЕ ИЗ ПУСТОГО буфера: get() при count=0")
            return EMPTY
        item = self.slots[self.head]
        self.slots[self.head] = None
        self.head = (self.head + 1) % self.size
        self.count -= 1
        return item


def run_experiment(title, buffer, put, get):
    """put(item) должен блокироваться, пока нет места; get() блокироваться, пока нет данных."""
    print(f"=== {title} ===")
    print(f"буфер: {BUFFER_SIZE}, производителей: {N_PRODUCERS}, "
          f"потребителей: {N_CONSUMERS}, элементов: {N_ITEMS}")

    quotas = [N_ITEMS // N_PRODUCERS + (1 if i < N_ITEMS % N_PRODUCERS else 0)
              for i in range(N_PRODUCERS)]
    produced = [[] for _ in range(N_PRODUCERS)]      # у каждого потока свой список
    consumed = [[] for _ in range(N_CONSUMERS)]

    def producer(pid):
        for seq in range(quotas[pid]):
            item = (pid, seq)                        # уникальный номер элемента
            time.sleep(random.random() * 0.0005)     # «производство» вне критической секции
            put(item)
            produced[pid].append(item)

    def consumer(cid):
        while True:
            item = get()
            if item is STOP:
                return
            if item is EMPTY:
                continue
            consumed[cid].append(item)
            time.sleep(random.random() * 0.0005)     # «обработка» вне критической секции

    prod_threads = [threading.Thread(target=producer, args=(i,), name=f"P{i}", daemon=True)
                    for i in range(N_PRODUCERS)]
    cons_threads = [threading.Thread(target=consumer, args=(i,), name=f"C{i}", daemon=True)
                    for i in range(N_CONSUMERS)]

    def stopper():                                   # после всех производителей кладём STOP
        for t in prod_threads:
            t.join()
        for _ in range(N_CONSUMERS):
            put(STOP)

    stop_thread = threading.Thread(target=stopper, name="stopper", daemon=True)

    t0 = time.perf_counter()
    for t in prod_threads + cons_threads + [stop_thread]:
        t.start()
    deadline = time.monotonic() + TIMEOUT
    for t in cons_threads + [stop_thread]:
        t.join(max(0.0, deadline - time.monotonic()))
    elapsed = time.perf_counter() - t0
    timed_out = any(t.is_alive() for t in cons_threads + [stop_thread])

    return verify(buffer, produced, consumed, timed_out, elapsed)


def verify(buffer, produced, consumed, timed_out, elapsed):
    """Проверка инвариантов в коде. Возвращает True, если все проверки пройдены."""
    all_produced = [x for lst in produced for x in lst]
    all_consumed = [x for lst in consumed for x in lst]
    counts = Counter(all_consumed)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    missing = set(all_produced) - set(all_consumed)
    foreign = set(all_consumed) - set(all_produced)

    checks = [
        ("потоки завершились (нет взаимной блокировки)", not timed_out),
        (f"произведено {len(all_produced)} из {N_ITEMS}", len(all_produced) == N_ITEMS),
        (f"потреблено {len(all_consumed)} из {N_ITEMS}", len(all_consumed) == N_ITEMS),
        (f"элементов, потреблённых больше одного раза: {len(duplicates)}", not duplicates),
        (f"элементов потеряно (не потреблено): {len(missing)}", not missing),
        (f"посторонних элементов: {len(foreign)}", not foreign),
        (f"нарушений инварианта буфера (0 <= count <= {BUFFER_SIZE}): {len(buffer.violations)}",
         not buffer.violations),
        (f"максимальное заполнение буфера: {buffer.max_count} (лимит {BUFFER_SIZE})",
         buffer.max_count <= BUFFER_SIZE),
        (f"буфер в конце пуст (count={buffer.count})", buffer.count == 0 or timed_out),
    ]
    ok = True
    for text, passed in checks:
        print(f"  [{'OK' if passed else 'FAIL'}] {text}")
        ok &= passed
    print(f"  по потребителям: " + ", ".join(f"C{i}={len(c)}" for i, c in enumerate(consumed)))
    print(f"  время: {elapsed:.2f} с")
    print("ИТОГ:", "ВСЁ КОРРЕКТНО" if ok else "ЕСТЬ НАРУШЕНИЯ")
    return ok
