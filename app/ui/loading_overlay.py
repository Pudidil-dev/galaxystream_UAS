from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

class LoadingOverlay(QWidget):
    """
    Overlay loading yang semi-transparan dengan animasi spinner.

    Widget ini ditampilkan di atas konten utama saat aplikasi sedang memuat data,
    dengan efek fade in/out untuk transisi yang smooth.
    """
    def __init__(self, parent=None):
        """
        Inisialisasi loading overlay.

        Args:
            parent: Widget parent untuk overlay ini
        """
        super().__init__(parent)
        self.setFixedSize(parent.size() if parent else self.size())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        # Background
        self.bg = QWidget(self)
        self.bg.setObjectName("LoadingBG")
        self.bg.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.bg_layout = QVBoxLayout(self.bg)
        self.bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner/Label
        self.spinner = QLabel("🍿") # Popcorn emoji as a simple "spinner"
        self.spinner.setStyleSheet("font-size: 64px; background: transparent;")
        self.bg_layout.addWidget(self.spinner)

        self.label = QLabel("Loading...")
        self.label.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 10px; background: transparent;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_layout.addWidget(self.label)

        # Opacity effect for fade in/out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.hide()

    def show_loading(self, message="Loading..."):
        """
        Menampilkan overlay loading dengan pesan tertentu.

        Args:
            message: Pesan yang ditampilkan saat loading (default: "Loading...")
        """
        if self.parent():
            self.setFixedSize(self.parent().size())
        self.label.setText(message)
        self.show()
        self.raise_()
        self.opacity_anim.setStartValue(0.0)
        self.opacity_anim.setEndValue(1.0)
        self.opacity_anim.start()

    def hide_loading(self):
        """
        Menyembunyikan overlay loading dengan efek fade out.
        """
        self.opacity_anim.setStartValue(self.opacity_effect.opacity())
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()

    def resizeEvent(self, event):
        """
        Handler event resize untuk menyesuaikan ukuran overlay dengan parent.

        Args:
            event: Event resize dari Qt
        """
        if self.parent():
            self.setFixedSize(self.parent().size())
            self.bg.setFixedSize(self.parent().size())
        super().resizeEvent(event)
