from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QMouseEvent
from app.models.movie import Movie

class ClickableLabel(QLabel):
    """
    Label yang meneruskan event mouse ke parent widget.

    Digunakan agar klik pada label poster atau judul akan
    diteruskan ke MovieCard parent-nya.
    """
    def mousePressEvent(self, event):
        """Meneruskan event mouse press ke parent widget."""
        self.parent().mousePressEvent(event)
    def mouseReleaseEvent(self, event):
        """Meneruskan event mouse release ke parent widget."""
        self.parent().mouseReleaseEvent(event)

class MovieCard(QFrame):
    """
    Widget kartu untuk menampilkan poster dan judul film/drama/komik.

    Kartu ini menampilkan gambar poster yang diambil dari image cache
    dan judul konten, serta dapat diklik untuk menampilkan detail.
    """
    clicked = Signal(object)  # Change to object for broader compatibility

    def __init__(self, movie: Movie, image_cache, current_source=None):
        """
        Inisialisasi movie card.

        Args:
            movie: Objek Movie yang akan ditampilkan
            image_cache: Service ImageCache untuk mendownload dan cache gambar poster
            current_source: Source yang sedang aktif (untuk validasi)
        """
        super().__init__()
        self.movie = movie
        self.image_cache = image_cache
        self.current_source = current_source or movie.source_type
        self._is_valid = True  # Flag untuk validasi source
        self.setObjectName("MovieCard")
        self.setFixedSize(180, 300)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout dan komponen UI untuk movie card.

        Membuat label untuk poster dan judul, lalu meminta gambar dari image cache.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # Reduced spacing

        # Use ClickableLabel so clicks pass through to parent
        self.poster_label = ClickableLabel(self)
        self.poster_label.setObjectName("MovieCardPoster")
        self.poster_label.setFixedSize(180, 260)
        self.poster_label.setScaledContents(True)
        layout.addWidget(self.poster_label)

        self.title_label = ClickableLabel(self)
        self.title_label.setText(self.movie.title)
        self.title_label.setObjectName("MovieCardTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(35)  # Limit title height to prevent overflow
        layout.addWidget(self.title_label)

        self.image_cache.get_image(self.movie.poster_url, self._on_image_loaded)

    def _on_image_loaded(self, path):
        """
        Callback yang dipanggil ketika gambar poster selesai didownload.

        IMPORTANT: Source validation untuk mencegah poster dari source lain
        menimpa poster yang sedang ditampilkan.

        Args:
            path: Path file gambar yang sudah di-cache, atau string kosong jika gagal
        """
        # MIDDLEWARE: Validasi source sebelum set pixmap
        if not self._is_valid:
            print(f"[MOVIECARD] Callback ignored - card invalidated (source changed)", flush=True)
            return

        # Validasi widget masih hidup
        try:
            if not self.poster_label:
                print(f"[MOVIECARD] Callback ignored - widget deleted", flush=True)
                return
        except RuntimeError:
            print(f"[MOVIECARD] Callback ignored - widget already destroyed", flush=True)
            return

        # Set pixmap jika validasi lolos
        if path:
            print(f"[MOVIECARD] Loading image for {self.movie.source_type}: {self.movie.title[:30]}...", flush=True)
            self.poster_label.setPixmap(QPixmap(path))
        else:
            # Show a styled placeholder when no image
            self.poster_label.setText("No Image")
            self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.poster_label.setStyleSheet("background-color: #1a1a2e; color: #666; font-size: 14px; border: 1px solid #333;")

    def invalidate(self):
        """
        Invalidate card untuk mencegah callback dieksekusi.

        Method ini dipanggil saat source berubah atau card akan dihapus.
        """
        print(f"[MOVIECARD] Invalidating card: {self.movie.title[:30]}... ({self.movie.source_type})", flush=True)
        self._is_valid = False

    def mousePressEvent(self, event: QMouseEvent):
        """
        Handler event klik mouse untuk emit signal dengan objek Movie.

        Args:
            event: Event mouse press dari Qt
        """
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"[DEBUG] MovieCard clicked: {self.movie.title} (ID: {self.movie.id})")
            self.clicked.emit(self.movie)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """
        Handler event mouse enter untuk menampilkan border merah saat hover.

        Args:
            event: Event enter dari Qt
        """
        self.setStyleSheet("#MovieCardPoster { border: 2px solid #E50914; }")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Handler event mouse leave untuk menghilangkan border saat tidak di-hover.

        Args:
            event: Event leave dari Qt
        """
        self.setStyleSheet("#MovieCardPoster { border: none; }")
        super().leaveEvent(event)
