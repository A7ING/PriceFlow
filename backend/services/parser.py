import asyncio
import ipaddress
import json
import os
import shutil
import signal
import socket
import sys
import tempfile
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from services.stores import match_store

PARSE_TIMEOUT = 55.0
INTERACTIVE_QUEUE_TIMEOUT = 40.0
WORKER_MODULE = "services.parser_worker"
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MSG_BAD_URL = "Некоректне посилання. Вставте повну адресу сторінки товару (https://...)."
MSG_GOOGLE = (
    "Це рекламне або службове посилання Google. Відкрийте сторінку товару в самому магазині "
    "та скопіюйте адресу з рядка браузера."
)
MSG_PRIVATE = "Це посилання недоступне для відстеження."
MSG_DNS = "Не вдалося знайти сайт за цим посиланням. Перевірте адресу."
MSG_BUSY = "Сервер зараз перевіряє інші товари. Спробуйте за хвилину."
MSG_TIMEOUT = "Сайт завис або увімкнув захист. Спробуйте пізніше."
MSG_FAILED = "Не вдалося отримати ціну зі сторінки (можливо, сайт показав капчу або захист від ботів)."
MSG_CRASH = "Парсер аварійно завершився. Спробуйте ще раз пізніше."

TRACKING_PARAMS = {
    "gclid", "gbraid", "wbraid", "dclid", "fbclid", "yclid", "msclkid",
    "_ga", "_gl", "mc_cid", "mc_eid",
}
AD_HOSTS = ("googleadservices.com", "doubleclick.net", "googlesyndication.com")

_parse_slot = asyncio.Semaphore(1)
_interactive_active = 0


def normalize_url(url: str) -> tuple[str, str]:
    """Повертає (очищений_url, host_без_www). Кидає ValueError з текстом для користувача."""
    try:
        parsed = urlparse((url or "").strip())
        host = (parsed.hostname or "").lower().removeprefix("www.")
    except ValueError:
        raise ValueError(MSG_BAD_URL) from None

    if parsed.scheme not in ("http", "https") or not host:
        raise ValueError(MSG_BAD_URL)

    if host == "google.com" or host.startswith("google.") or any(
        host == h or host.endswith("." + h) for h in AD_HOSTS
    ):
        raise ValueError(MSG_GOOGLE)

    if match_store(host):
        query = ""
    else:
        query = urlencode(
            [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS
            ]
        )

    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, ""))
    return clean_url, host


async def _ensure_public_host(host: str) -> None:
    """Захист від SSRF: не пускаємо браузер на localhost / приватні мережі / docker-сервіси."""
    try:
        infos = await asyncio.wait_for(
            asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM), timeout=8
        )
    except (socket.gaierror, asyncio.TimeoutError, OSError):
        raise ValueError(MSG_DNS) from None

    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0].split("%")[0])
        except ValueError:
            continue
        if not ip.is_global:
            raise ValueError(MSG_PRIVATE)


def _kill_group(proc) -> None:
    """Вбиває воркер і всі його дочірні процеси (браузери)."""
    try:
        if hasattr(os, "killpg"):
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _read_result(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


async def _run_worker(clean_url: str, host: str) -> dict:
    tmp_dir = tempfile.mkdtemp(prefix="pf_parse_")
    result_path = os.path.join(tmp_dir, "result.json")
    proc = None
    collector = None
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", WORKER_MODULE, clean_url, host, result_path,
            cwd=BACKEND_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "TMPDIR": tmp_dir},
            start_new_session=True,
        )

        async def _collect() -> bytes:
            out = await proc.stdout.read()
            await proc.wait()
            return out

        collector = asyncio.ensure_future(_collect())
        done, _ = await asyncio.wait({collector}, timeout=PARSE_TIMEOUT)
        timed_out = not done
        if timed_out:
            print(f"[парсер ERROR] Таймаут {PARSE_TIMEOUT:.0f}с, вбиваю процес парсера для {host}", flush=True)
            _kill_group(proc)
            await asyncio.wait({collector}, timeout=5)

        if collector.done() and not collector.cancelled() and collector.exception() is None:
            text = collector.result().decode("utf-8", errors="replace").strip()
            if text:
                print(text[-4000:], flush=True)

        result = _read_result(result_path)
        if result is None:
            raise ValueError(MSG_TIMEOUT if timed_out else MSG_CRASH)
        if not result.get("ok"):
            print(f"[парсер ERROR] {host}: {result.get('error')}", flush=True)
            raise ValueError(MSG_FAILED)
        return result["data"]
    finally:
        if collector is not None and not collector.done():
            collector.cancel()
        if proc is not None:
            _kill_group(proc)
            if proc.returncode is None:
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    pass
        shutil.rmtree(tmp_dir, ignore_errors=True)


async def get_product_data(url: str, *, background: bool = False) -> dict:
    """Повертає {"name", "price", "image_url"}. Помилки для користувача: ValueError.
    background=True: виклик із планувальника. Він пропускає вперед запити користувачів.
    """
    global _interactive_active

    clean_url, host = normalize_url(url)
    await _ensure_public_host(host)

    if not background:
        _interactive_active += 1
    acquired = False
    try:
        if background:
            while _interactive_active > 0:
                await asyncio.sleep(2)
            await _parse_slot.acquire()
        else:
            try:
                await asyncio.wait_for(_parse_slot.acquire(), timeout=INTERACTIVE_QUEUE_TIMEOUT)
            except asyncio.TimeoutError:
                print(f"[парсер] Черга зайнята більше {INTERACTIVE_QUEUE_TIMEOUT:.0f}с, відмова для {host}", flush=True)
                raise ValueError(MSG_BUSY) from None
        acquired = True
        return await _run_worker(clean_url, host)
    finally:
        if acquired:
            _parse_slot.release()
        if not background:
            _interactive_active -= 1