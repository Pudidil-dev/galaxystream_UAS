import sys
import os
import subprocess

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

# Ensure the root directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow

def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _start_local_server():
    if os.environ.get("GALAXY_NO_SERVER") == "1":
        print("[SERVER] Auto-start disabled via GALAXY_NO_SERVER", flush=True)
        return None

    base_dir = _get_base_dir()
    server_path = os.path.join(base_dir, "wajik-anime-api.exe")
    if not os.path.exists(server_path):
        print(f"[SERVER] Server binary not found: {server_path}", flush=True)
        return None

    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = 0x08000000  # CREATE_NO_WINDOW
        proc = subprocess.Popen(
            [server_path],
            cwd=base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        print("[SERVER] wajik-anime-api started", flush=True)
        return proc
    except Exception as exc:
        print(f"[SERVER] Failed to start wajik-anime-api: {exc}", flush=True)
        return None

def _stop_local_server(proc):
    if not proc:
        return
    if proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

def main():
    """
    Fungsi utama untuk menjalankan aplikasi GalaxyStream.

    Fungsi ini mengatur environment variable untuk auto-scaling layar,
    membuat instance aplikasi Qt, mengatur nama aplikasi, membuat dan
    menampilkan jendela utama, serta menjalankan event loop aplikasi.
    """
    # Load environment variables
    if load_dotenv:
        load_dotenv()

    # Force unbuffered output for debug messages
    print("[DEBUG] Starting GalaxyStream application...", flush=True)

    if "QT_LOGGING_RULES" not in os.environ:
        os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg=false"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("GalaxyStream")

    print("[DEBUG] Creating MainWindow...", flush=True)
    server_proc = _start_local_server()
    app.aboutToQuit.connect(lambda: _stop_local_server(server_proc))
    window = MainWindow()
    window.show()

    print("[DEBUG] MainWindow shown, entering event loop...", flush=True)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
