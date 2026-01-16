from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtGui import QPixmap, QImage, QLinearGradient, QColor, QPalette
import os

class DetailFetcher(QThread):
    """
    Thread untuk mengambil detail lengkap dan daftar episode secara asynchronous.

    Thread ini mengambil informasi detail dari movie/komik dan semua episode/chapter
    yang tersedia dari API.
    """
    finished = Signal(object, list)
    error = Signal(str)

    def __init__(self, api, movie_id):
        """
        Inisialisasi detail fetcher.

        Args:
            api: Instance APIClient untuk request data
            movie_id: ID movie/komik yang akan diambil detailnya
        """
        super().__init__()
        self.api = api
        self.movie_id = movie_id

    def run(self):
        """
        Menjalankan proses fetch detail dan episodes.

        Emit signal finished dengan objek Movie detail dan list Episodes,
        atau emit signal error jika terjadi exception.
        """
        try:
            detail = self.api.get_detail(self.movie_id)
            episodes = self.api.get_episodes(self.movie_id)
            self.finished.emit(detail, episodes)
        except Exception as e:
            self.error.emit(str(e))

class DetailPage(QtWidgets.QWidget):
    """
    Halaman detail untuk menampilkan informasi lengkap movie/drama/komik.

    Halaman ini menampilkan poster, judul, sinopsis, metadata, dan grid
    episode/chapter yang dapat diklik untuk mulai menonton/membaca.
    """
    backClicked = Signal()
    playClicked = Signal(object, int) # movie, episode_index
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, api, image_cache):
        """
        Inisialisasi detail page.

        Args:
            api: Instance APIClient untuk request data
            image_cache: Instance ImageCache untuk caching gambar
        """
        super().__init__()
        self.api = api
        self.image_cache = image_cache
        self.movie = None
        self.episodes = []
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout detail page dengan hero section dan episode grid.

        Membuat struktur scrollable yang berisi hero banner dengan poster,
        judul, sinopsis, tombol play, dan grid episode di bawahnya.
        """
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Scroll area for long synopses or episode lists
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: #0B0D12; border: none;")

        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout = QtWidgets.QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 50)
        self.layout.setSpacing(0)

        # Header Section (Hero Pattern)
        self.hero = QtWidgets.QFrame()
        self.hero.setFixedHeight(450)
        self.hero.setObjectName("DetailHero")
        self.hero_layout = QtWidgets.QVBoxLayout(self.hero)
        self.hero_layout.setContentsMargins(60, 0, 60, 40)
        self.hero_layout.setSpacing(10)

        # Back Button in Hero
        self.back_btn = QtWidgets.QPushButton("← Back")
        self.back_btn.setFixedSize(100, 40)
        self.back_btn.setStyleSheet("background: rgba(255,255,255,0.1); color: white; border: 1px solid #444; border-radius: 20px;")
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.hero_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.hero_layout.addStretch()

        # Info Container
        info_h_layout = QtWidgets.QHBoxLayout()

        # Small Poster on Left
        self.small_poster = QtWidgets.QLabel()
        self.small_poster.setFixedSize(160, 240)
        self.small_poster.setStyleSheet("background: #222; border-radius: 8px; border: 2px solid #444;")
        self.small_poster.setScaledContents(True)
        info_h_layout.addWidget(self.small_poster)

        # Text Info on Right
        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setContentsMargins(20, 0, 0, 0)

        self.title_label = QtWidgets.QLabel("Loading...")
        self.title_label.setStyleSheet("font-size: 40px; font-weight: 900; color: white;")
        text_layout.addWidget(self.title_label)

        self.meta_label = QtWidgets.QLabel("Source: Unknown • Status: Loading")
        self.meta_label.setStyleSheet("color: #E50914; font-weight: bold; font-size: 14px;")
        text_layout.addWidget(self.meta_label)

        self.synopsis_label = QtWidgets.QLabel("Fetching details...")
        self.synopsis_label.setWordWrap(True)
        self.synopsis_label.setStyleSheet("color: #AAA; font-size: 16px; line-height: 1.5;")
        self.synopsis_label.setMaximumWidth(800)
        text_layout.addWidget(self.synopsis_label)

        text_layout.addSpacing(20)

        # Main Actions
        self.play_main_btn = QtWidgets.QPushButton("▶ START WATCHING")
        self.play_main_btn.setFixedSize(200, 50)
        self.play_main_btn.setObjectName("PrimaryButton")
        self.play_main_btn.clicked.connect(lambda: self.playClicked.emit(self.movie, 0))
        text_layout.addWidget(self.play_main_btn)

        info_h_layout.addLayout(text_layout)
        info_h_layout.addStretch()

        self.hero_layout.addLayout(info_h_layout)
        self.layout.addWidget(self.hero)

        # Episode Section
        self.ep_section = QtWidgets.QWidget()
        self.ep_section.setContentsMargins(60, 40, 60, 0)
        self.ep_v_layout = QtWidgets.QVBoxLayout(self.ep_section)

        self.ep_title = QtWidgets.QLabel("Episodes")
        self.ep_title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        self.ep_v_layout.addWidget(self.ep_title)

        self.ep_grid = QtWidgets.QGridLayout()
        self.ep_grid.setSpacing(10)
        self.ep_v_layout.addLayout(self.ep_grid)

        self.layout.addWidget(self.ep_section)
        self.layout.addStretch()

        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)

    def load_movie(self, movie):
        """
        Memuat detail movie/komik yang dipilih.

        Args:
            movie: Objek Movie yang akan ditampilkan detailnya
        """
        self.movie = movie
        self.title_label.setText(movie.title)
        self.synopsis_label.setText("Fetching detailed synopsis...")
        self.meta_label.setText(f"Source: {movie.source_type.upper()}")

        if movie.poster_url:
            self.image_cache.get_image(movie.poster_url, self._on_poster_loaded)

        # Clear episodes
        while self.ep_grid.count():
            item = self.ep_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.loadingRequested.emit("Loading details...")

        # FIXED: Safe thread interruption dengan timeout wait
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[DETAIL PAGE] Stopping previous fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            # Wait dengan timeout pendek (non-blocking untuk user, tapi safe untuk thread)
            if not self.fetcher.wait(2000):  # Wait max 2 seconds
                print("[DETAIL PAGE] WARNING: Thread didn't finish in time, terminating...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(1000)
            print("[DETAIL PAGE] Previous fetcher stopped", flush=True)

        self.fetcher = DetailFetcher(self.api, movie.id)
        self.fetcher.finished.connect(self._on_details_loaded)
        self.fetcher.error.connect(lambda e: self.loadingFinished.emit())
        self.fetcher.start()

    def stop(self):
        """
        Menghentikan detail fetcher yang sedang berjalan.

        Dipanggil sebelum navigasi ke halaman lain untuk cleanup.
        """
        # FIXED: Safe interruption dengan timeout wait
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[DETAIL PAGE] Stopping fetcher in stop()...", flush=True)
            self.fetcher.requestInterruption()
            # Wait dengan timeout pendek
            if not self.fetcher.wait(1000):  # 1 second timeout
                print("[DETAIL PAGE] Forcing termination in stop()...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

    def reset(self):
        """
        Reset halaman detail ke state awal.

        CRITICAL: Dipanggil saat switch source untuk clear state Komik/Flic/dll.
        """
        print("[DETAIL PAGE] Resetting detail page...", flush=True)

        # Stop fetcher
        self.stop()

        # Clear movie state
        self.movie = None
        self.episodes = []

        # Clear UI
        self.title_label.setText("Select a title")
        self.synopsis_label.setText("Choose a movie or drama to see details")
        self.meta_label.setText("")

        # Clear poster
        self.small_poster.clear()

        # Clear episode grid
        while self.ep_grid.count():
            item = self.ep_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        print("[DETAIL PAGE] Reset completed", flush=True)

    def _on_poster_loaded(self, path):
        """
        Callback yang dipanggil ketika poster selesai didownload.

        Args:
            path: Path file gambar poster yang sudah di-cache
        """
        if path and os.path.exists(path):
            self.small_poster.setPixmap(QPixmap(path))

    def _on_details_loaded(self, detail, episodes):
        """
        Handler yang dipanggil ketika detail dan episodes selesai dimuat.

        Args:
            detail: Objek Movie dengan informasi detail lengkap
            episodes: List objek Episode yang tersedia
        """
        if detail:
            self.synopsis_label.setText(detail.synopsis or "No synopsis available.")

        self.episodes = episodes
        self.ep_title.setText(f"Chapters" if self.movie.source_type == "komik" else "Episodes")
        self.play_main_btn.setText("📖 START READING" if self.movie.source_type == "komik" else "▶ START WATCHING")

        # Populate Episodes Grid
        cols = 6
        for i, ep in enumerate(episodes):
            row = i // cols
            col = i % cols
            btn = QtWidgets.QPushButton(f"{i+1}")
            btn.setFixedSize(100, 45)
            btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a1a;
                    color: white;
                    border: 1px solid #333;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #E50914;
                    border-color: #E50914;
                }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=i: self.playClicked.emit(self.movie, idx))
            self.ep_grid.addWidget(btn, row, col)

        self.loadingFinished.emit()
