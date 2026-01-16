from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QScrollArea, QFrame, QSizePolicy
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, Signal, QTime, QTimer, QThread, Slot, QEvent
from PySide6.QtGui import QKeyEvent, QIcon
from app.models.movie import Movie, Episode
from app.services.history_service import HistoryService

# Style untuk tombol episode dalam keadaan normal
EPISODE_BTN_NORMAL = """
    QPushButton {
        background: #1a1a1a;
        color: white;
        border: 1px solid #333;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: #2a2a2a;
        border-color: #555;
    }
"""

# Style untuk tombol episode yang sedang aktif/diputar
EPISODE_BTN_ACTIVE = """
    QPushButton {
        background: #E50914;
        color: white;
        border: 2px solid #ff3333;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
    }
"""

class MovieFetcher(QThread):
    """
    Thread untuk mengambil daftar episode secara asynchronous.

    Thread ini mengambil semua episode dari movie/drama yang akan diputar.
    """
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api, movie_id):
        """
        Inisialisasi movie fetcher.

        Args:
            api: Instance APIClient untuk request data
            movie_id: ID movie yang akan diambil episode-nya
        """
        super().__init__()
        self.api = api
        self.movie_id = movie_id

    def run(self):
        """
        Menjalankan proses fetch episodes.

        Emit signal finished dengan list Episodes, atau signal error jika gagal.
        """
        try:
            episodes = self.api.get_episodes(self.movie_id)
            self.finished.emit(episodes)
        except Exception as e:
            self.error.emit(str(e))

class PlayerPage(QWidget):
    """
    Halaman video player untuk menonton film/drama.

    Halaman ini menampilkan video player dengan kontrol lengkap (play/pause, seek,
    volume, fullscreen), daftar episode, dan keyboard shortcuts. Mendukung mode
    fullscreen dengan auto-hide controls.
    """
    backClicked = Signal()
    toggleFullScreen = Signal()
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, api_client):
        """
        Inisialisasi player page.

        Args:
            api_client: Instance APIClient untuk request data streaming
        """
        super().__init__()
        self.api = api_client
        self.episodes = []
        self.current_idx = 0
        self.ep_buttons = []
        self.is_full_screen = False
        self.current_movie = None  # Store current movie object for stream URL fetching

        # History service untuk menyimpan riwayat tontonan
        self.history_service = HistoryService()

        # Auto-hide controls in fullscreen
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_controls)
        self.controls_visible = True

        self.setup_ui()
        self.setup_player()

        # Enable mouse tracking for auto-hide
        self.setMouseTracking(True)

        # Enable focus for keyboard shortcuts
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_ui(self):
        """
        Menyiapkan antarmuka pengguna untuk video player.

        Membuat layout lengkap dengan video container, control overlay (seek bar,
        play/pause, prev/next, volume, fullscreen), dan episode list di bawah.
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Set size policy to prevent overflow
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Video container
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #000;")
        self.video_container.setMouseTracking(True)
        self.video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_container_layout = QHBoxLayout(self.video_container)
        self.video_container_layout.setContentsMargins(0, 0, 0, 0)
        self.video_container_layout.setSpacing(0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setMouseTracking(True)
        self.video_widget.installEventFilter(self)
        self.video_container_layout.addWidget(self.video_widget)
        
        self.main_layout.addWidget(self.video_container, 8)

        # Controls Overlay
        self.controls = QFrame()
        self.controls.setObjectName("PlayerOverlay")
        self.controls.setFixedHeight(90)  # Reduced from 120 to 90
        self.controls.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.c_layout = QVBoxLayout(self.controls)
        self.c_layout.setContentsMargins(15, 5, 15, 5)  # Reduced margins
        
        # Seek bar on top of controls
        self.seek_bar = QSlider(Qt.Orientation.Horizontal)
        self.seek_bar.sliderMoved.connect(self._on_seek)
        self.c_layout.addWidget(self.seek_bar)

        # Main controls horizontal layout
        self.controls_h_layout = QHBoxLayout()
        self.controls_h_layout.setSpacing(15)

        # LEFT SIDE: Back and Time
        left_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Back")
        self.back_btn.setStyleSheet("background: transparent; color: white; border: none; font-size: 16px;")
        self.back_btn.clicked.connect(self.backClicked.emit)
        left_layout.addWidget(self.back_btn)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #ccc; font-size: 13px;")
        left_layout.addWidget(self.time_label)
        self.controls_h_layout.addLayout(left_layout)

        self.controls_h_layout.addStretch()

        # CENTER SIDE: Prev, Play/Pause, Next
        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setStyleSheet("font-size: 20px; color: white; background: transparent; border: none;")
        self.prev_btn.clicked.connect(self._on_prev_clicked)
        center_layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(60, 60)
        self.play_btn.setStyleSheet("font-size: 32px; color: white; background: transparent; border: none;")
        self.play_btn.clicked.connect(self._toggle_play)
        center_layout.addWidget(self.play_btn)

        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setStyleSheet("font-size: 20px; color: white; background: transparent; border: none;")
        self.next_btn.clicked.connect(self._on_next_clicked)
        center_layout.addWidget(self.next_btn)

        self.controls_h_layout.addLayout(center_layout)

        self.controls_h_layout.addStretch()

        # RIGHT SIDE: Volume and Fullscreen
        right_layout = QHBoxLayout()
        right_layout.setSpacing(10)

        vol_icon = QLabel("🔈")
        right_layout.addWidget(vol_icon)
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setValue(80)
        self.vol_slider.valueChanged.connect(self._on_volume)
        right_layout.addWidget(self.vol_slider)

        self.fs_btn = QPushButton("⛶")
        self.fs_btn.setFixedSize(40, 40)
        self.fs_btn.setStyleSheet("font-size: 20px; color: white; background: transparent; border: none;")
        self.fs_btn.setToolTip("Full Screen (F)")
        self.fs_btn.clicked.connect(self.toggleFullScreen.emit)
        right_layout.addWidget(self.fs_btn)

        self.controls_h_layout.addLayout(right_layout)

        self.c_layout.addLayout(self.controls_h_layout)
        self.main_layout.addWidget(self.controls)

        # Episodes list (Bottom bar)
        self.ep_scroll = QScrollArea()
        self.ep_scroll.setFixedHeight(90)  # Reduced from 120 to 90
        self.ep_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ep_scroll.setWidgetResizable(True)
        self.ep_scroll.setStyleSheet("background: #000; border-top: 1px solid #222;")

        self.ep_container = QWidget()
        self.ep_layout = QHBoxLayout(self.ep_container)
        self.ep_layout.setContentsMargins(15, 5, 15, 5)  # Reduced margins
        self.ep_scroll.setWidget(self.ep_container)
        self.main_layout.addWidget(self.ep_scroll)

    def setup_player(self):
        """
        Menyiapkan QMediaPlayer dan audio output.

        Menghubungkan video output ke video widget dan menghubungkan
        semua signal player (position, duration, state, error) ke handler.
        """
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        self.player.positionChanged.connect(self._on_pos_changed)
        self.player.durationChanged.connect(self._on_dur_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.errorOccurred.connect(self._on_error)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handler untuk keyboard shortcuts pada player.

        Shortcuts yang tersedia:
        - F: Toggle fullscreen
        - Space: Play/Pause
        - Escape: Exit fullscreen
        - Left/Right: Seek backward/forward 10 detik
        - N: Next episode
        - P: Previous episode

        Args:
            event: Event keyboard dari Qt
        """
        if event.key() == Qt.Key.Key_F:
            self.toggleFullScreen.emit()
        elif event.key() == Qt.Key.Key_Space:
            self._toggle_play()
        elif event.key() == Qt.Key.Key_Escape:
            if self.is_full_screen:
                self.toggleFullScreen.emit()
        elif event.key() == Qt.Key.Key_Left:
            self.player.setPosition(max(0, self.player.position() - 10000))
        elif event.key() == Qt.Key.Key_Right:
            self.player.setPosition(min(self.player.duration(), self.player.position() + 10000))
        elif event.key() == Qt.Key.Key_N:
            self._on_next_clicked()
        elif event.key() == Qt.Key.Key_P:
            self._on_prev_clicked()
        else:
            super().keyPressEvent(event)

    def set_full_screen_mode(self, enabled: bool):
        """
        Mengatur mode fullscreen untuk player.

        Dalam mode fullscreen, episode list dan back button disembunyikan,
        dan controls akan auto-hide setelah beberapa detik tidak ada interaksi.

        Args:
            enabled: True untuk enable fullscreen, False untuk keluar
        """
        self.is_full_screen = enabled
        if enabled:
            self.ep_scroll.hide()
            self.back_btn.hide()
            # Start auto-hide timer
            self._start_hide_timer()
        else:
            self.ep_scroll.show()
            self.back_btn.show()
            self.hide_timer.stop()
            self._show_controls()

    def eventFilter(self, obj, event):
        """Intercept mouse events from video widget."""
        if obj == self.video_widget and event.type() == QEvent.Type.MouseMove:
            if self.is_full_screen:
                # Map global pos or local pos
                # event.position() is local to video_widget
                # We need to check relative to the screen or this widget height
                
                # Since video_widget fills the screen in fullscreen, local y is fine
                # But we should be careful. Let's use the mouseMoveEvent logic here.
                bottom_zone = self.video_widget.height() - 150
                if event.position().y() > bottom_zone:
                    self._show_controls()
                    self._start_hide_timer()
            return False # Propagate
        return super().eventFilter(obj, event)

    def mouseMoveEvent(self, event):
        """Show controls when mouse hovers at bottom of screen in fullscreen."""
        if self.is_full_screen:
            # Check if mouse is in bottom 150px of the widget (control zone)
            bottom_zone = self.height() - 150
            if event.position().y() > bottom_zone:
                self._show_controls()
                self._start_hide_timer()
        super().mouseMoveEvent(event)

    def _start_hide_timer(self):
        """Start timer to hide controls after 3 seconds."""
        self.hide_timer.stop()
        self.hide_timer.start(3000)  # 3 seconds

    def _hide_controls(self):
        """Hide controls overlay in fullscreen."""
        if self.is_full_screen and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.controls.hide()
            self.controls_visible = False

    def _show_controls(self):
        """Show controls overlay."""
        self.controls.show()
        self.controls_visible = True

    def _on_error(self, error, error_string):
        """Handler error dari media player."""
        print(f"[PLAYER ERROR] Media Player Error: {error} - {error_string}", flush=True)
        print(f"[PLAYER ERROR] Current source: {self.player.source().toString()}", flush=True)
        if self.episodes and 0 <= self.current_idx < len(self.episodes):
            current_ep = self.episodes[self.current_idx]
            print(f"[PLAYER ERROR] Episode ID: {current_ep.id}, Stream URL: {current_ep.stream_url}", flush=True)

    def _on_media_status_changed(self, status):
        """
        Handler ketika status media berubah.

        Otomatis memutar episode berikutnya ketika video selesai.

        Args:
            status: Status media dari QMediaPlayer
        """
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._play_next_episode()

    def _play_next_episode(self):
        """Memutar episode berikutnya secara otomatis."""
        self._on_next_clicked()

    def _on_prev_clicked(self):
        """Handler tombol previous episode."""
        if self.current_idx > 0:
            self.play_episode(self.current_idx - 1)

    def _on_next_clicked(self):
        """Handler tombol next episode."""
        if self.current_idx < len(self.episodes) - 1:
            self.play_episode(self.current_idx + 1)

    def play_movie(self, movie, initial_episode=0):
        """
        Memulai pemutaran movie/drama dengan mengambil daftar episode.

        Menampilkan loading overlay, membuat thread untuk fetch episodes,
        dan mempersiapkan player untuk playback.

        Args:
            movie: Objek Movie yang akan diputar
            initial_episode: Index episode yang akan dimainkan pertama kali (default: 0)
        """
        self.current_movie = movie  # Store for stream URL fetching
        self.current_idx = initial_episode  # Set initial episode index
        self.loadingRequested.emit(f"Loading {movie.title}...")

        # Safe thread cleanup
        if hasattr(self, 'fetcher') and self.fetcher.isRunning():
            self.fetcher.terminate()
            self.fetcher.wait()

        self.fetcher = MovieFetcher(self.api, movie.id)
        self.fetcher.finished.connect(self._on_episodes_loaded)
        self.fetcher.error.connect(lambda err: self.loadingFinished.emit())
        self.fetcher.start()
        self.setFocus()

    def _on_episodes_loaded(self, episodes):
        """
        Handler yang dipanggil ketika daftar episode selesai dimuat.

        Args:
            episodes: List objek Episode yang berhasil dimuat
        """
        print(f"[PLAYER] Loaded {len(episodes)} episodes", flush=True)
        self.episodes = episodes
        self._refresh_episodes()

        # Play the selected episode (could be 0 or user-selected index)
        if self.episodes and 0 <= self.current_idx < len(self.episodes):
            print(f"[PLAYER] Playing episode {self.current_idx + 1}", flush=True)
            print(f"[PLAYER] Episode stream URL: {self.episodes[self.current_idx].stream_url}", flush=True)
            self.play_episode(self.current_idx)
        elif not self.episodes:
            print("[PLAYER] WARNING: No episodes found. Check API token and endpoints.", flush=True)
            self.loadingFinished.emit()

    def play_episode(self, index):
        """
        Memutar episode pada index tertentu.

        Jika stream URL memerlukan fetch tambahan, akan membuat thread baru
        untuk mengambil URL streaming sebenarnya.

        Args:
            index: Index episode yang akan diputar
        """
        if 0 <= index < len(self.episodes):
            self.current_idx = index
            ep = self.episodes[index]

            stream_url = ep.stream_url

            # If stream URL is empty or needs to be fetched, fetch it
            if not stream_url or stream_url.startswith("FETCH_REQUIRED"):
                self.loadingRequested.emit("Fetching stream...")
                from threading import Thread
                def fetch():
                    # Pass book_id, episode_id, and episode order to get_stream_url
                    book_id = self.current_movie.id if self.current_movie else None
                    episode_no = ep.order  # Episode number/order
                    url = self.api.get_stream_url(ep.id, book_id=book_id, episode_no=episode_no)
                    self._start_playback(url)
                Thread(target=fetch, daemon=True).start()
                return

            self._start_playback(stream_url)

    def _start_playback(self, url):
        """
        Memulai playback dengan URL yang diberikan (thread-safe).

        Menggunakan QMetaObject.invokeMethod untuk memastikan UI calls
        dijalankan di main thread.

        Args:
            url: URL stream video
        """
        from PySide6.QtCore import QMetaObject, Q_ARG
        # Ensure UI calls are on main thread
        QMetaObject.invokeMethod(self, "_do_play", Qt.ConnectionType.QueuedConnection, Q_ARG(str, url))

    @Slot(str)
    def _do_play(self, url):
        """
        Melakukan playback aktual pada main thread.

        Mengatur source player, memulai playback, update highlight episode,
        dan mengatur state tombol prev/next.

        Args:
            url: URL stream video
        """
        if not url:
            print("[PLAYER] ERROR: Stream URL is empty!", flush=True)
            self.loadingFinished.emit()
            return

        # Validate URL format
        if not url.startswith(("http://", "https://", "file://")):
            print(f"[PLAYER] ERROR: Invalid stream URL format: {url}", flush=True)
            print("[PLAYER] Hint: URL should be a valid HTTP/HTTPS video URL", flush=True)
            self.loadingFinished.emit()
            return

        print(f"[PLAYER] Starting playback: {url}", flush=True)
        self.player.setSource(QUrl(url))
        self.player.play()
        self._update_episode_highlight()
        if self.current_idx < len(self.ep_buttons):
            self.ep_scroll.ensureWidgetVisible(self.ep_buttons[self.current_idx])

        # Simpan ke history
        self._save_to_history(url)

        # Update disabled state of prev/next buttons
        self.prev_btn.setEnabled(self.current_idx > 0)
        self.next_btn.setEnabled(self.current_idx < len(self.episodes) - 1)
        self.prev_btn.setAlpha(1.0 if self.prev_btn.isEnabled() else 0.3)
        self.next_btn.setAlpha(1.0 if self.next_btn.isEnabled() else 0.3)
        self.loadingFinished.emit()

    def _refresh_episodes(self):
        """
        Merefresh tampilan episode list dengan data episode yang baru.

        Membersihkan semua tombol episode yang ada dan membuat tombol baru
        untuk setiap episode dalam list.
        """
        self.ep_buttons.clear()
        while self.ep_layout.count():
            item = self.ep_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        for i, ep in enumerate(self.episodes):
            btn = QPushButton(f"EP {i+1}")
            btn.setFixedSize(65, 65)  # Reduced from 70x70 to 65x65
            btn.setStyleSheet(EPISODE_BTN_NORMAL)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, idx=i: self.play_episode(idx))
            self.ep_layout.addWidget(btn)
            self.ep_buttons.append(btn)

    def _update_episode_highlight(self):
        """
        Update highlight tombol episode berdasarkan episode yang sedang aktif.

        Tombol episode aktif akan ditampilkan dengan style merah (EPISODE_BTN_ACTIVE),
        sedangkan yang lain menggunakan style normal.
        """
        for i, btn in enumerate(self.ep_buttons):
            btn.setStyleSheet(EPISODE_BTN_ACTIVE if i == self.current_idx else EPISODE_BTN_NORMAL)

    def _toggle_play(self):
        """Toggle play/pause state dari player."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_state_changed(self, state):
        """
        Handler ketika playback state berubah.

        Update tombol play/pause dengan icon yang sesuai (pause saat playing,
        play saat paused).

        Args:
            state: State playback dari QMediaPlayer
        """
        self.play_btn.setText("⏸" if state == QMediaPlayer.PlaybackState.PlayingState else "▶")

    def _on_pos_changed(self, pos):
        """
        Handler ketika posisi playback berubah.

        Update seek bar dan time label sesuai posisi playback.

        Args:
            pos: Posisi playback dalam milliseconds
        """
        self.seek_bar.setValue(pos)
        self._update_time()

    def _on_dur_changed(self, dur):
        """
        Handler ketika durasi video berubah.

        Mengatur range seek bar sesuai durasi dan update time label.

        Args:
            dur: Durasi video dalam milliseconds
        """
        self.seek_bar.setRange(0, dur)
        self._update_time()

    def _on_seek(self, pos):
        """
        Handler ketika user melakukan seek pada seek bar.

        Args:
            pos: Posisi target seek dalam milliseconds
        """
        self.player.setPosition(pos)

    def _on_volume(self, val):
        """
        Handler ketika volume slider berubah.

        Args:
            val: Nilai volume dari slider (0-100)
        """
        self.audio.setVolume(val / 100.0)

    def _update_time(self):
        """Update tampilan time label dengan posisi dan durasi saat ini."""
        cur = QTime(0,0).addMSecs(self.player.position()).toString("mm:ss")
        dur = QTime(0,0).addMSecs(self.player.duration()).toString("mm:ss")
        self.time_label.setText(f"{cur} / {dur}")

    def _save_to_history(self, stream_url: str):
        """
        Simpan konten yang sedang ditonton ke history.

        Args:
            stream_url: URL stream video yang sedang diputar
        """
        if not self.current_movie:
            return

        try:
            # Ambil episode yang sedang diputar
            episode = None
            if 0 <= self.current_idx < len(self.episodes):
                episode = self.episodes[self.current_idx]

            self.history_service.add_history(
                source=self.current_movie.source_type or "",
                content_id=self.current_movie.id,
                title=self.current_movie.title,
                poster_url=self.current_movie.poster_url or "",
                episode_id=episode.id if episode else "",
                episode_title=episode.title if episode else f"EP {self.current_idx + 1}",
                episode_path=stream_url,
                duration=0,  # Will be updated when duration is known
                position=0
            )
        except Exception as e:
            print(f"[PLAYER] Error saving to history: {e}", flush=True)

    def stop(self):
        """
        Menghentikan player dan cleanup thread fetcher.

        Dipanggil sebelum navigasi ke halaman lain.
        """
        if hasattr(self, 'fetcher') and self.fetcher.isRunning():
            self.fetcher.terminate()
            self.fetcher.wait()
        self.player.stop()

# Helper for transparency since QWidget doesn't have setAlpha
def setAlpha(widget, alpha):
    from PySide6.QtWidgets import QGraphicsOpacityEffect
    effect = QGraphicsOpacityEffect()
    effect.setOpacity(alpha)
    widget.setGraphicsEffect(effect)

QPushButton.setAlpha = setAlpha
