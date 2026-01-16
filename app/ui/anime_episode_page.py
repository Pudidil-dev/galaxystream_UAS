"""
Anime Episode Page - Halaman untuk menampilkan episode list dan server list.

Ditampilkan setelah user klik anime card di anime_page.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QPixmap, QFont
from app.models.movie import Movie
from app.services.anime_client import AnimeClient


class EpisodeCard(QFrame):
    """Card widget untuk menampilkan episode dalam bentuk kotak."""
    clicked = Signal(str, str)  # episode_id, episode_title

    def __init__(self, episode_id, episode_title):
        super().__init__()
        self.episode_id = episode_id
        self.episode_title = episode_title
        self.setFixedSize(120, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("EpisodeCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Episode number/title
        title_label = QLabel(episode_title)
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        self.setStyleSheet("""
            #EpisodeCard {
                background-color: rgba(255, 255, 255, 0.08);
                border: 2px solid #333;
                border-radius: 8px;
            }
            #EpisodeCard:hover {
                background-color: rgba(229, 9, 20, 0.3);
                border-color: #E50914;
            }
        """)

    def mousePressEvent(self, event):
        """Handle click event."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.episode_id, self.episode_title)
        super().mousePressEvent(event)


class ServerButton(QPushButton):
    """Button widget untuk menampilkan server dalam bentuk button yang bisa diselect."""

    def __init__(self, server_id, server_name, server_quality):
        super().__init__()
        self.server_id = server_id
        self.server_name = server_name
        self.server_quality = server_quality

        # Set text
        display_text = f"{server_name}"
        if server_quality:
            display_text += f"\n{server_quality}"
        self.setText(display_text)

        self.setFixedHeight(70)
        self.setMinimumWidth(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #E5E5E5;
                border: 2px solid #333;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 0.3);
                border-color: #E50914;
            }
            QPushButton:pressed {
                background-color: #E50914;
                border-color: #E50914;
                color: white;
            }
        """)


class EpisodeDetailFetcher(QThread):
    """Thread untuk mengambil detail anime dan episode list (Otakudesu only)."""
    dataLoaded = Signal(dict)

    def __init__(self, client, anime_id):
        super().__init__()
        self.client = client
        self.anime_id = anime_id

    def run(self):
        """Fetch anime detail dan episode list."""
        print(f"[EPISODE FETCHER] Fetching episodes for {self.anime_id}", flush=True)
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
        print(f"[SERVER FETCHER] Fetching servers for {self.episode_id}", flush=True)
        data = self.client.get_otakudesu_episode_servers(self.episode_id)
        self.dataLoaded.emit(data)


class AnimeEpisodePage(QWidget):
    """
    Halaman Episode & Server untuk anime.

    Menampilkan poster, judul, synopsis, episode list, dan server list.
    """
    backClicked = Signal()
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, image_cache):
        """
        Inisialisasi anime episode page.

        Args:
            image_cache: Instance ImageCache untuk caching gambar poster
        """
        super().__init__()
        self.image_cache = image_cache
        self.client = AnimeClient()
        self.current_anime = None
        self.episode_fetcher = None
        self.server_fetcher = None
        self.setup_ui()

    def setup_ui(self):
        """Menyiapkan layout dan komponen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with back button
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background: rgba(0,0,0,0.5); border-bottom: 1px solid #222;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 20, 40, 20)

        back_btn = QPushButton("← Back to Anime")
        back_btn.setFixedHeight(40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E50914;
            }
        """)
        back_btn.clicked.connect(self.backClicked.emit)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()

        layout.addWidget(header)

        # Main content
        content = QWidget()
        content.setStyleSheet("background: #0B0D12;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(30)

        # Left: Anime info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(15)

        # Poster
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(300, 400)
        self.poster_label.setScaledContents(True)
        self.poster_label.setStyleSheet("border: 2px solid #333; border-radius: 8px;")
        info_layout.addWidget(self.poster_label)

        # Title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)

        # Synopsis
        self.synopsis_label = QLabel()
        self.synopsis_label.setStyleSheet("font-size: 14px; color: #aaa; line-height: 1.5;")
        self.synopsis_label.setWordWrap(True)
        self.synopsis_label.setMaximumWidth(300)
        info_layout.addWidget(self.synopsis_label)

        info_layout.addStretch()
        content_layout.addWidget(info_widget)

        # Right: Episodes and Servers
        lists_widget = QWidget()
        lists_layout = QVBoxLayout(lists_widget)
        lists_layout.setSpacing(20)

        # Episodes section
        episodes_label = QLabel("📺 Episodes")
        episodes_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E5E5E5;")
        lists_layout.addWidget(episodes_label)

        # Episodes grid container with scroll
        episodes_scroll = QScrollArea()
        episodes_scroll.setWidgetResizable(True)
        episodes_scroll.setStyleSheet("""
            QScrollArea {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)

        episodes_container = QWidget()
        self.episodes_grid = QGridLayout(episodes_container)
        self.episodes_grid.setSpacing(10)
        self.episodes_grid.setContentsMargins(15, 15, 15, 15)
        episodes_scroll.setWidget(episodes_container)
        lists_layout.addWidget(episodes_scroll, stretch=1)

        # Servers section
        servers_label = QLabel("🖥️ Servers")
        servers_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #E5E5E5;")
        lists_layout.addWidget(servers_label)

        # Servers flow container with scroll
        servers_scroll = QScrollArea()
        servers_scroll.setWidgetResizable(True)
        servers_scroll.setStyleSheet("""
            QScrollArea {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)

        servers_container = QWidget()
        self.servers_layout = QGridLayout(servers_container)
        self.servers_layout.setSpacing(10)
        self.servers_layout.setContentsMargins(15, 15, 15, 15)
        servers_scroll.setWidget(servers_container)
        lists_layout.addWidget(servers_scroll, stretch=1)

        content_layout.addWidget(lists_widget, stretch=1)
        layout.addWidget(content)

    def load_anime(self, anime: Movie):
        """
        Load detail anime beserta episode list.

        Args:
            anime: Objek Movie yang akan ditampilkan
        """
        print(f"[ANIME EPISODE PAGE] Loading anime: {anime.title}", flush=True)
        self.current_anime = anime

        # Set title and synopsis
        self.title_label.setText(anime.title)
        self.synopsis_label.setText(anime.synopsis or "No synopsis available")

        # Load poster
        if anime.poster_url:
            self.image_cache.get_image(anime.poster_url, self._on_poster_loaded)
        else:
            self.poster_label.setText("No Poster")
            self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Clear grids
        while self.episodes_grid.count():
            item = self.episodes_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fetch episodes
        self.loadingRequested.emit("Loading episodes...")

        if self.episode_fetcher and self.episode_fetcher.isRunning():
            self.episode_fetcher.terminate()
            self.episode_fetcher.wait()

        self.episode_fetcher = EpisodeDetailFetcher(self.client, anime.id)
        self.episode_fetcher.dataLoaded.connect(self._on_episodes_loaded)
        self.episode_fetcher.start()

    def _on_poster_loaded(self, path):
        """Callback ketika poster selesai di-load."""
        if path:
            self.poster_label.setPixmap(QPixmap(path))
        else:
            self.poster_label.setText("No Poster")
            self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.poster_label.setStyleSheet("background-color: #1a1a2e; color: #666;")

    def _on_episodes_loaded(self, data):
        """Handler ketika episode list selesai dimuat."""
        self.loadingFinished.emit()
        episodes = data.get("episodes", [])

        print(f"[ANIME EPISODE PAGE] Loaded {len(episodes)} episodes", flush=True)

        # Clear existing episode cards
        while self.episodes_grid.count():
            item = self.episodes_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not episodes:
            no_ep_label = QLabel("No episodes available")
            no_ep_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            no_ep_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.episodes_grid.addWidget(no_ep_label, 0, 0)
            return

        # Create grid of episode cards (5 columns)
        cols = 5
        for i, episode in enumerate(episodes):
            row = i // cols
            col = i % cols
            card = EpisodeCard(episode.id, episode.title)
            card.clicked.connect(self._on_episode_clicked)
            self.episodes_grid.addWidget(card, row, col)

    def _on_episode_clicked(self, episode_id, episode_title):
        """Handler ketika user klik episode card."""
        if not episode_id:
            return

        print(f"[ANIME EPISODE PAGE] Episode clicked: {episode_title}", flush=True)

        # Clear existing server buttons
        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load servers
        self.loadingRequested.emit("Loading servers...")

        if self.server_fetcher and self.server_fetcher.isRunning():
            self.server_fetcher.terminate()
            self.server_fetcher.wait()

        self.server_fetcher = ServerFetcher(self.client, episode_id)
        self.server_fetcher.dataLoaded.connect(self._on_servers_loaded)
        self.server_fetcher.start()

    def _on_servers_loaded(self, servers):
        """Handler ketika server list selesai dimuat."""
        self.loadingFinished.emit()

        print(f"[ANIME EPISODE PAGE] Loaded {len(servers)} servers", flush=True)

        # Clear existing server buttons
        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not servers:
            no_server_label = QLabel("No servers available")
            no_server_label.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
            no_server_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.servers_layout.addWidget(no_server_label, 0, 0)
            return

        # Create grid of server buttons (3 columns for better readability)
        cols = 3
        for i, server in enumerate(servers):
            row = i // cols
            col = i % cols
            server_id = server.get("id", "")
            server_name = server.get("name", "Unknown")
            server_quality = server.get("quality", "")

            btn = ServerButton(server_id, server_name, server_quality)
            btn.clicked.connect(lambda checked, sid=server_id, sname=server_name: self._on_server_clicked(sid, sname))
            self.servers_layout.addWidget(btn, row, col)

    def _on_server_clicked(self, server_id, server_name):
        """Handler ketika user klik server button."""
        if not server_id:
            return

        print(f"[ANIME EPISODE PAGE] Server clicked: {server_name}", flush=True)

        self.loadingRequested.emit("Resolving stream URL...")

        # Resolve server URL
        url = self.client.get_otakudesu_server_url(server_id)

        self.loadingFinished.emit()

        if url:
            print(f"[ANIME EPISODE PAGE] Opening URL in browser: {url}", flush=True)
            QDesktopServices.openUrl(QUrl(url))
        else:
            print("[ANIME EPISODE PAGE] Failed to resolve server URL", flush=True)

    def stop(self):
        """Menghentikan semua thread yang sedang berjalan."""
        if self.episode_fetcher and self.episode_fetcher.isRunning():
            self.episode_fetcher.terminate()
            self.episode_fetcher.wait()
        if self.server_fetcher and self.server_fetcher.isRunning():
            self.server_fetcher.terminate()
            self.server_fetcher.wait()
