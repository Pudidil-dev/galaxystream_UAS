"""
Search Page - Menampilkan hasil pencarian dalam layout grid.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame
from PySide6.QtCore import Qt, Signal, QThread
from app.ui.cards import MovieCard
from app.models.movie import Movie


class SearchFetcher(QThread):
    """
    Thread untuk mencari film secara asynchronous.

    Thread ini menjalankan pencarian di background berdasarkan query
    yang diberikan user.
    """
    dataLoaded = Signal(list)

    def __init__(self, api, query):
        """
        Inisialisasi search fetcher.

        Args:
            api: Instance APIClient untuk request data
            query: String query pencarian dari user
        """
        super().__init__()
        self.api = api
        self.query = query

    def run(self):
        """
        Menjalankan proses pencarian.

        Hanya melakukan pencarian jika query minimal 2 karakter,
        kemudian emit signal dataLoaded dengan hasil pencarian.
        """
        if self.query and len(self.query) >= 2:
            data = self.api.search(self.query)
        else:
            data = []
        self.dataLoaded.emit(data)


class SearchPage(QWidget):
    """
    Halaman untuk menampilkan hasil pencarian film/drama/komik.

    Halaman ini menampilkan hasil pencarian dalam grid layout,
    dengan state untuk query kosong, loading, hasil ditemukan, dan tidak ditemukan.
    """
    movieClicked = Signal(object)
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, api_client, image_cache):
        """
        Inisialisasi search page.

        Args:
            api_client: Instance APIClient untuk request data
            image_cache: Instance ImageCache untuk caching gambar
        """
        super().__init__()
        self.api = api_client
        self.image_cache = image_cache
        self.current_query = ""
        self.fetcher = None
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout search page dengan header dan grid results.

        Membuat header dengan judul, scroll area dengan grid layout
        untuk menampilkan hasil pencarian.
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

        self.title_label = QLabel("🔍 Search Results")
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

        # Initial state
        self._show_message("Type to search for dramas...")

    def _show_message(self, text):
        """
        Menampilkan pesan tengah di grid (untuk empty state, loading, dll).

        Args:
            text: Pesan yang akan ditampilkan
        """
        self._clear_grid()
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #666; font-size: 16px; padding: 50px;")
        self.grid.addWidget(label, 0, 0, 1, 5)

    def search(self, query: str):
        """
        Melakukan pencarian dengan query yang diberikan.

        Args:
            query: String pencarian dari user
        """
        query = query.strip()

        if len(query) < 2:
            self._show_message("Type at least 2 characters to search...")
            self.current_query = ""
            return

        if self.current_query == query:
            return  # Same query, skip

        self.current_query = query
        self.title_label.setText(f"🔍 Results for \"{query}\"")

        # Show loading
        self._show_message("Searching...")

        # Fetch data
        self.loadingRequested.emit(f"Searching for \"{query}\"...")

        # FIXED: Safe interruption dengan timeout
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[SEARCH PAGE] Stopping previous fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                print("[SEARCH PAGE] Forcing termination...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

        self.fetcher = SearchFetcher(self.api, query)
        self.fetcher.dataLoaded.connect(self._on_data_loaded)
        self.fetcher.start()

    def _clear_grid(self):
        """
        Membersihkan semua item dari grid layout.

        IMPORTANT: Invalidate MovieCard sebelum delete.
        """
        print(f"[SEARCH PAGE] Clearing {self.grid.count()} grid items...", flush=True)
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                # Invalidate jika MovieCard
                from app.ui.cards import MovieCard
                if isinstance(widget, MovieCard):
                    widget.invalidate()
                widget.deleteLater()
        print("[SEARCH PAGE] Grid cleared", flush=True)

    def _on_data_loaded(self, movies):
        """
        Handler yang dipanggil ketika hasil pencarian selesai dimuat.

        Args:
            movies: List objek Movie hasil pencarian
        """
        self._clear_grid()

        if not movies:
            self._show_message(f"No results found for \"{self.current_query}\"")
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

    def reset(self):
        """
        Membersihkan hasil pencarian dan mengembalikan ke state awal.

        Menghentikan fetcher yang sedang berjalan dan menampilkan empty state.
        """
        self.current_query = ""
        self.title_label.setText("🔍 Search")
        # FIXED: Safe interruption
        if self.fetcher and self.fetcher.isRunning():
            print("[SEARCH PAGE] Stopping fetcher in reset()...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                self.fetcher.terminate()
                self.fetcher.wait(500)
        self._show_message("Type to search for dramas...")

    def stop(self):
        """
        Metode stop yang terstandarisasi untuk cleanup.

        Memanggil reset() untuk membersihkan state halaman.
        """
        self.reset()
