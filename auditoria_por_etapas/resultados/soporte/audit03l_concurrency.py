"""Observe real contention between two service calls in the 03-L private PostgreSQL DB."""
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event

from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction


def contest(winner, contender):
    """Hold the winner's actual service locks until the independent observer sees its waiter."""
    identities = Queue()
    ready = Event()
    release = Event()

    def worker(action, first):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                identities.put((first, cursor.fetchone()[0]))
            if first:
                with transaction.atomic():
                    value = action()
                    ready.set()
                    if not release.wait(timeout=15):
                        raise RuntimeError("Observer failed to release winner")
            else:
                if not ready.wait(timeout=12):
                    raise RuntimeError("First service did not acquire locks")
                value = action()
            return {"status": "committed", "value": value}
        except ValidationError as error:
            return {"status": "rejected", "messages": error.messages}
        finally:
            connections.close_all()

    observed = False
    wait_event = None
    category_sql = False
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(worker, winner, True)
        second = executor.submit(worker, contender, False)
        try:
            ids = dict(identities.get(timeout=10) for _ in range(2))
            if ready.wait(timeout=10):
                deadline = time.monotonic() + 7
                while not second.done() and time.monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT wait_event_type, wait_event, pg_blocking_pids(pid),
                                   position('catalog_category' in query) > 0
                            FROM pg_stat_activity WHERE pid = %s
                        """, [ids[False]])
                        waiting = cursor.fetchone()
                    if waiting and waiting[0] == "Lock" and ids[True] in waiting[2]:
                        observed = True
                        wait_event = waiting[1]
                        category_sql = waiting[3]
                        break
                    time.sleep(.025)
        finally:
            release.set()
        return {
            "winner": first.result(timeout=15), "contender": second.result(timeout=15),
            "lock_observed": observed, "blocker_matches_winner": observed,
            "distinct_connections": ids[False] != ids[True], "wait_event": wait_event,
            "waiter_statement_touches_category": category_sql,
        }
