"""Ditado: gravação e transcrição local em português."""

from __future__ import annotations

import gc
import json
import logging
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import numpy as np
import sounddevice as sd
from compatibilidade import migrate_preferences


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "modelos"
DATA = Path(os.environ.get("LOCALAPPDATA", str(ROOT))) / "Ditado"
MODEL_OPTIONS = {"Mais rápido — base": "base", "Mais precisão — small": "small"}
MAX_RECORDING_SECONDS = 600
os.environ["PATH"] = str(ROOT / "bin") + os.pathsep + os.environ.get("PATH", "")


def read_config():
    migrate_preferences(DATA)
    try:
        data = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def resample_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Converte o áudio em memória para os 16 kHz esperados pelo modelo."""
    audio = np.ascontiguousarray(audio, dtype=np.float32).reshape(-1)
    if sample_rate == 16000:
        return audio
    process = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
         "-f", "f32le", "-ar", str(sample_rate), "-ac", "1", "-i", "pipe:0",
         "-f", "f32le", "-ar", "16000", "-ac", "1", "pipe:1"],
        input=audio.tobytes(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=True,
    )
    return np.frombuffer(process.stdout, dtype=np.float32).copy()


class Transcriber:
    """Carrega somente um modelo por vez; reutiliza o modelo entre ditados."""

    def __init__(self):
        self.model = None
        self.name = None

    def load(self, model_name, notify=lambda message: None):
        import torch
        import whisper

        torch.set_num_threads(min(6, os.cpu_count() or 2))
        if self.name != model_name:
            # A instalação prepara os modelos. Evita download inesperado no uso.
            checkpoint = MODELS / f"{model_name}.pt"
            if not checkpoint.is_file():
                raise RuntimeError(
                    "O modelo não foi encontrado. Execute Preparar modelos.cmd "
                    "com conexão à internet e tente novamente."
                )
            notify(f"Carregando o modelo {model_name}. O primeiro ditado demora mais…")
            self.model = None
            self.name = None
            gc.collect()
            self.model = whisper.load_model(str(checkpoint), device="cpu")
            self.name = model_name

    def transcribe(self, source, model_name, notify=lambda message: None):
        import whisper
        self.load(model_name, notify)
        notify("Transcrevendo em português. Aguarde…")
        if isinstance(source, (str, Path)):
            source = whisper.load_audio(str(source))
        if source.size == 0:
            return ""
        # Silêncio pode provocar palavras inventadas por modelos de transcrição.
        if float(np.max(np.abs(source))) < 0.003:
            return ""
        result = self.model.transcribe(
            source, language="pt", task="transcribe", fp16=False,
            temperature=0, beam_size=5, condition_on_previous_text=False,
            verbose=None,
        )
        return result["text"].strip()


class DictationApp:
    def __init__(self, window, *, desktop=False, instance=None):
        self.window = window
        self.desktop = desktop
        self.instance = instance
        self.tray = None
        self.hotkey = None
        self.config = read_config() if desktop else {}
        self.engine = Transcriber()
        self.events = queue.Queue()
        self.stream = None
        self.chunks = []
        self.devices = {}
        self.recording = False
        self.busy = False
        self.closing = False
        self.level = 0.0
        self.audio_warning = False
        self.started = 0.0
        self.sample_rate = 16000
        self.mic_name = tk.StringVar()
        self.model_name = tk.StringVar(value=self.config.get("mode", next(iter(MODEL_OPTIONS))))
        if self.model_name.get() not in MODEL_OPTIONS:
            self.model_name.set(next(iter(MODEL_OPTIONS)))
        self.auto_copy = tk.BooleanVar(value=self.config.get("auto_copy", True))
        self.sounds = tk.BooleanVar(value=self.config.get("sounds", True))
        self.status = tk.StringVar(value="Pronto para gravar. Escolha o microfone e clique em Iniciar gravação.")
        self.elapsed = tk.StringVar(value="00:00")
        self.count = tk.StringVar(value="0 palavras")
        self._build()
        self.refresh_microphones()
        self.window.bind("<F8>", self.toggle_recording)
        self.window.protocol("WM_DELETE_WINDOW", self.hide if desktop else self.close)
        self.model_combo.bind("<<ComboboxSelected>>", lambda event: self.save_config())
        self.mic_combo.bind("<<ComboboxSelected>>", lambda event: self.save_config())
        self.window.after(100, self.poll)
        if desktop:
            self.setup_desktop()
            self.preload()

    def _build(self):
        window = self.window
        window.title("Ditado")
        window.geometry("960x790")
        window.minsize(840, 720)
        window.configure(bg="#f4f6f8")
        style = ttk.Style(window)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("TLabel", background="#f4f6f8", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#182b3a")
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 9))
        style.configure("Primary.TButton", foreground="white", background="#116b61")
        style.map("Primary.TButton", background=[("active", "#0c5149"), ("disabled", "#a4b7b5")])
        style.configure("TCombobox", padding=5)
        outer = ttk.Frame(window, padding=24)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Dite sua ocorrência", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Ctrl+Alt+Espaço: gravar / parar em qualquer campo • Depois, Ctrl+V para colar").pack(anchor="w", pady=(4, 15))

        options = ttk.Frame(outer)
        options.pack(fill="x")
        options.columnconfigure(0, weight=1)
        ttk.Label(options, text="Microfone").grid(row=0, column=0, sticky="w")
        ttk.Label(options, text="Modo de transcrição").grid(row=0, column=2, sticky="w", padx=(14, 0))
        self.mic_combo = ttk.Combobox(options, textvariable=self.mic_name, state="readonly")
        self.mic_combo.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.refresh_button = ttk.Button(options, text="Atualizar", command=self.refresh_microphones)
        self.refresh_button.grid(row=1, column=1, padx=(8, 0))
        self.model_combo = ttk.Combobox(options, textvariable=self.model_name, values=list(MODEL_OPTIONS), state="readonly", width=25)
        self.model_combo.grid(row=1, column=2, padx=(14, 0), pady=(4, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(18, 8))
        self.record_button = ttk.Button(actions, text="Iniciar gravação (F8)", style="Primary.TButton", command=self.start_recording)
        self.record_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Parar e transcrever (F8)", command=self.stop_recording, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        self.import_button = ttk.Button(actions, text="Abrir áudio…", command=self.import_audio)
        self.import_button.pack(side="left")
        ttk.Label(actions, textvariable=self.elapsed, font=("Segoe UI", 13, "bold")).pack(side="right")
        self.meter = ttk.Progressbar(outer, maximum=100)
        self.meter.pack(fill="x", pady=(2, 9))
        ttk.Label(outer, textvariable=self.status, wraplength=850).pack(anchor="w", pady=(0, 10))

        text_header = ttk.Frame(outer)
        text_header.pack(fill="x")
        ttk.Label(text_header, text="Texto da ocorrência — revise e edite antes de colar", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(text_header, textvariable=self.count).pack(side="right")
        self.text = scrolledtext.ScrolledText(
            outer, wrap="word", font=("Segoe UI", 12), padx=14, pady=12,
            relief="solid", borderwidth=1, undo=True, height=13,
        )
        self.text.pack(fill="both", expand=True, pady=(8, 12))
        self.text.bind("<<Modified>>", self.update_count)
        footer = ttk.Frame(outer)
        footer.pack(fill="x")
        ttk.Button(footer, text="Copiar texto", style="Primary.TButton", command=self.copy_text).pack(side="left")
        ttk.Button(footer, text="Salvar .txt…", command=self.save_text).pack(side="left", padx=8)
        self.clear_button = ttk.Button(footer, text="Limpar", command=self.clear_text)
        self.clear_button.pack(side="left")
        if self.desktop:
            ttk.Button(footer, text="Ocultar painel", command=self.hide).pack(side="right")
        preferences = ttk.Frame(outer)
        preferences.pack(fill="x", pady=(12, 6))
        ttk.Checkbutton(preferences, text="Copiar automaticamente cada novo ditado", variable=self.auto_copy, command=self.save_config).pack(side="left")
        ttk.Checkbutton(preferences, text="Avisos sonoros", variable=self.sounds, command=self.save_config).pack(side="left", padx=16)
        ttk.Label(outer, text="O atalho global funciona com o painel oculto. O texto fica pronto após parar a gravação.").pack(anchor="w", pady=(4, 4))
        ttk.Label(outer, text="Fechar o painel mantém o atalho ativo. Para encerrar, use Sair no ícone perto do relógio. O áudio não é salvo.", wraplength=880, foreground="#536573").pack(anchor="w")

    def save_config(self):
        if not self.desktop:
            return
        try:
            DATA.mkdir(parents=True, exist_ok=True)
            content = {"mode": self.model_name.get(), "microphone": self.mic_name.get(),
                       "auto_copy": self.auto_copy.get(), "sounds": self.sounds.get()}
            temporary = DATA / "config.tmp"
            temporary.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(DATA / "config.json")
        except OSError:
            logging.exception("Falha ao salvar preferências")

    def setup_desktop(self):
        import pystray
        from integracao_windows import GlobalHotkey
        self.tray = pystray.Icon("Ditado", self.tray_image("#116b61"), "Ditado • Ctrl+Alt+Espaço",
            menu=pystray.Menu(
                pystray.MenuItem("Abrir painel", lambda icon, item: self.events.put(("show", None)), default=True),
                pystray.MenuItem("Gravar / parar — Ctrl+Alt+Espaço", lambda icon, item: self.events.put(("toggle", None))),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", lambda icon, item: self.events.put(("quit", None)))))
        threading.Thread(target=self.tray.run, daemon=True).start()
        self.hotkey = GlobalHotkey(lambda: self.events.put(("toggle", None)),
                                  lambda error: self.events.put(("hotkey_error", error))).start()

    @staticmethod
    def tray_image(color):
        from PIL import Image, ImageDraw
        image = Image.new("RGBA", (64, 64))
        draw = ImageDraw.Draw(image)
        draw.ellipse((1, 1, 63, 63), fill=color)
        draw.rounded_rectangle((25, 12, 39, 37), radius=7, fill="white")
        draw.arc((18, 23, 46, 47), 0, 180, fill="white", width=4)
        draw.line((32, 46, 32, 53), fill="white", width=4)
        draw.line((24, 53, 40, 53), fill="white", width=4)
        return image

    def show(self):
        self.window.deiconify()
        self.window.lift()

    def hide(self):
        self.save_config()
        self.window.withdraw()

    def notice(self, text):
        if self.tray:
            try:
                self.tray.notify(text, "Ditado")
            except Exception:
                logging.exception("Falha ao exibir notificação")

    def beep(self, state):
        if not self.desktop or not self.sounds.get():
            return
        def play():
            import winsound
            tones = {"start": [(900, 130)], "stop": [(500, 130)],
                     "ready": [(1000, 100), (1400, 150)], "error": [(300, 220)]}
            try:
                for tone, duration in tones[state]:
                    winsound.Beep(tone, duration)
            except RuntimeError:
                pass
        threading.Thread(target=play, daemon=True).start()

    def preload(self):
        self.busy = True
        self.set_controls()
        self.status.set("Preparando o Ditado. Aguarde o aviso de que está pronto…")
        self.update_tray()
        model_name = MODEL_OPTIONS[self.model_name.get()]
        def worker():
            try:
                self.engine.load(model_name)
                self.events.put(("loaded", None))
            except Exception as error:
                logging.exception("Falha ao preparar modelo")
                self.events.put(("error", str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def update_tray(self):
        if not self.tray:
            return
        state, color = (("Gravando", "#c73333") if self.recording else
                        ("Processando", "#d18b13") if self.busy else ("Pronto", "#116b61"))
        self.tray.icon = self.tray_image(color)
        self.tray.title = f"Ditado • {state} • Ctrl+Alt+Espaço"

    def refresh_microphones(self):
        try:
            # Reinicializa a enumeração para reconhecer fones conectados depois.
            sd._terminate()
            sd._initialize()
            devices = sd.query_devices()
            apis = sd.query_hostapis()
            default_index = sd.default.device[0]
            self.devices = {
                f"{index}: {device['name']} ({apis[device['hostapi']]['name']})": index
                for index, device in enumerate(devices) if device["max_input_channels"] > 0
            }
            old_name = self.mic_name.get() or self.config.get("microphone", "")
            self.mic_combo["values"] = list(self.devices)
            chosen = next((name for name, index in self.devices.items() if index == default_index), next(iter(self.devices), ""))
            self.mic_name.set(old_name if old_name in self.devices else chosen)
            if not self.devices:
                self.status.set("Nenhum microfone encontrado. Conecte um microfone e clique em Atualizar.")
            else:
                self.status.set("Pronto. Clique em Iniciar gravação e fale perto do microfone.")
            self.set_controls()
        except Exception:
            logging.exception("Falha ao listar microfones")
            self.devices = {}
            self.mic_combo["values"] = []
            self.mic_name.set("")
            self.set_controls()
            self.status.set("Não foi possível acessar o áudio. Verifique o microfone e a permissão de microfone do Windows.")

    def set_controls(self):
        available = not self.recording and not self.busy
        self.record_button.configure(state="normal" if available and self.devices else "disabled")
        self.stop_button.configure(state="normal" if self.recording else "disabled")
        for button in (self.refresh_button, self.import_button, self.clear_button):
            button.configure(state="normal" if available else "disabled")
        for combo in (self.mic_combo, self.model_combo):
            combo.configure(state="readonly" if available else "disabled")
        self.update_tray()

    def toggle_recording(self, event=None):
        if self.recording:
            self.stop_recording()
        elif not self.busy:
            self.start_recording()
        else:
            self.notice("O Ditado está processando. Aguarde o aviso antes de gravar novamente.")
        return "break"

    def start_recording(self):
        if self.recording or self.busy or not self.devices:
            return
        device_index = self.devices.get(self.mic_name.get())
        if device_index is None:
            return
        self.chunks = []
        self.level = 0.0
        self.audio_warning = False
        try:
            try:
                sd.check_input_settings(device=device_index, channels=1, dtype="float32", samplerate=16000)
                self.sample_rate = 16000
            except sd.PortAudioError:
                self.sample_rate = int(sd.query_devices(device_index)["default_samplerate"])
            self.stream = sd.InputStream(
                device=device_index, samplerate=self.sample_rate, channels=1,
                dtype="float32", callback=self.audio_callback,
            )
            self.stream.start()
        except Exception as error:
            if self.stream is not None:
                self.stream.close()
                self.stream = None
            logging.exception("Falha ao iniciar o microfone")
            self.status.set(f"Microfone indisponível: {error}")
            self.notice("Não foi possível acessar o microfone. Abra o painel para verificar o dispositivo e as permissões do Windows.")
            self.beep("error")
            if not self.desktop:
                messagebox.showerror("Microfone indisponível", str(error))
            return
        self.started = time.monotonic()
        self.recording = True
        self.status.set("Gravando… fale naturalmente. Ao terminar, clique em Parar e transcrever (ou F8).")
        self.set_controls()
        self.beep("start")

    def audio_callback(self, data, frames, timing, status):
        if status:
            self.audio_warning = True
        self.chunks.append(data[:, 0].copy())
        self.level = min(100.0, float(np.sqrt(np.mean(data * data))) * 800)

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        stream, self.stream = self.stream, None
        try:
            stream.stop()
        except Exception:
            logging.exception("Falha ao parar o microfone")
        finally:
            stream.close()
        self.beep("stop")
        self.meter["value"] = 0
        if not self.chunks:
            self.status.set("Nenhum áudio capturado. Tente outro microfone.")
            self.notice("Nenhum áudio capturado. Confira o microfone no painel.")
            self.set_controls()
            return
        audio = np.concatenate(self.chunks)
        self.chunks = []
        if audio.size / self.sample_rate < 0.5:
            self.status.set("Gravação muito curta. Grave novamente e fale por alguns segundos.")
            self.set_controls()
            self.notice("Gravação muito curta. Pressione Ctrl+Alt+Espaço e fale por alguns segundos.")
            return
        self.run_transcription(audio, self.sample_rate)

    def import_audio(self):
        filename = filedialog.askopenfilename(
            title="Escolha uma gravação para transcrever",
            filetypes=[("Áudio e vídeo", "*.wav *.mp3 *.m4a *.mp4 *.ogg *.flac *.webm *.wma *.aac"), ("Todos os arquivos", "*.*")],
        )
        if filename:
            self.elapsed.set("Arquivo")
            self.audio_warning = False
            self.run_transcription(filename)

    def run_transcription(self, source, sample_rate=None):
        self.busy = True
        self.set_controls()
        self.status.set("Preparando a transcrição…")
        self.meter.configure(mode="indeterminate")
        self.meter.start(15)
        model_name = MODEL_OPTIONS[self.model_name.get()]

        def worker():
            started = time.monotonic()
            try:
                audio = resample_audio(source, sample_rate) if sample_rate is not None else source
                result = self.engine.transcribe(audio, model_name, lambda message: self.events.put(("status", message)))
                self.events.put(("result", (result, time.monotonic() - started)))
            except Exception as error:
                logging.exception("Falha ao transcrever")
                self.events.put(("error", str(error)))

        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        if self.closing:
            return
        if self.instance and self.instance.show_requested():
            self.show()
        if self.recording:
            elapsed = int(time.monotonic() - self.started)
            self.elapsed.set(f"{elapsed // 60:02d}:{elapsed % 60:02d}")
            self.meter["value"] = self.level
            if elapsed >= MAX_RECORDING_SECONDS:
                self.stop_recording()
        while True:
            try:
                event, data = self.events.get_nowait()
            except queue.Empty:
                break
            if event == "toggle":
                if not self.devices and not self.busy:
                    self.refresh_microphones()
                if not self.devices:
                    self.notice("Nenhum microfone encontrado. Conecte um microfone e abra o painel.")
                else:
                    self.toggle_recording()
                continue
            if event == "show":
                self.show()
                continue
            if event == "quit":
                self.show()
                self.close()
                if self.closing:
                    return
                continue
            if event == "hotkey_error":
                self.status.set(data)
                self.notice(data)
                self.show()
                continue
            if event == "status":
                self.status.set(data)
                continue
            self.busy = False
            self.meter.stop()
            self.meter.configure(mode="determinate", value=0)
            self.set_controls()
            if event == "loaded":
                self.status.set("Pronto. Ctrl+Alt+Espaço para gravar; pressione novamente para parar e depois cole com Ctrl+V.")
                self.notice("Pronto! Ctrl+Alt+Espaço para gravar e parar. Aguarde o sinal e cole com Ctrl+V.")
                continue
            if event == "result":
                transcript, seconds = data
                if transcript:
                    previous = self.text.get("1.0", "end-1c").strip()
                    self.text.insert("end", ("\n\n" if previous else "") + transcript)
                    self.text.see("end")
                    self.text.edit_separator()
                    warning = " Houve interrupção no áudio; revise com atenção." if self.audio_warning else ""
                    self.status.set(f"Texto pronto em {seconds:.0f} s.{warning}")
                    if self.auto_copy.get():
                        self.copy_latest(transcript)
                    else:
                        self.notice("Texto pronto no painel. A cópia automática está desativada.")
                else:
                    self.status.set("Não foi identificada fala. Verifique o microfone e tente falar mais perto dele.")
                    self.notice("Não foi identificada fala. Confira o microfone. A área de transferência não foi alterada.")
                    self.beep("error")
            else:
                self.status.set("A transcrição não foi concluída. Você pode tentar novamente.")
                self.status.set(f"Não foi possível transcrever: {data}")
                self.notice("A transcrição falhou. Abra o painel para ver o erro e tente novamente.")
                self.beep("error")
                if not self.desktop:
                    messagebox.showerror("Não foi possível transcrever", str(data))
        self.window.after(100, self.poll)

    def copy_latest(self, text, attempt=0):
        if self.closing:
            return
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            self.window.update_idletasks()
        except tk.TclError:
            if attempt < 10:
                self.window.after(100, lambda: self.copy_latest(text, attempt + 1))
            else:
                self.status.set("Texto pronto, mas a área de transferência está ocupada. Use Copiar texto no painel.")
                self.notice("Não foi possível copiar. Seu texto está disponível no painel.")
                self.beep("error")
            return
        self.status.set("Último ditado copiado. Cole no campo desejado com Ctrl+V.")
        self.beep("ready")
        self.notice("Texto copiado! Pressione Ctrl+V no campo desejado.")

    def update_count(self, event=None):
        self.count.set(f"{len(self.text.get('1.0', 'end-1c').split())} palavras")
        self.text.edit_modified(False)

    def copy_text(self):
        text = self.text.get("1.0", "end-1c").strip()
        if not text:
            self.status.set("Grave uma fala ou escreva um texto antes de copiar.")
            return
        self.window.clipboard_clear()
        self.window.clipboard_append(text)
        self.window.update_idletasks()
        if not self.busy and not self.recording:
            self.status.set("Texto copiado. Abra o campo da ocorrência e pressione Ctrl+V.")

    def save_text(self):
        text = self.text.get("1.0", "end-1c").strip()
        if not text:
            return
        filename = filedialog.asksaveasfilename(
            title="Salvar o texto revisado", defaultextension=".txt",
            initialfile=time.strftime("ocorrencia_%Y-%m-%d_%H-%M.txt"),
            filetypes=[("Texto", "*.txt")],
        )
        if filename:
            try:
                Path(filename).write_text(text + "\n", encoding="utf-8-sig")
                self.text.edit_modified(False)
                if not self.busy and not self.recording:
                    self.status.set("Texto salvo no arquivo escolhido.")
            except OSError as error:
                messagebox.showerror("Erro ao salvar", str(error))

    def clear_text(self):
        if self.text.get("1.0", "end-1c").strip() and not messagebox.askyesno("Limpar texto", "Limpar o texto desta janela? Copie ou salve antes, se precisar."):
            return
        self.text.delete("1.0", "end")
        self.status.set("Texto limpo. Pronto para uma nova ocorrência.")

    def close(self):
        if self.recording or self.busy:
            if not messagebox.askyesno("Fechar", "Há uma gravação ou transcrição em andamento. Deseja interromper e fechar?"):
                return
        if self.text.get("1.0", "end-1c").strip():
            if not messagebox.askyesno("Fechar", "O texto não é salvo automaticamente. Já copiou ou salvou o que precisa e deseja fechar?"):
                return
        self.closing = True
        self.save_config()
        if self.stream is not None:
            self.stream.abort()
            self.stream.close()
        self.chunks = []
        if self.hotkey:
            self.hotkey.close()
        if self.tray:
            self.tray.stop()
        self.window.destroy()


def main():
    from integracao_windows import SingleInstance
    instance = SingleInstance()
    if instance.already_running:
        if "--background" not in sys.argv:
            instance.request_show()
        instance.close()
        return
    DATA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=DATA / "transcritor.log", level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    window = tk.Tk()
    if "--background" in sys.argv:
        window.withdraw()
    window.report_callback_exception = lambda kind, value, tb: (
        logging.error("Erro na janela", exc_info=(kind, value, tb)),
        messagebox.showerror("Erro", f"Ocorreu um erro. Consulte {DATA / 'transcritor.log'}."),
    )
    try:
        DictationApp(window, desktop=True, instance=instance)
        window.mainloop()
    finally:
        instance.close()


if __name__ == "__main__":
    main()
