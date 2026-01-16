"""
History Page untuk menampilkan riwayat tontonan.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from app.services.history_service import HistoryService, HistoryItem
from app.services.image_cache import ImageCache


class HistoryCard(QFrame):
    """Card untuk menampilkan satu item history."""

    clicked = Signal(object)  # HistoryItem
    deleteClicked = Signal(str)  # history_id

    def __init__(self, item: HistoryItem, cache: ImageCache):
        super().__init__()
        self.item = item
        self.cache = cache
        self.setObjectName("HistoryCard")
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#HistoryCard {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
            }
            QFrame#HistoryCard:hover {
                background: #252525;
                border-color: #E50914;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Poster
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(70, 100)
        self.poster_label.setStyleSheet("background: #333; border-radius: 4px;")
        self.poster_label.setScaledContents(True)
        layout.addWidget(self.poster_label)

        # Load poster async
        if self.item.poster_url:
            self.cache.get_image(self.item.poster_url, self._on_poster_loaded)

        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Title
        title_label = QLabel(self.item.title)
        title_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)

        # Episode
        if self.item.episode_title:
            ep_label = QLabel(f"▶ {self.item.episode_title}")
            ep_label.setStyleSheet("color: #E50914; font-size: 12px; font-weight: bold;")
            info_layout.addWidget(ep_label)

        # Source
        source_label = QLabel(f"📺 {self.item.source.upper()}")
        source_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(source_label)

        # Watched time
        watched_label = QLabel(f"🕐 {self._format_time(self.item.watched_at)}")
        watched_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(watched_label)

        info_layout.addStretch()
        layout.addLayout(info_layout, 1)

        # Delete button
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #E50914;
            }
        """)
        delete_btn.clicked.connect(lambda: self.deleteClicked.emit(self.item.id))
        layout.addWidget(delete_btn, 0, Qt.AlignmentFlag.AlignTop)

    def _on_poster_loaded(self, filepath: str):
        if filepath and isinstance(filepath, str):
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                self.poster_label.setPixmap(pixmap)

    def _format_time(self, iso_time: str) -> str:
        """Format ISO timestamp ke bentuk yang lebih readable."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_time)
            now = datetime.now()
            diff = now - dt

            if diff.days == 0:
                hours = diff.seconds // 3600
                if hours == 0:
                    mins = diff.seconds // 60
                    return f"{mins} menit lalu" if mins > 0 else "Baru saja"
                return f"{hours} jam lalu"
            elif diff.days == 1:
                return "Kemarin"
            elif diff.days < 7:
                return f"{diff.days} hari lalu"
            else:
                return dt.strftime("%d %b %Y")
        except Exception:
            return iso_time

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item)
        super().mousePressEvent(event)


class HistoryPage(QWidget):
    """Halaman untuk menampilkan riwayat tontonan."""

    historyClicked = Signal(object)  # HistoryItem
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self, cache: ImageCache):
        super().__init__()
        self.cache = cache
        self.history_service = HistoryService()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("📜 Riwayat Tontonan")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.clear_btn = QPushButton("Hapus Semua")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: #aaa;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #E50914;
                color: white;
            }
        """)
        self.clear_btn.clicked.connect(self._on_clear_all)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # Scroll area for history list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 10, 0)
        self.history_layout.setSpacing(10)
        self.history_layout.addStretch()

        scroll.setWidget(self.history_container)
        layout.addWidget(scroll)

        # Empty state label
        self.empty_label = QLabel("Belum ada riwayat tontonan.\nMulai menonton untuk melihat riwayat di sini.")
        self.empty_label.setStyleSheet("color: #666; font-size: 14px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

    def refresh(self):
        """Refresh daftar history."""
        # Clear existing cards
        while self.history_layout.count() > 1:  # Keep the stretch
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load history
        items = self.history_service.get_history(limit=50)

        if not items:
            self.empty_label.show()
            self.clear_btn.setEnabled(False)
        else:
            self.empty_label.hide()
            self.clear_btn.setEnabled(True)

            for history_item in items:
                card = HistoryCard(history_item, self.cache)
                card.clicked.connect(self._on_history_clicked)
                card.deleteClicked.connect(self._on_delete_item)
                self.history_layout.insertWidget(self.history_layout.count() - 1, card)

    def _on_history_clicked(self, item: HistoryItem):
        self.historyClicked.emit(item)

    def _on_delete_item(self, history_id: str):
        self.history_service.delete_item(history_id)
        self.refresh()

    def _on_clear_all(self):
        reply = QMessageBox.question(
            self,
            "Hapus Semua History",
            "Apakah Anda yakin ingin menghapus semua riwayat tontonan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_service.clear_history()
            self.refresh()

    def showEvent(self, event):
        """Handler saat halaman ditampilkan."""
        super().showEvent(event)
        self.refresh()

    def stop(self):
        """Stop any ongoing operations."""
        pass

    def reset(self):
        """Reset halaman ke state awal."""
        pass
