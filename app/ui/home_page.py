from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton
from PySide6.QtCore import Qt, Signal, QThread
from app.ui.cards import MovieCard
from app.models.movie import Movie

class DataFetcher(QThread):
    """
    Thread untuk mengambil data home page secara asynchronous.

    Thread ini mengambil 3 kategori sekaligus (For You, Trending, Latest)
    untuk ditampilkan di halaman home.
    """
    dataLoaded = Signal(list, list, list)

    def __init__(self, api):
        """
        Inisialisasi data fetcher untuk home page.

        Args:
            api: Instance APIClient untuk request data
        """
        super().__init__()
        self.api = api

    def run(self):
        """
        Menjalankan proses fetch data untuk 3 kategori.

        Emit signal dataLoaded dengan 3 list Movie (foryou, trending, latest)
        setelah semua data berhasil dimuat.
        """
        foryou = self.api.get_foryou()
        trending = self.api.get_trending()
        latest = self.api.get_latest()
        self.dataLoaded.emit(foryou, trending, latest)

class MovieSection(QWidget):
    """
    Widget section horizontal untuk menampilkan daftar film dalam format carousel.

    Section ini menampilkan judul kategori dan movie cards dalam scroll area horizontal,
    mirip dengan layout Netflix.
    """
    movieClicked = Signal(Movie)

    def __init__(self, title, movies, image_cache):
        """
        Inisialisasi movie section.

        Args:
            title: Judul section (contoh: "Recommended For You")
            movies: List objek Movie yang akan ditampilkan
            image_cache: Instance ImageCache untuk caching gambar
        """
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.setup_ui(title, movies, image_cache)

    def setup_ui(self, title, movies, image_cache):
        """
        Menyiapkan layout section dengan judul dan horizontal scroll.

        Args:
            title: Judul section
            movies: List objek Movie
            image_cache: Instance ImageCache
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 0, 10)
        layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #E5E5E5; background: transparent;")
        layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 40, 0)
        content_layout.setSpacing(15)

        for movie in movies:
            card = MovieCard(movie, image_cache)
            card.clicked.connect(self.movieClicked.emit)
            content_layout.addWidget(card)

        scroll.setWidget(content)
        layout.addWidget(scroll)

class HomePage(QWidget):
    """
    Halaman utama (home) aplikasi dengan hero banner dan multiple sections.

    Halaman ini menampilkan hero banner di atas dengan featured content,
    diikuti dengan beberapa section horizontal untuk kategori berbeda
    (Recommended, Popular, Latest).
    """
    movieClicked = Signal(Movie)
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, api_client, image_cache):
        """
        Inisialisasi home page.

        Args:
            api_client: Instance APIClient untuk request data
            image_cache: Instance ImageCache untuk caching gambar
        """
        super().__init__()
        self.api = api_client
        self.image_cache = image_cache
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        self._start_data_fetch()

    def setup_ui(self):
        """
        Menyiapkan layout home page dengan scroll area, hero, dan sections.

        Membuat struktur vertikal scrollable yang berisi hero banner di atas
        dan multiple movie sections di bawahnya.
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("MainScroll")
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 50)
        self.container_layout.setSpacing(0)

        # Hero
        self.hero = self._create_hero()
        self.container_layout.addWidget(self.hero)

        # Sections Holder
        self.sections_widget = QWidget()
        self.sections_widget.setStyleSheet("background: transparent;")
        self.sections_layout = QVBoxLayout(self.sections_widget)
        self.sections_layout.setSpacing(30)
        self.container_layout.addWidget(self.sections_widget)

        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)

    def _create_hero(self):
        """
        Membuat hero banner dengan featured content.

        Returns:
            QFrame widget hero banner dengan judul, deskripsi, dan tombol aksi
        """
        hero = QFrame()
        hero.setObjectName("HeroBanner")
        hero.setFixedHeight(550)
        hero.setStyleSheet("background-color: #000;")

        layout = QVBoxLayout(hero)
        layout.setContentsMargins(60, 0, 0, 80)
        layout.addStretch()

        tag = QLabel("★ #1 IN DRAMAS TODAY")
        tag.setStyleSheet("color: #E50914; font-weight: bold; font-size: 14px; background: transparent;")
        layout.addWidget(tag)

        title = QLabel("GALAXY DESTINY")
        title.setStyleSheet("font-size: 72px; font-weight: 900; color: #E5E5E5; letter-spacing: -2px; background: transparent;")
        layout.addWidget(title)

        desc = QLabel("In a future where humanity lives among the stars, one pilot must choose between his mission and the woman he loves.")
        desc.setFixedWidth(500)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #AAAAAA; font-size: 18px; line-height: 1.5; background: transparent;")
        layout.addWidget(desc)

        btn_layout = QHBoxLayout()
        play_btn = QPushButton(" ▶ Play")
        play_btn.setObjectName("PrimaryButton")
        play_btn.setFixedSize(140, 48)
        btn_layout.addWidget(play_btn)

        info_btn = QPushButton(" ⓘ More Info")
        info_btn.setObjectName("SecondaryButton")
        info_btn.setFixedSize(180, 48)
        btn_layout.addWidget(info_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return hero

    def refresh_data(self):
        """
        Membersihkan konten yang ada dan memulai fetch data baru.

        Metode ini dipanggil ketika user switch source atau refresh halaman.
        """
        self.loadingRequested.emit("Refreshing content...")

        # FIXED: Safe interruption dengan timeout wait
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[HOME PAGE] Stopping previous fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            # Wait dengan timeout pendek (non-blocking)
            if not self.fetcher.wait(1000):  # 1 second max
                print("[HOME PAGE] WARNING: Fetcher didn't stop, terminating...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

        self.clear_sections()
        self._start_data_fetch()

    def clear_sections(self):
        """
        Menghapus semua widget section dari layout.

        IMPORTANT: Invalidate semua MovieCard sebelum delete untuk
        mencegah callback image menimpa widget lain.
        """
        print(f"[HOME PAGE] Clearing {self.sections_layout.count()} sections...", flush=True)
        while self.sections_layout.count():
            item = self.sections_layout.takeAt(0)
            widget = item.widget()
            if widget:
                # Invalidate semua MovieCard di dalam section
                self._invalidate_cards_in_widget(widget)
                widget.deleteLater()
        print("[HOME PAGE] Sections cleared", flush=True)

    def _invalidate_cards_in_widget(self, widget):
        """
        Recursively invalidate semua MovieCard dalam widget.

        Args:
            widget: Widget yang akan di-scan untuk MovieCard
        """
        from app.ui.cards import MovieCard

        # Jika widget adalah MovieCard, invalidate
        if isinstance(widget, MovieCard):
            widget.invalidate()
            return

        # Jika widget punya children, scan recursive
        for child in widget.findChildren(MovieCard):
            child.invalidate()

    def _start_data_fetch(self):
        """
        Memulai proses fetch data di background thread.

        Membuat dan menjalankan DataFetcher thread untuk mengambil
        data dari API secara asynchronous.
        """
        self.fetcher = DataFetcher(self.api)
        self.fetcher.dataLoaded.connect(self._on_data_loaded)
        self.fetcher.start()

    def stop(self):
        """
        Menghentikan data fetcher yang sedang berjalan.

        Dipanggil sebelum navigasi ke halaman lain untuk cleanup.
        """
        # FIXED: Safe interruption dengan timeout
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            print("[HOME PAGE] Stopping fetcher safely...", flush=True)
            self.fetcher.requestInterruption()
            if not self.fetcher.wait(1000):
                print("[HOME PAGE] Forcing termination...", flush=True)
                self.fetcher.terminate()
                self.fetcher.wait(500)

    def reset(self):
        """
        Reset halaman home ke state awal.

        Menghentikan fetcher, membersihkan semua section, dan menghapus
        semua widget poster yang ter-cache.
        """
        print("[HOME PAGE] Resetting home page...", flush=True)
        self.stop()
        self.clear_sections()
        print("[HOME PAGE] Home page reset completed", flush=True)

    def _on_data_loaded(self, foryou, trending, latest):
        """
        Handler yang dipanggil ketika semua data selesai dimuat.

        Args:
            foryou: List Movie untuk kategori "For You"
            trending: List Movie untuk kategori "Trending"
            latest: List Movie untuk kategori "Latest"
        """
        self.loadingFinished.emit()
        self.clear_sections()
        self._add_section("Recommended For You", foryou)
        self._add_section("Popular on Galaxy", trending)
        self._add_section("Latest Releases", latest)

    def _add_section(self, title, movies):
        """
        Menambahkan section baru ke layout.

        Args:
            title: Judul section
            movies: List Movie untuk section tersebut
        """
        if not movies: return
        sec = MovieSection(title, movies, self.image_cache)
        sec.movieClicked.connect(self.movieClicked.emit)
        self.sections_layout.addWidget(sec)
