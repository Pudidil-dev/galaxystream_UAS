"""
Anime Page - Halaman untuk browsing dan menonton anime dari Otakudesu & Kuramanime.

Fitur:
- Tab untuk Ongoing, Completed, dan Search
- Dropdown untuk memilih source (Otakudesu/Kuramanime)
- Grid layout responsive (5 kolom)
- Panel episode dan server
- Buka streaming di browser eksternal
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGridLayout, QFrame, QPushButton, QLineEdit, QComboBox,
    QButtonGroup, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl
from PySide6.QtGui import QDesktopServices
from app.ui.cards import MovieCard
from app.models.movie import Movie
from app.services.anime_client import AnimeClient


class AnimeFetcher(QThread):
    """
    Thread untuk mengambil data anime secara asynchronous.

    Menjalankan request API di background sehingga tidak memblokir UI.
    """
    dataLoaded = Signal(list)

    def __init__(self, client, source, tab, page=1, query=""):
        """
        Inisialisasi anime fetcher.

        Args:
            client: Instance AnimeClient untuk request data
            source: Source anime (otakudesu/kuramanime)
            tab: Tab yang aktif (ongoing/completed/search)
            page: Nomor halaman untuk pagination
            query: Query pencarian (untuk tab search)
        """
        super().__init__()
        self.client = client
        self.source = source
        self.tab = tab
        self.page = page
        self.query = query

    def run(self):
        """Menjalankan proses fetch data berdasarkan source dan tab."""
        print(f"[ANIME FETCHER] Starting fetch - source: {self.source}, tab: {self.tab}, page: {self.page}", flush=True)
        data = []

        try:
            if self.tab == "ongoing":
                if self.source == "otakudesu":
                    print(f"[ANIME FETCHER] Calling get_otakudesu_ongoing(page={self.page})", flush=True)
                    data = self.client.get_otakudesu_ongoing(self.page)
                else:
                    print(f"[ANIME FETCHER] Calling get_kuramanime_ongoing(page={self.page})", flush=True)
                    data = self.client.get_kuramanime_ongoing(self.page)
            elif self.tab == "completed":
                if self.source == "otakudesu":
                    print(f"[ANIME FETCHER] Calling get_otakudesu_completed(page={self.page})", flush=True)
                    data = self.client.get_otakudesu_completed(self.page)
                else:
                    print(f"[ANIME FETCHER] Calling get_kuramanime_completed(page={self.page})", flush=True)
                    data = self.client.get_kuramanime_completed(self.page)
            elif self.tab == "search" and self.query:
                if self.source == "otakudesu":
                    print(f"[ANIME FETCHER] Calling search_otakudesu(query={self.query})", flush=True)
                    data = self.client.search_otakudesu(self.query)
                else:
                    print(f"[ANIME FETCHER] Calling search_kuramanime(query={self.query})", flush=True)
                    data = self.client.search_kuramanime(self.query)

            print(f"[ANIME FETCHER] Fetch completed - got {len(data)} items", flush=True)
        except Exception as e:
            print(f"[ANIME FETCHER] Fetch error: {e}", flush=True)
            import traceback
            traceback.print_exc()

        self.dataLoaded.emit(data)


class EpisodeDetailFetcher(QThread):
    """Thread untuk mengambil detail anime dan episode list (Otakudesu only)."""
    dataLoaded = Signal(dict)

    def __init__(self, client, anime_id):
        super().__init__()
        self.client = client
        self.anime_id = anime_id

    def run(self):
        """Fetch anime detail dan episode list."""
        data = self.client.get_otakudesu_anime_detail(self.anime_id)
        self.dataLoaded.emit(data)


class ServerFetcher(QThread):
    """Thread untuk mengambil daftar server untuk episode (Otakudesu only)."""
    dataLoaded = Signal(list)

    def __init__(self, client, episode_id):
        super().__init__()
        self.client = client
        self.episode_id = episode_id

    def run(self):
        """Fetch server list untuk episode."""
        data = self.client.get_otakudesu_episode_servers(self.episode_id)
        self.dataLoaded.emit(data)


class AnimePage(QWidget):
    """
    Halaman Anime untuk browsing dan menonton anime dari Otakudesu & Kuramanime.

    Fitur utama:
    - Tab Ongoing/Completed/Search
    - Source selection (Otakudesu/Kuramanime)
    - Grid anime cards responsive
    - Episode dan server panel
    - Buka streaming di browser eksternal
    """
    loadingRequested = Signal(str)
    loadingFinished = Signal()
    animeClicked = Signal(object)  # Emit anime object when clicked

    def __init__(self, image_cache):
        """
        Inisialisasi anime page.

        Args:
            image_cache: Instance ImageCache untuk caching gambar poster
        """
        super().__init__()
        print("=" * 80, flush=True)
        print("[ANIME PAGE] __init__ called - Creating AnimePage instance", flush=True)
        print("=" * 80, flush=True)

        self.image_cache = image_cache
        self.client = AnimeClient()
        self.current_tab = "ongoing"
        self.current_source = "otakudesu"
        self.current_page = 1
        self.fetcher = None
        self.is_loading = False  # Flag to prevent double loading
        # Removed episode_fetcher and server_fetcher - moved to anime_episode_page

        print("[ANIME PAGE] About to call setup_ui()", flush=True)
        self.setup_ui()
        print("[ANIME PAGE] setup_ui() completed", flush=True)

    def setup_ui(self):
        """Menyiapkan layout dan komponen UI untuk anime page."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with controls
        self.header = QFrame()
        self.header.setFixedHeight(120)
        self.header.setStyleSheet("background: rgba(0,0,0,0.5); border-bottom: 1px solid #222;")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(40, 20, 40, 10)
        header_layout.setSpacing(15)

        # Title
        title_label = QLabel("🎬 Anime Streaming")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #E5E5E5;")
        header_layout.addWidget(title_label)

        # Control row (tabs + source + search)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)

        # Tab buttons (Ongoing, Completed, Search)
        self.tab_button_group = QButtonGroup(self)
        self.tab_button_group.setExclusive(True)

        tabs = [("Ongoing", "ongoing"), ("Completed", "completed"), ("Search", "search")]
        for label, tab_id in tabs:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255,255,255,0.1);
                    color: #888;
                    border: 1px solid #333;
                    border-radius: 6px;
                    padding: 0 20px;
                    font-weight: bold;
                }
                QPushButton:checked {
                    background-color: #E50914;
                    color: white;
                    border: 1px solid #E50914;
                }
                QPushButton:hover {
                    background-color: rgba(229, 9, 20, 0.3);
                    color: #E5E5E5;
                }
            """)
            btn.clicked.connect(lambda checked, tid=tab_id: self._on_tab_changed(tid))
            self.tab_button_group.addButton(btn)
            control_layout.addWidget(btn)
            if tab_id == "ongoing":
                btn.setChecked(True)

        control_layout.addSpacing(20)

        # Source dropdown
        source_label = QLabel("Source:")
        source_label.setStyleSheet("color: #888; font-size: 14px;")
        control_layout.addWidget(source_label)

        self.source_combo = QComboBox()
        self.source_combo.addItems(["Otakudesu", "Kuramanime"])
        self.source_combo.setFixedWidth(150)
        self.source_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: #E5E5E5;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QComboBox:hover {
                border: 1px solid #E50914;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #E5E5E5;
                selection-background-color: #E50914;
            }
        """)
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        control_layout.addWidget(self.source_combo)

        control_layout.addSpacing(20)

        # Search input (only visible when Search tab is active)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search anime...")
        self.search_input.setFixedWidth(300)
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255,255,255,0.1);
                color: #E5E5E5;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #E50914;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.hide()
        control_layout.addWidget(self.search_input)

        control_layout.addStretch()
        header_layout.addLayout(control_layout)
        layout.addWidget(self.header)

        # Main content area (grid + episode/server panel)
        main_content = QWidget()
        main_content.setStyleSheet("background: transparent;")
        main_layout = QHBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left: Scroll area with grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(40, 30, 20, 50)
        self.grid.setSpacing(20)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)  # Add scroll directly to layout, no panels

        # Don't load data on init - wait until widget is shown
        # Initial load will be triggered by showEvent

    def showEvent(self, event):
        """Handler ketika widget ditampilkan - trigger data load."""
        super().showEvent(event)
        # Only load data if grid is empty and not already loading
        if self.grid.count() == 0 and not self.is_loading:
            print("[ANIME PAGE] showEvent - triggering initial load", flush=True)
            self.load_data()

    def load_data(self):
        """Memuat data anime berdasarkan tab dan source yang aktif."""
        # Prevent double loading
        if self.is_loading:
            print("[ANIME PAGE] Already loading, skipping duplicate request", flush=True)
            return

        print(f"[ANIME PAGE] load_data called - tab: {self.current_tab}, source: {self.current_source}, page: {self.current_page}", flush=True)
        self.is_loading = True

        self._clear_grid()
        # No more panels to clear

        # Show loading
        loading_label = QLabel("Loading anime...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet("color: #888; font-size: 18px; padding: 50px;")
        self.grid.addWidget(loading_label, 0, 0, 1, 5)

        self.loadingRequested.emit(f"Loading {self.current_tab} anime from {self.current_source}...")

        # FIXED: Safe interruption dengan timeout
        if self.fetcher and self.fetcher.isRunning():
            print("[ANIME PAGE] Stopping previous fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                print("[ANIME PAGE] Forcing termination...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

        # Start new fetch
        query = self.search_input.text() if self.current_tab == "search" else ""
        print(f"[ANIME PAGE] Starting fetcher - query: '{query}'", flush=True)
        self.fetcher = AnimeFetcher(self.client, self.current_source, self.current_tab, self.current_page, query)
        self.fetcher.dataLoaded.connect(self._on_data_loaded)
        self.fetcher.start()
        print(f"[ANIME PAGE] Fetcher started", flush=True)

    def _on_tab_changed(self, tab_id):
        """Handler ketika user mengubah tab."""
        self.current_tab = tab_id
        self.current_page = 1

        # Show/hide search input
        if tab_id == "search":
            self.search_input.show()
            self.search_input.setFocus()
        else:
            self.search_input.hide()
            self.load_data()

    def _on_source_changed(self, source_text):
        """Handler ketika user mengubah source."""
        self.current_source = source_text.lower()
        self.current_page = 1
        self.load_data()

    def _on_search(self):
        """Handler ketika user menekan Enter di search input."""
        if self.current_tab == "search" and self.search_input.text().strip():
            self.load_data()

    def _clear_grid(self):
        """Membersihkan semua item dari grid layout."""
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_panels(self):
        """Membersihkan episode dan server lists."""
        self.episodes_list.clear()
        self.servers_list.clear()
        self.current_anime = None
        self.current_anime_slug = ""

    def _on_data_loaded(self, anime_list):
        """Handler ketika data anime selesai dimuat."""
        print(f"[ANIME PAGE] _on_data_loaded called - received {len(anime_list)} anime", flush=True)

        # Reset loading flag
        self.is_loading = False

        self._clear_grid()

        if not anime_list:
            print(f"[ANIME PAGE] No anime found, showing empty message", flush=True)
            empty_label = QLabel("No anime found")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #666; font-size: 16px; padding: 50px;")
            self.grid.addWidget(empty_label, 0, 0, 1, 5)
            self.loadingFinished.emit()
            return

        # Calculate columns based on width
        cols = self._calculate_columns()
        print(f"[ANIME PAGE] Grid columns: {cols}", flush=True)

        # Show anime in grid
        for i, anime in enumerate(anime_list):
            row = i // cols
            col = i % cols
            card = MovieCard(anime, self.image_cache)
            card.clicked.connect(self._on_anime_clicked)
            self.grid.addWidget(card, row, col)

        print(f"[ANIME PAGE] Grid populated with {len(anime_list)} cards", flush=True)
        self.loadingFinished.emit()

    def _calculate_columns(self) -> int:
        """Menghitung jumlah kolom berdasarkan lebar window."""
        width = self.width()
        if width >= 1200:
            return 5
        elif width >= 1000:
            return 4
        elif width >= 800:
            return 3
        else:
            return 2

    def _on_anime_clicked(self, anime: Movie):
        """Handler ketika user klik anime card - emit signal to navigate to episode page."""
        print(f"[ANIME PAGE] Anime clicked: {anime.title} (ID: {anime.id})", flush=True)
        self.animeClicked.emit(anime)  # Emit to main_window to navigate to episode page

    def resizeEvent(self, event):
        """Handler resize event untuk responsive grid."""
        super().resizeEvent(event)
        # Optionally reload grid with new column count
        # For simplicity, we keep current grid until next load

    def stop(self):
        """Menghentikan semua thread yang sedang berjalan."""
        print("[ANIME PAGE] Stopping all fetchers", flush=True)
        self.is_loading = False
        # FIXED: Safe interruption dengan timeout
        if self.fetcher and self.fetcher.isRunning():
            print("[ANIME PAGE] Stopping fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                print("[ANIME PAGE] Forcing termination...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

    def refresh(self):
        """Refresh halaman anime - reload data dari server."""
        print("[ANIME PAGE] Refresh called", flush=True)
        # Reset loading flag before loading
        self.is_loading = False
        self.load_data()

    def reset(self):
        """Reset halaman anime ke state awal."""
        print("[ANIME PAGE] Reset called", flush=True)
        self.stop()
        self._clear_grid()
        self.current_tab = "ongoing"
        self.current_source = "otakudesu"
        self.current_page = 1
        self.search_input.clear()
        self.is_loading = False
