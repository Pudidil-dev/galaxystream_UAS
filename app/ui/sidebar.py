from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QButtonGroup
from PySide6.QtCore import Qt, Signal

class Sidebar(QWidget):
    """
    Widget sidebar navigasi untuk menu utama aplikasi.

    Sidebar ini menampilkan logo, menu navigasi dengan tombol-tombol untuk
    berpindah halaman, tombol untuk switch source, dan informasi profil user.
    """
    navigationChanged = Signal(str)

    def __init__(self):
        """Inisialisasi sidebar dengan komponen UI."""
        super().__init__()
        self.setObjectName("Sidebar")
        self.setup_ui()

    def setup_ui(self):
        """
        Menyiapkan layout dan komponen UI untuk sidebar.

        Membuat menu navigasi dengan button group untuk memastikan hanya
        satu menu yang aktif pada satu waktu, serta tombol untuk switch source.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        self.logo_label = QLabel("GALAXY")
        self.logo_label.setObjectName("SidebarLogo")
        layout.addWidget(self.logo_label)

        # Menu List
        self.menu_container = QWidget()
        self.menu_container.setObjectName("SidebarMenu")
        self.menu_layout = QVBoxLayout(self.menu_container)
        self.menu_layout.setContentsMargins(0, 20, 0, 10)
        self.menu_layout.setSpacing(0)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        menu_items = [
            ("Home", "home"),
            ("Popular", "popular"),
            ("For You", "foryou"),
            ("Random Drama", "random"),
            ("Search", "search"),
            ("History", "history"),
            ("My List", "mylist")
        ]

        for label, page_id in menu_items:
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda checked, pid=page_id: self.navigationChanged.emit(pid))
            self.button_group.addButton(btn)
            self.menu_layout.addWidget(btn)
            if page_id == "home":
                btn.setChecked(True)

        layout.addWidget(self.menu_container)
        layout.addStretch()

        # profile marker
        profile = QLabel("Alex Astronaut")
        profile.setStyleSheet("padding: 20px; color: #666; font-size: 12px;")
        layout.addWidget(profile)
