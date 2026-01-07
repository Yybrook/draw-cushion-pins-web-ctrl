import socket
import threading
import queue
import time
from traceback import print_exc, format_exc
from typing import Optional


class TCPClient:
    def __init__(self):
        self.sock: Optional[socket.socket] = None
        self._connected: bool = False

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._recv_thread: Optional[threading.Thread] = None

        self._msg_queue: queue.Queue[str] = queue.Queue()

        self._last_active_ts: float = 0.0

    def _clear_queue(self):
        while not self._msg_queue.empty():
            try:
                self._msg_queue.get_nowait()
            except queue.Empty:
                break

    def is_alive(self) -> bool:
        return self._connected and self.sock is not None

    def connect(self, host: str, port: int) -> dict:
        with self._lock:

            if self.is_alive():
                return {"res": False, "info": "TCP连接已存在"}

            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(3)
                self.sock.connect((host, int(port)))
                self.sock.settimeout(1)  # recv 专用

                self._connected = True

                self._last_active_ts = time.time()

                self._clear_queue()

                self._stop_event.clear()

                self._recv_thread = threading.Thread(
                    target=self._recv_loop,
                    daemon=True
                )
                self._recv_thread.start()

                return {"res": True}
            except Exception as err:
                self._connected = False
                self.sock = None
                print_exc()
                return {"res": False, "info": str(err)}

    def disconnect(self):
        self._stop_event.set()

        with self._lock:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                finally:
                    self.sock = None
                    self._connected = False

        if self._recv_thread and self._recv_thread.is_alive():
            self._recv_thread.join(timeout=1.0)

        self._clear_queue()

    def send(self, message: str, clear_queue: bool = True, update_activate_ts: bool = True) -> dict:
        if clear_queue:
            self._clear_queue()

        with self._lock:
            if not self.is_alive():
                return {"res": False, "info": "TCP连接断开"}
            try:
                self.sock.sendall(message.encode("utf-8"))
                if update_activate_ts:
                    self._last_active_ts = time.time()
                return {"res": True}
            except Exception as err:
                print_exc()
                return {"res": False, "info": str(err)}

    def _recv_loop(self):
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    if not self.is_alive():
                        break
                    recv = self.sock.recv(2048)

                # 远端主动断开
                if not recv:
                    break

                self._last_active_ts = time.time()
                resp = recv.decode("utf-8", errors="ignore")
                self._msg_queue.put(resp)

            except socket.timeout:
                continue
            except Exception as err:
                print("Recv error:", err)
                break

    def recv(self, timeout: float = 3.0) -> Optional[str]:
        """
        从接收队列中取一条消息（阻塞）
        """
        with self._lock:
            if not self.is_alive():
                return None

        try:
            return self._msg_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def heartbeat(self, payload: str = "", interval: float = 10, max_idle=120):
        def _hb():
            while True:
                with self._lock:
                    if not self.is_alive():
                        break

                time.sleep(interval)
                if time.time() - self._last_active_ts > max_idle:
                    self.disconnect()
                    break

                res = self.send(payload or "\n" , clear_queue=False, update_activate_ts=False)
                if not res["res"]:
                    self.disconnect()
                    break

        threading.Thread(target=_hb, daemon=True).start()

    def __del__(self):
        self.disconnect()
