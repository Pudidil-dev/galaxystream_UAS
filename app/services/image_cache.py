import os
import sys
import requests
import hashlib
from PySide6.QtCore import QObject, Signal, QThread
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Sharing the robust session logic
def create_robust_session(verify_ssl=False):
    """
    Membuat session HTTP yang robust dengan pengaturan SSL yang permisif.

    Args:
        verify_ssl: Boolean untuk mengaktifkan/menonaktifkan verifikasi SSL (default: False)

    Returns:
        Objek Session yang sudah dikonfigurasi dengan adapter SSL khusus
    """
    from requests.adapters import HTTPAdapter
    from urllib3.util.ssl_ import create_urllib3_context

    class SSLAdapter(HTTPAdapter):
        """Adapter SSL khusus untuk menangani koneksi dengan sertifikat yang tidak valid."""
        def __init__(self, verify_ssl=True, *args, **kwargs):
            self.verify_ssl = verify_ssl
            super().__init__(*args, **kwargs)

        def init_poolmanager(self, *args, **kwargs):
            """Inisialisasi pool manager dengan konteks SSL yang dikustomisasi."""
            context = create_urllib3_context()
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            if not self.verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            try:
                context.set_ciphers('DEFAULT@SECLEVEL=1')
            except:
                pass
            kwargs['ssl_context'] = context
            return super().init_poolmanager(*args, **kwargs)

    session = requests.Session()
    session.verify = verify_ssl
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Connection': 'keep-alive',
        'Accept': 'image/*'
    })
    session.mount("https://", SSLAdapter(verify_ssl=verify_ssl))
    return session

class ImageDownloader(QThread):
    """
    Thread untuk mendownload gambar secara asynchronous.

    Thread ini digunakan untuk mendownload gambar dari URL tanpa memblokir UI.
    Setelah download selesai, akan mengirimkan signal dengan path file hasil download.
    """
    finished = Signal(str)

    def __init__(self, url, dest_path, session, max_retries=2):
        """
        Inisialisasi ImageDownloader.

        Args:
            url: URL gambar yang akan didownload
            dest_path: Path tujuan untuk menyimpan file gambar
            session: Session HTTP yang akan digunakan untuk download
            max_retries: Maximum number of retry attempts (default: 2)
        """
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.session = session
        self.max_retries = max_retries

    def run(self):
        """
        Menjalankan proses download gambar.

        Metode ini akan dipanggil ketika thread dimulai. Akan mendownload gambar
        dari URL yang ditentukan dan menyimpannya ke dest_path. Setelah selesai,
        akan emit signal 'finished' dengan path file atau string kosong jika gagal.

        HEIC Support: Jika file yang didownload adalah HEIC, akan dikonversi ke JPEG.
        """
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    print(f"[IMAGE DOWNLOADER] Retry attempt {attempt}/{self.max_retries}: {self.url[:80]}...")

                print(f"[IMAGE DOWNLOADER] Starting download: {self.url[:80]}...")
                response = self.session.get(self.url, timeout=30)  # Increased timeout to 30s
                print(f"[IMAGE DOWNLOADER] Response status: {response.status_code}")

                if response.status_code == 200:
                    content = response.content
                    print(f"[IMAGE DOWNLOADER] Downloaded {len(content)} bytes")

                    # Check if the downloaded content is HEIC format
                    is_heic = False
                    content_type = response.headers.get('Content-Type', '').lower()
                    print(f"[IMAGE DOWNLOADER] Content-Type: {content_type}")

                    # Check by URL extension or content-type
                    if '.heic' in self.url.lower() or 'heic' in content_type or 'heif' in content_type:
                        is_heic = True
                        print(f"[IMAGE CACHE] Detected HEIC image from URL: {self.url[:80]}...")

                    # Convert HEIC to JPEG if needed
                    if is_heic:
                        try:
                            from PIL import Image
                            from io import BytesIO

                            # Try to import pillow_heif for HEIC support
                            try:
                                from pillow_heif import register_heif_opener
                                register_heif_opener()
                                print(f"[IMAGE CACHE] Using pillow-heif for HEIC conversion")
                            except ImportError:
                                print(f"[IMAGE CACHE] pillow-heif not available, trying direct PIL conversion")

                            # Load HEIC and convert to JPEG
                            print(f"[IMAGE CACHE] Loading HEIC image...")
                            img = Image.open(BytesIO(content))
                            print(f"[IMAGE CACHE] Image loaded, mode: {img.mode}, size: {img.size}")

                            # Convert to RGB if needed (HEIC might be in different mode)
                            if img.mode in ('RGBA', 'LA', 'P'):
                                # Convert RGBA to RGB by compositing on white background
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                                img = background
                                print(f"[IMAGE CACHE] Converted from {img.mode} to RGB")
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                                print(f"[IMAGE CACHE] Converted to RGB mode")

                            # Save as JPEG
                            img.save(self.dest_path, 'JPEG', quality=90)
                            print(f"[IMAGE CACHE] Successfully converted HEIC to JPEG: {self.dest_path}")
                            self.finished.emit(self.dest_path)
                            return

                        except ImportError as e:
                            print(f"[IMAGE CACHE] Cannot convert HEIC - PIL/pillow-heif not available: {e}")
                            print(f"[IMAGE CACHE] Install pillow-heif: pip install pillow-heif")
                            # Don't retry on ImportError, just fail
                            self.finished.emit("")
                            return
                        except Exception as e:
                            print(f"[IMAGE CACHE] HEIC conversion failed: {e}")
                            import traceback
                            traceback.print_exc()
                            # Retry on conversion failure
                            if attempt < self.max_retries:
                                continue
                            else:
                                print(f"[IMAGE CACHE] All retry attempts failed for HEIC conversion")
                                self.finished.emit("")
                                return

                    # Save as normal image (JPEG, PNG, etc.)
                    print(f"[IMAGE DOWNLOADER] Saving image to: {self.dest_path}")
                    with open(self.dest_path, 'wb') as f:
                        f.write(content)
                    print(f"[IMAGE DOWNLOADER] Image saved successfully")
                    self.finished.emit(self.dest_path)
                    return
                else:
                    print(f"[IMAGE DOWNLOADER] Failed with status {response.status_code}")
                    if attempt < self.max_retries:
                        continue
                    else:
                        self.finished.emit("")
                        return

            except Exception as e:
                print(f"[IMAGE DOWNLOADER] Error downloading {self.url}: {e}")
                import traceback
                traceback.print_exc()
                if attempt < self.max_retries:
                    continue
                else:
                    print(f"[IMAGE DOWNLOADER] All retry attempts failed")
                    self.finished.emit("")
                    return

class CacheCleaner(QThread):
    """Thread untuk menghapus cache secara asynchronous agar tidak freeze UI."""
    finished = Signal()

    def __init__(self, cache_dir):
        super().__init__()
        self.cache_dir = cache_dir

    def run(self):
        """Menghapus semua file cache di background thread."""
        print(f"[CACHE CLEANER] Starting async cache clear...", flush=True)
        try:
            import shutil
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                print("[CACHE CLEANER] Cache cleared successfully", flush=True)
        except Exception as e:
            print(f"[CACHE CLEANER] Failed to clear cache: {e}", flush=True)
        self.finished.emit()


class ImageCache(QObject):
    """
    Service untuk mengelola caching gambar poster.

    Class ini menangani download dan caching gambar dari URL, menyimpannya di disk
    untuk menghindari download berulang. Menggunakan thread untuk download asynchronous
    dengan queue system untuk limit concurrent downloads.
    """
    cacheCleared = Signal()

    def __init__(self, cache_dir="cache/posters", max_concurrent_downloads=5):
        """
        Inisialisasi ImageCache.

        Args:
            cache_dir: Direktori untuk menyimpan cache gambar (default: "cache/posters")
            max_concurrent_downloads: Maximum number of concurrent downloads (default: 5)
        """
        super().__init__()

        # Determine cache directory based on running mode
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - use user's local app data
            app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
            self.cache_dir = os.path.join(app_data, 'GalaxyStream', 'cache', 'posters')
            print(f"[CACHE] Running as executable, using: {self.cache_dir}", flush=True)
        else:
            # Running in development - use relative path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.cache_dir = os.path.join(base_dir, cache_dir)
            print(f"[CACHE] Running in development, using: {self.cache_dir}", flush=True)

        # Create cache directory if it doesn't exist
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir, exist_ok=True)
                print(f"[CACHE] Created cache directory successfully", flush=True)
        except Exception as e:
            print(f"[CACHE] Error creating cache directory: {e}", flush=True)
            # Fallback to temp directory if creation fails
            import tempfile
            self.cache_dir = os.path.join(tempfile.gettempdir(), 'GalaxyStream', 'cache', 'posters')
            os.makedirs(self.cache_dir, exist_ok=True)
            print(f"[CACHE] Using fallback temp directory: {self.cache_dir}", flush=True)

        self.downloads = {}
        self._threads = []
        self.session = create_robust_session(verify_ssl=False)

        # Queue system for limiting concurrent downloads
        self.max_concurrent_downloads = max_concurrent_downloads
        self.download_queue = []  # Queue of pending downloads
        self.active_downloads = 0  # Count of active downloads

        # Cache cleaner thread (for async cache clearing)
        self._cache_cleaner = None

        print(f"[CACHE] Max concurrent downloads set to: {max_concurrent_downloads}", flush=True)

    def get_image(self, url, callback):
        """
        Mendapatkan gambar dari cache atau mendownload jika belum ada.

        Args:
            url: URL gambar yang ingin diambil
            callback: Fungsi callback yang akan dipanggil dengan path file gambar
                     ketika gambar sudah tersedia (dari cache atau setelah download)
        """
        if not url:
            print(f"[IMAGE CACHE] Empty URL provided, skipping download")
            callback("")
            return

        hashed = hashlib.md5(url.encode()).hexdigest()
        filename = f"{hashed}.jpg"
        filepath = os.path.join(self.cache_dir, filename)

        if os.path.exists(filepath):
            # Cache hit - return immediately
            callback(filepath)
            return

        if url in self.downloads:
            # Already downloading - add callback to list
            self.downloads[url].append(callback)
            return

        # New download - add to queue
        self.downloads[url] = [callback]
        self.download_queue.append((url, filepath))

        # Process queue
        self._process_queue()

    def _process_queue(self):
        """Process download queue with concurrent limit."""
        while self.active_downloads < self.max_concurrent_downloads and len(self.download_queue) > 0:
            url, filepath = self.download_queue.pop(0)

            print(f"[IMAGE CACHE] Starting download ({self.active_downloads + 1}/{self.max_concurrent_downloads}): {url[:80]}...")

            self.active_downloads += 1
            downloader = ImageDownloader(url, filepath, self.session)
            downloader.finished.connect(lambda path, u=url: self._on_download_finished(u, path))
            self._threads.append(downloader)
            downloader.start()

    def _on_download_finished(self, url, path):
        """
        Handler yang dipanggil ketika download gambar selesai.

        Args:
            url: URL gambar yang selesai didownload
            path: Path file hasil download atau string kosong jika gagal
        """
        self.active_downloads -= 1

        callbacks = self.downloads.pop(url, [])
        for cb in callbacks:
            try:
                cb(path)
            except RuntimeError:
                # Widget was deleted, skip callback
                pass

        # Clean up finished threads
        self._threads = [t for t in self._threads if not t.isFinished()]

        # Process next in queue
        self._process_queue()

    def cleanup(self):
        """
        Menghentikan semua thread download yang sedang berjalan.

        Metode ini harus dipanggil sebelum menutup aplikasi untuk memastikan
        semua thread berhenti dengan aman.
        """
        print(f"[CACHE] Cleanup: Stopping {len(self._threads)} download threads...", flush=True)

        # Clear download queue
        self.download_queue.clear()
        print(f"[CACHE] Cleared download queue", flush=True)

        # Clear downloads dict to prevent callbacks from being called
        self.downloads.clear()

        # Terminate all running threads
        for thread in self._threads:
            if thread.isRunning():
                try:
                    # Disconnect signal to prevent callback execution
                    thread.finished.disconnect()
                except:
                    pass

                # Terminate and wait
                thread.terminate()
                thread.wait(1000)

        # Clear thread list
        self._threads.clear()
        self.active_downloads = 0
        print("[CACHE] Cleanup completed", flush=True)

    def clear_cache(self, async_mode=True):
        """
        Menghapus semua gambar yang tersimpan di cache.

        Args:
            async_mode: Jika True, hapus cache di background thread (default).
                       Jika False, hapus secara synchronous (blocking).

        Metode ini akan menghapus seluruh direktori cache dan membuatnya kembali.
        """
        print(f"[CACHE] clear_cache called (async={async_mode})", flush=True)

        # Stop all downloads first
        self.cleanup()

        if async_mode:
            # Async mode - run in background thread
            print("[CACHE] Starting async cache clear...", flush=True)

            # Stop previous cleaner if still running
            if self._cache_cleaner and self._cache_cleaner.isRunning():
                print("[CACHE] Previous cleaner still running, waiting...", flush=True)
                self._cache_cleaner.wait()

            # Start new cleaner thread
            self._cache_cleaner = CacheCleaner(self.cache_dir)
            self._cache_cleaner.finished.connect(self._on_cache_cleared)
            self._cache_cleaner.start()
        else:
            # Sync mode - blocking (untuk backward compatibility)
            print("[CACHE] Starting synchronous cache clear...", flush=True)
            try:
                import shutil
                if os.path.exists(self.cache_dir):
                    shutil.rmtree(self.cache_dir)
                    os.makedirs(self.cache_dir, exist_ok=True)
                    print("[CACHE] Cache cleared successfully (sync)", flush=True)
            except Exception as e:
                print(f"[CACHE] Failed to clear cache: {e}", flush=True)
            self._on_cache_cleared()

    def _on_cache_cleared(self):
        """Handler yang dipanggil setelah cache selesai dihapus."""
        print("[CACHE] Cache clear completed, emitting signal", flush=True)
        self.cacheCleared.emit()
