"""
Browse Page - Halaman generik untuk menampilkan grid film dari berbagai kategori.
Digunakan untuk Popular, For You, Random Drama, dll.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from PySide6.QtCore import Qt, Signal, QThread
from app.ui.cards import MovieCard
from app.models.movie import Movie


class CategoryFetcher(QThread):
    """
    Thread untuk mengambil data kategori secara asynchronous.

    Thread ini menjalankan request API di background sehingga tidak memblokir
    UI saat mengambil data film dari berbagai kategori.
    """
    dataLoaded = Signal(list)

    def __init__(self, api, category):
        """
        Inisialisasi category fetcher.

        Args:
            api: Instance APIClient untuk request data
            category: Nama kategori yang akan diambil
        """
        super().__init__()
        self.api = api
        self.category = category

    def run(self):
        """
        Menjalankan proses fetch data berdasarkan kategori.

        Metode ini akan dipanggil ketika thread dimulai dan akan
        emit signal dataLoaded dengan list Movie setelah selesai.
        """
        data = []
        if self.category == "popular":
            data = self.api.get_trending()
        elif self.category == "foryou":
            data = self.api.get_foryou()
        elif self.category == "random":
            data = self.api.get_random()
        elif self.category == "latest":
            data = self.api.get_latest()
        self.dataLoaded.emit(data)


class BrowsePage(QWidget):
    """
    Halaman browse generik untuk menampilkan grid film berdasarkan kategori.

    Halaman ini digunakan untuk menampilkan berbagai kategori seperti Popular,
    For You, Random, dan Latest dengan layout grid yang dapat di-scroll.
    """
    movieClicked = Signal(object)
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    CATEGORY_TITLES = {
        "popular": "🔥 Popular Right Now",
        "foryou": "✨ Recommended For You",
        "random": "🎲 Random Drama",
        "latest": "🆕 Latest Releases",
    }

    def __init__(self, api_client, image_cache):
        """
        Inisialisasi browse page.

        Args:
            api_client: Instance APIClient untuk request data
            image_cache: Instance ImageCache untuk caching gambar poster
        """
        super().__init__()
        self.api = api_client
        self.image_cache = image_cache
        self.current_category = None
        self.fetcher = None
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout dan komponen UI untuk browse page.

        Membuat header dengan judul kategori, scroll area dengan grid layout
        untuk menampilkan movie cards, dan label loading.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self.header = QFrame()
        self.header.setFixedHeight(80)
        self.header.setStyleSheet("background: rgba(0,0,0,0.5); border-bottom: 1px solid #222;")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(40, 20, 40, 10)

        self.title_label = QLabel("Browse")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #E5E5E5;")
        header_layout.addWidget(self.title_label)
        layout.addWidget(self.header)

        # Scroll Area with Grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(40, 30, 40, 50)
        self.grid.setSpacing(20)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

        # Loading label
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #888; font-size: 18px; padding: 50px;")
        self.grid.addWidget(self.loading_label, 0, 0, 1, 5)

    def load_category(self, category: str):
        """
        Memuat kategori film tertentu.

        Args:
            category: Nama kategori yang akan dimuat (popular/foryou/random/latest)
        """
        if self.current_category == category:
            return  # Already loaded

        self.current_category = category
        self.title_label.setText(self.CATEGORY_TITLES.get(category, "Browse"))

        # Show loading
        self._clear_grid()
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #888; font-size: 18px; padding: 50px;")
        self.grid.addWidget(self.loading_label, 0, 0, 1, 5)

        # Fetch data
        self.loadingRequested.emit(f"Loading {self.CATEGORY_TITLES.get(category, 'Browse')}...")

        # FIXED: Safe interruption dengan timeout
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[BROWSE PAGE] Stopping previous fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                print("[BROWSE PAGE] Forcing termination...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

        self.fetcher = CategoryFetcher(self.api, category)
        self.fetcher.dataLoaded.connect(self._on_data_loaded)
        self.fetcher.start()

    def reset(self):
        """
        Mereset semua state dan konten halaman.

        Menghapus kategori yang sedang aktif, membersihkan grid, dan
        menghentikan fetcher yang sedang berjalan.
        """
        self.current_category = None
        self._clear_grid()
        self.title_label.setText("Browse")
        # FIXED: Safe interruption
        if self.fetcher and self.fetcher.isRunning():
            print("[BROWSE PAGE] Stopping fetcher in reset()...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                self.fetcher.terminate()
                self.fetcher.wait(500)

    def _clear_grid(self):
        """
        Membersihkan semua item dari grid layout.

        IMPORTANT: Invalidate MovieCard sebelum delete.
        """
        print(f"[BROWSE PAGE] Clearing {self.grid.count()} grid items...", flush=True)
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                # Invalidate jika MovieCard
                from app.ui.cards import MovieCard
                if isinstance(widget, MovieCard):
                    widget.invalidate()
                widget.deleteLater()
        print("[BROWSE PAGE] Grid cleared", flush=True)

    def _on_data_loaded(self, movies):
        """
        Handler yang dipanggil ketika data dari API selesai dimuat.

        Args:
            movies: List objek Movie yang dimuat dari API
        """
        self._clear_grid()

        if not movies:
            empty_label = QLabel("No content available")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 16px; padding: 50px;")
            self.grid.addWidget(empty_label, 0, 0, 1, 5)
            return

        # Show movies in a grid (5 columns)
        cols = 5
        for i, movie in enumerate(movies):
            row = i // cols
            col = i % cols
            card = MovieCard(movie, self.image_cache)
            card.clicked.connect(self.movieClicked.emit)
            self.grid.addWidget(card, row, col)

        self.loadingFinished.emit()

    def stop(self):
        """
        Menghentikan semua proses fetcher yang sedang berjalan di background.

        Metode ini harus dipanggil sebelum navigasi ke halaman lain untuk
        memastikan tidak ada thread yang masih berjalan.
        """
        # FIXED: Safe interruption
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[BROWSE PAGE] Stopping fetcher in stop()...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                self.fetcher.terminate()
                self.fetcher.wait(500)
