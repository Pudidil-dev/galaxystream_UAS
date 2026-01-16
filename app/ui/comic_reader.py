from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal, QThread, QMetaObject, Q_ARG
from PySide6.QtGui import QPixmap, QImage
import os

class ChapterFetcher(QThread):
    """
    Thread untuk mengambil daftar chapter komik secara asynchronous.

    Thread ini mengambil semua chapter dari komik yang akan dibaca.
    """
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api, movie_id):
        """
        Inisialisasi chapter fetcher.

        Args:
            api: Instance APIClient untuk request data
            movie_id: ID komik yang akan diambil chapter-nya
        """
        super().__init__()
        self.api = api
        self.movie_id = movie_id

    def run(self):
        """
        Menjalankan proses fetch chapters.

        Emit signal finished dengan list Chapters, atau signal error jika gagal.
        """
        try:
            chapters = self.api.get_episodes(self.movie_id)
            self.finished.emit(chapters)
        except Exception as e:
            self.error.emit(str(e))

class ComicFetcher(QThread):
    """
    Thread untuk mengambil daftar gambar halaman komik secara asynchronous.

    Thread ini mengambil semua URL gambar dari chapter komik tertentu.
    """
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api, chapter_id):
        """
        Inisialisasi comic fetcher.

        Args:
            api: Instance APIClient untuk request data
            chapter_id: ID chapter yang akan diambil gambarnya
        """
        super().__init__()
        self.api = api
        self.chapter_id = chapter_id

    def run(self):
        """
        Menjalankan proses fetch gambar halaman komik.

        Emit signal finished dengan list URL gambar, atau signal error jika gagal.
        """
        try:
            images = self.api.get_comic_images(self.chapter_id)
            self.finished.emit(images)
        except Exception as e:
            self.error.emit(str(e))

class ComicReader(QtWidgets.QWidget):
    """
    Halaman comic reader untuk membaca komik/manga.

    Halaman ini menampilkan gambar halaman komik secara vertikal scroll,
    dengan kontrol navigasi chapter, zoom in/out, dan chapter list menu.
    Mendukung lazy loading gambar menggunakan image cache.
    """
    backClicked = Signal()
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, api, image_cache):
        """
        Inisialisasi comic reader.

        Args:
            api: Instance APIClient untuk request data komik
            image_cache: Instance ImageCache untuk caching gambar halaman
        """
        super().__init__()
        self.api = api
        self.image_cache = image_cache
        self.chapters = []
        self.current_chapter_idx = 0
        self.movie = None
        self.fetcher = None # Image fetcher
        self.chapter_fetcher = None
        self.zoom_level = 1.0  # Zoom scale (0.5 to 2.0)
        self.base_width = 800  # Base image width
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan antarmuka pengguna untuk comic reader.

        Membuat top bar dengan back button, judul, zoom controls, dan navigation buttons.
        Membuat scroll area untuk menampilkan gambar halaman komik secara vertikal.
        """
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Top Bar
        self.top_bar = QtWidgets.QFrame()
        self.top_bar.setFixedHeight(60)
        self.top_bar.setStyleSheet("background-color: rgba(0, 0, 0, 0.9); border-bottom: 1px solid #E50914;")
        tb_layout = QtWidgets.QHBoxLayout(self.top_bar)
        tb_layout.setContentsMargins(20, 0, 20, 0)
        
        self.back_btn = QtWidgets.QPushButton("← Back")
        self.back_btn.setFixedSize(80, 40)
        self.back_btn.setStyleSheet("background: transparent; color: white; font-weight: bold; border: none;")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.backClicked.emit)
        tb_layout.addWidget(self.back_btn)

        self.title_label = QtWidgets.QLabel("Reading...")
        self.title_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        tb_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Zoom Controls
        zoom_widget = QtWidgets.QWidget()
        zoom_layout = QtWidgets.QHBoxLayout(zoom_widget)
        zoom_layout.setSpacing(5)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        
        self.zoom_out_btn = QtWidgets.QPushButton("−")
        self.zoom_out_btn.setFixedSize(35, 35)
        self.zoom_out_btn.setStyleSheet("background: #333; color: white; border-radius: 4px; font-size: 18px; font-weight: bold;")
        self.zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        
        self.zoom_label = QtWidgets.QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("color: white; font-size: 12px;")
        
        self.zoom_in_btn = QtWidgets.QPushButton("+")
        self.zoom_in_btn.setFixedSize(35, 35)
        self.zoom_in_btn.setStyleSheet("background: #333; color: white; border-radius: 4px; font-size: 18px; font-weight: bold;")
        self.zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_in_btn)
        tb_layout.addWidget(zoom_widget)
        
        tb_layout.addStretch()
        
        # Navigation Buttons
        nav_widget = QtWidgets.QWidget()
        nav_layout = QtWidgets.QHBoxLayout(nav_widget)
        nav_layout.setSpacing(10)
        
        self.prev_btn = QtWidgets.QPushButton("PREV")
        self.prev_btn.setFixedSize(70, 35)
        self.prev_btn.setStyleSheet("background: #222; color: white; border-radius: 4px;")
        self.prev_btn.clicked.connect(self._prev_chapter)
        
        self.list_btn = QtWidgets.QPushButton("≡ LIST")
        self.list_btn.setFixedSize(70, 35)
        self.list_btn.setStyleSheet("background: #222; color: white; border-radius: 4px;")
        self.list_btn.clicked.connect(self._show_chapter_list)
        
        self.next_btn = QtWidgets.QPushButton("NEXT")
        self.next_btn.setFixedSize(70, 35)
        self.next_btn.setStyleSheet("background: #E50914; color: white; border-radius: 4px; font-weight: bold;")
        self.next_btn.clicked.connect(self._next_chapter)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.list_btn)
        nav_layout.addWidget(self.next_btn)
        tb_layout.addWidget(nav_widget)
        
        self._layout.addWidget(self.top_bar)

        # Scroll Area for images
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #0B0D12; border: none;")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QtWidgets.QWidget()
        self.content.setStyleSheet("background-color: #0B0D12;")
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.scroll.setWidget(self.content)
        self._layout.addWidget(self.scroll)
        
        # Ensure top bar is on top and receiving clicks
        self.top_bar.raise_()

    def load_comic(self, movie, index=0):
        """
        Memulai pembacaan komik dengan mengambil daftar chapter.

        Menampilkan loading overlay, membuat thread untuk fetch chapters,
        dan mempersiapkan reader untuk menampilkan chapter.

        Args:
            movie: Objek Movie (komik) yang akan dibaca
            index: Index chapter yang akan dibaca pertama kali (default: 0)
        """
        self.movie = movie
        self.loadingRequested.emit(f"Loading {movie.title} chapters...")
        
        if self.chapter_fetcher and self.chapter_fetcher.isRunning():
            self.chapter_fetcher.terminate()
            self.chapter_fetcher.wait()
            
        self.chapter_fetcher = ChapterFetcher(self.api, movie.id)
        self.chapter_fetcher.finished.connect(lambda ch, idx=index: self._on_chapters_loaded(ch, idx))
        self.chapter_fetcher.error.connect(lambda err: self.loadingFinished.emit())
        self.chapter_fetcher.start()

    def _on_chapters_loaded(self, chapters, index):
        """
        Handler yang dipanggil ketika daftar chapter selesai dimuat.

        Args:
            chapters: List objek Episode (chapter) yang berhasil dimuat
            index: Index chapter yang akan dibaca pertama kali
        """
        self.loadingFinished.emit()
        self.chapters = chapters
        if self.chapters:
            self.read_chapter(index)
        else:
            self.title_label.setText("No chapters found")

    def read_chapter(self, index):
        """
        Membaca chapter pada index tertentu.

        Membersihkan gambar yang ada, mengambil daftar gambar halaman chapter,
        dan menampilkannya secara vertikal scroll.

        Args:
            index: Index chapter yang akan dibaca
        """
        if not (0 <= index < len(self.chapters)): return
        self.current_chapter_idx = index
        chapter = self.chapters[index]
        self.title_label.setText(f"{self.movie.title} - {chapter.title}")
        
        # Clear existing images
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.loadingRequested.emit(f"Loading {chapter.title}...")
        
        # Safe thread cleanup
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            self.fetcher.terminate()
            self.fetcher.wait()
            
        self.fetcher = ComicFetcher(self.api, chapter.id)
        self.fetcher.finished.connect(self._on_images_loaded)
        self.fetcher.error.connect(lambda err: self.loadingFinished.emit())
        self.fetcher.start()

    def stop(self):
        """
        Menghentikan semua thread fetcher yang sedang berjalan.

        Dipanggil sebelum navigasi ke halaman lain untuk cleanup.
        """
        if hasattr(self, 'fetcher') and self.fetcher and self.fetcher.isRunning():
            self.fetcher.terminate()
            self.fetcher.wait()
        if hasattr(self, 'chapter_fetcher') and self.chapter_fetcher and self.chapter_fetcher.isRunning():
            self.chapter_fetcher.terminate()
            self.chapter_fetcher.wait()

    def _on_images_loaded(self, images):
        """
        Handler yang dipanggil ketika daftar gambar halaman selesai dimuat.

        Membuat label untuk setiap gambar dan menggunakan image cache untuk
        mendownload dan menampilkan gambar secara lazy loading.

        Args:
            images: List URL gambar halaman komik
        """
        if not images:
            self.loadingFinished.emit()
            self.title_label.setText(f"{self.movie.title} - No Images found")
            return

        for img_url in images:
            img_label = QtWidgets.QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setText("Loading page...")
            img_label.setStyleSheet("color: #444; padding: 50px;")
            self.content_layout.addWidget(img_label)
            
            # Use cache to load image
            self.image_cache.get_image(img_url, lambda path, lbl=img_label: self._on_image_loaded(path, lbl))
        
        self.loadingFinished.emit()
        self.scroll.verticalScrollBar().setValue(0)
        
        # Update nav buttons
        self.prev_btn.setEnabled(self.current_chapter_idx > 0)
        self.next_btn.setEnabled(self.current_chapter_idx < len(self.chapters) - 1)

    def _prev_chapter(self):
        """Membaca chapter sebelumnya jika ada."""
        if self.current_chapter_idx > 0:
            self.read_chapter(self.current_chapter_idx - 1)

    def _next_chapter(self):
        """Membaca chapter berikutnya jika ada."""
        if self.current_chapter_idx < len(self.chapters) - 1:
            self.read_chapter(self.current_chapter_idx + 1)

    def _show_chapter_list(self):
        """
        Menampilkan popup menu dengan daftar chapter.

        Menu menampilkan 20 chapter sebelum dan 20 chapter setelah chapter
        yang sedang aktif, dengan indicator untuk chapter saat ini.
        """
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #111; color: white; border: 1px solid #E50914; padding: 5px; }
            QMenu::item { padding: 8px 25px; }
            QMenu::item:selected { background: #E50914; }
        """)
        
        start = max(0, self.current_chapter_idx - 20)
        end = min(len(self.chapters), self.current_chapter_idx + 20)
        
        for i in range(start, end):
            ch = self.chapters[i]
            action = menu.addAction(f"{'➡️ ' if i == self.current_chapter_idx else ''}{ch.title}")
            action.triggered.connect(lambda checked=False, idx=i: self.read_chapter(idx))
            
        menu.exec(self.list_btn.mapToGlobal(self.list_btn.rect().bottomLeft()))

    def _on_image_loaded(self, path, label):
        """
        Callback yang dipanggil ketika gambar halaman selesai didownload.

        Menyimpan path gambar di property label untuk re-scaling saat zoom,
        dan menerapkan zoom level saat ini.

        Args:
            path: Path file gambar yang sudah di-cache
            label: QLabel untuk menampilkan gambar
        """
        if path and os.path.exists(path):
            label.setProperty("image_path", path)  # Store original path for re-scaling
            self._apply_zoom_to_label(label, path)
        else:
            label.setText("Failed to load image")

    def _apply_zoom_to_label(self, label, path):
        """
        Menerapkan zoom level saat ini ke label gambar.

        Menggunakan base_width dan zoom_level untuk menghitung ukuran gambar
        yang ditampilkan, dengan smooth transformation untuk kualitas yang baik.

        Args:
            label: QLabel yang akan menampilkan gambar
            path: Path file gambar
        """
        pixmap = QPixmap(path)
        target_width = int(self.base_width * self.zoom_level)
        if pixmap.width() > target_width:
            pixmap = pixmap.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)
        label.setText("")
        label.setMinimumHeight(pixmap.height())
        label.setStyleSheet("padding: 0;")

    def _zoom_in(self):
        """
        Memperbesar zoom level (maksimal 200%).

        Menambah zoom level sebesar 0.25 (25%) dan update semua gambar.
        """
        if self.zoom_level < 2.0:
            self.zoom_level = min(2.0, self.zoom_level + 0.25)
            self._update_zoom()

    def _zoom_out(self):
        """
        Memperkecil zoom level (minimal 50%).

        Mengurangi zoom level sebesar 0.25 (25%) dan update semua gambar.
        """
        if self.zoom_level > 0.5:
            self.zoom_level = max(0.5, self.zoom_level - 0.25)
            self._update_zoom()

    def _update_zoom(self):
        """
        Update tampilan zoom label dan re-render semua gambar dengan zoom baru.

        Mengiterasi semua gambar yang sudah dimuat dan menerapkan ulang
        zoom level terbaru ke setiap gambar.
        """
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
        
        # Re-apply zoom to all loaded images
        for i in range(self.content_layout.count()):
            widget = self.content_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'property'):
                path = widget.property("image_path")
                if path:
                    self._apply_zoom_to_label(widget, path)
