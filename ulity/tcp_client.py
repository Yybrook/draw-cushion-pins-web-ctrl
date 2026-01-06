import socket
import threading
import queue
import time
from traceback import print_exc, format_exc


class TCPClient:
    def __init__(self):
        self.sock: socket.socket | None = None
        self.connected = False

        self.socket_lock = threading.Lock()

        self.recv_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self.msg_queue: queue.Queue[str] = queue.Queue()

    def clear_msg_queue(self):
        while True:
            try:
                self.msg_queue.get_nowait()
            except queue.Empty:
                break

    def connect(self, host: str, port: int) -> dict:
        with self.socket_lock:
            if self.connected:
                return {"res": False, "info": "connection already established"}

            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(1)
                self.sock.connect((host, int(port)))
                self.connected = True

                self.clear_msg_queue()

                self.stop_event.clear()
                self.recv_thread = threading.Thread(
                    target=self._recv_loop,
                    daemon=True
                )
                self.recv_thread.start()

                return {"res": True}
            except Exception as err:
                self.connected = False
                print_exc()
                return {"res": False, "info": str(err)}

    def disconnect(self):
        self.stop_event.set()

        self.clear_msg_queue()

        with self.socket_lock:
            if self.sock:
                try:
                    self.sock.close()
                finally:
                    self.sock = None
                    self.connected = False

    def send(self, message: str) -> dict:
        self.clear_msg_queue()

        with self.socket_lock:
            if not self.connected or not self.sock:
                return {"res": False, "info": "connection not existed"}
            try:
                self.sock.sendall(message.encode("utf-8"))
                return {"res": True}
            except Exception as err:
                # self.disconnect()
                print_exc()
                return {"res": False, "info": str(err)}

    def _recv_loop(self):
        while True:
            if self.stop_event.is_set():
                break

            try:
                with self.socket_lock:
                    recv = self.sock.recv(2048)

                if not recv:
                    time.sleep(0.1)
                    continue
                resp = recv.decode("utf-8")

                self.msg_queue.put(resp)

            except socket.timeout:
                continue
            except Exception as err:
                print("Recv error:", err)
                time.sleep(0.1)
                continue

    def recv(self, timeout: float = 3.0) -> str | None:
        """
        从接收队列中取一条消息（阻塞）
        """
        try:
            return self.msg_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def __del__(self):
        print("__del__")
