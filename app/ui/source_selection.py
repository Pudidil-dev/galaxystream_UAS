from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QGridLayout, QApplication, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont, QScreen

class SourceCard(QFrame):
    """
    Widget kartu untuk menampilkan pilihan sumber konten.

    Kartu ini menampilkan ikon, judul, dan deskripsi dari sebuah sumber konten
    (dramabox, netshort, atau komik) yang dapat diklik oleh user.
    """
    clicked = Signal(str)

    def __init__(self, source_id, title, description, icon_text):
        """
        Inisialisasi source card.

        Args:
            source_id: ID unik sumber konten
            title: Judul sumber konten
            description: Deskripsi singkat sumber konten
            icon_text: Emoji atau teks ikon yang ditampilkan
        """
        super().__init__()
        self.source_id = source_id
        self.setObjectName("SourceCard")

        # Calculate card size based on screen resolution (smaller size)
        screen = QApplication.primaryScreen().availableGeometry()
        card_width = int(screen.width() * 0.10)  # 10% of screen width (reduced from 14%)
        card_height = int(screen.height() * 0.20)  # 20% of screen height (reduced from 28%)

        # Set minimum and maximum constraints (smaller limits)
        card_width = max(120, min(card_width, 180))  # Between 120-180px (reduced from 150-250px)
        card_height = max(140, min(card_height, 220))  # Between 140-220px (reduced from 180-300px)

        self.setFixedSize(card_width, card_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Calculate responsive margins and spacing based on card size
        margin_h = int(card_width * 0.08)  # 8% of card width
        margin_v = int(card_height * 0.09)  # 9% of card height
        spacing = int(card_height * 0.045)  # 4.5% of card height

        layout = QVBoxLayout(self)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        layout.setSpacing(spacing)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Responsive icon size (18% of card height)
        icon_size = int(card_height * 0.18)
        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"font-size: {icon_size}px;")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Responsive title size (7.3% of card height)
        title_size = int(card_height * 0.073)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: {title_size}px; font-weight: bold; color: white;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Responsive description size (5% of card height)
        desc_size = int(card_height * 0.05)
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"font-size: {desc_size}px; color: #aaa;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)

        self.setStyleSheet("""
            #SourceCard {
                background-color: #161a21;
                border: 1px solid #2a2e37;
                border-radius: 12px;
            }
            #SourceCard:hover {
                background-color: #1c222b;
                border-color: #E50914;
            }
        """)

    def mousePressEvent(self, event):
        """
        Handler event klik mouse untuk emit signal dengan source_id.

        Args:
            event: Event mouse press dari Qt
        """
        self.clicked.emit(self.source_id)

class SourceSelectionPage(QWidget):
    """
    Halaman pemilihan sumber konten (dramabox/netshort/komik).

    Halaman ini ditampilkan saat pertama kali aplikasi dibuka, memungkinkan
    user untuk memilih sumber konten yang ingin mereka akses.
    """
    sourceSelected = Signal(str)

    def __init__(self):
        """Inisialisasi halaman pemilihan sumber."""
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout dan komponen UI untuk halaman pemilihan sumber.

        Menampilkan logo aplikasi, judul, grid kartu sumber, dan footer.
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSpacing(20)  # Reduced from 50 for more compact layout
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # Add margins for better spacing

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)  # Add tighter spacing between logo and subtitle

        # Responsive logo size based on screen width
        screen = QApplication.primaryScreen().availableGeometry()
        logo_size = int(screen.width() * 0.035)  # 3.5% of screen width
        logo_size = max(36, min(logo_size, 60))  # Between 36-60px

        logo = QLabel("GalaxyStream")
        logo.setStyleSheet(f"font-size: {logo_size}px; font-weight: 900; color: #E50914; letter-spacing: -2px;")
        header_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        # Responsive subtitle size
        subtitle_size = int(screen.width() * 0.013)  # 1.3% of screen width
        subtitle_size = max(14, min(subtitle_size, 22))  # Between 14-22px

        subtitle = QLabel("Choose Your Entertainment Galaxy")
        subtitle.setStyleSheet(f"font-size: {subtitle_size}px; color: #888;")
        header_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(header_layout)

        # Scroll area for grid container (allows scrolling when window is small)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #E50914;
                border-radius: 5px;
            }
            QScrollBar:horizontal {
                background: #1a1a1a;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background: #E50914;
                border-radius: 5px;
            }
        """)

        # Grid of sources
        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(grid_container)

        # Responsive grid spacing based on screen size (smaller spacing)
        screen = QApplication.primaryScreen().availableGeometry()
        grid_spacing = int(screen.width() * 0.010)  # 1.0% of screen width (reduced from 1.5%)
        grid_spacing = max(10, min(grid_spacing, 20))  # Between 10-20px (reduced from 15-30px)
        self.grid_layout.setSpacing(grid_spacing)

        sources = [
            ("dramabox", "DramaBox", "Premium short and long dramas.", "🎭"),
            ("netshort", "NetShort", "Exclusive fast-paced narratives.", "🎬"),
            ("melolo", "Melolo", "Discover unique stories and series.", "📖"),
            ("anime", "Anime", "Watch your favorite anime series.", "🎌"),
            ("komik", "Komik", "Read manga and comics online.", "📚")
        ]

        for i, (sid, name, desc, icon) in enumerate(sources):
            card = SourceCard(sid, name, desc, icon)
            card.clicked.connect(self.sourceSelected.emit)
            row = i // 3  # 3 columns per row (better for 7 items)
            col = i % 3
            self.grid_layout.addWidget(card, row, col)

        # Add grid container to scroll area
        scroll_area.setWidget(grid_container)

        # Add scroll area to main layout
        self.main_layout.addWidget(scroll_area)

        # Footer
        footer = QLabel("Discover unique stories across different dimensions.")
        footer.setStyleSheet("color: #444; font-size: 12px; margin-top: 20px;")
        self.main_layout.addWidget(footer, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet("background-color: #0B0D12;")
