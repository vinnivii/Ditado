"""Atalho global e instância única usando APIs do próprio Windows."""
import ctypes
from ctypes import wintypes
import threading

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
user32.GetMessageW.argtypes = (ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT)
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = (wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
user32.PostThreadMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CreateEventW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR)
kernel32.CreateEventW.restype = wintypes.HANDLE
kernel32.SetEvent.argtypes = (wintypes.HANDLE,)
kernel32.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)


class GlobalHotkey:
    def __init__(self, callback, failed):
        self.callback = callback
        self.failed = failed
        self.thread_id = None
        self.ready = threading.Event()
        self.registered = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def _run(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        self.registered = bool(user32.RegisterHotKey(None, 1, 0x4000 | 0x0002 | 0x0001, 0x20))
        self.ready.set()
        if not self.registered:
            self.failed("Ctrl+Alt+Espaço já está sendo usado por outro aplicativo. Feche-o ou use os botões do painel.")
            return
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == 0x0312 and message.wParam == 1:
                    self.callback()
        finally:
            user32.UnregisterHotKey(None, 1)
            self.registered = False

    def close(self):
        self.ready.wait(2)
        if self.thread_id and self.thread.is_alive():
            user32.PostThreadMessageW(self.thread_id, 0x0012, 0, 0)
            self.thread.join(2)


class SingleInstance:
    def __init__(self):
        self.mutex = kernel32.CreateMutexW(None, False, "Local\\WhisperDitadoV2")
        if not self.mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        self.already_running = ctypes.get_last_error() == 183
        self.show_event = kernel32.CreateEventW(None, False, False, "Local\\WhisperDitadoV2Mostrar")
        if not self.show_event:
            kernel32.CloseHandle(self.mutex)
            raise ctypes.WinError(ctypes.get_last_error())

    def request_show(self):
        kernel32.SetEvent(self.show_event)

    def show_requested(self):
        return kernel32.WaitForSingleObject(self.show_event, 0) == 0

    def close(self):
        kernel32.CloseHandle(self.show_event)
        kernel32.CloseHandle(self.mutex)
