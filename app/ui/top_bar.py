from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel, QPushButton, QMenu
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction

class TopBar(QWidget):
    """
    Widget top bar yang menampilkan search box dan ikon notifikasi/profil.

    Top bar ini muncul di bagian atas aplikasi dan menyediakan fitur pencarian
    dengan debouncing untuk menghindari pencarian yang terlalu sering.
    """
    searchChanged = Signal(str)
    logoutRequested = Signal()
    switchSourceRequested = Signal()
    profileRequested = Signal()  # Signal baru untuk membuka halaman Profile

    def __init__(self):
        """Inisialisasi top bar dengan komponen UI dan timer untuk search debouncing."""
        super().__init__()
        self.setObjectName("TopBar")
        self.setFixedHeight(100)
        self.setup_ui()

        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._emit_search)

    def setup_ui(self):
        """Menyiapkan layout dan komponen UI untuk top bar."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(20)

        # Space Filler or Navigation
        layout.addStretch()

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Titles, people, genres")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        layout.addWidget(self.search_input)

        # Icons
        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setStyleSheet("background:transparent; border:none; font-size: 20px;")
        layout.addWidget(self.notif_btn)

        self.profile_btn = QPushButton("👤")
        self.profile_btn.setStyleSheet("background:transparent; border:none; font-size: 20px;")
        self.profile_btn.clicked.connect(self._show_profile_menu)
        layout.addWidget(self.profile_btn)

    def _on_search_text_changed(self, text):
        """
        Handler ketika teks pencarian berubah.

        Menggunakan timer debouncing untuk menunda emit signal hingga user
        berhenti mengetik selama 700ms.
        """
        self.search_timer.start(700)

    def _emit_search(self):
        """Emit signal searchChanged dengan query pencarian saat timer selesai."""
        self.searchChanged.emit(self.search_input.text())

    def _show_profile_menu(self):
        """
        Menampilkan dropdown menu profil dengan opsi switch source dan logout.

        Menu ini muncul ketika user klik tombol profil di top bar.
        """
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                color: #fff;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #E50914;
            }
        """)

        # Account info (disabled, just for display)
        account_action = QAction("👤 Alex Astronaut", self)
        account_action.setEnabled(False)
        menu.addAction(account_action)

        menu.addSeparator()

        # Token Settings action
        profile_action = QAction("🔑 Token Settings", self)
        profile_action.triggered.connect(self._on_profile)
        menu.addAction(profile_action)

        # Switch Source action
        switch_source_action = QAction("🔄 Switch Source", self)
        switch_source_action.triggered.connect(self._on_switch_source)
        menu.addAction(switch_source_action)

        menu.addSeparator()

        # Logout action
        logout_action = QAction("🚪 Logout", self)
        logout_action.triggered.connect(self._on_logout)
        menu.addAction(logout_action)

        # Show menu below profile button
        menu.exec(self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft()))

    def _on_logout(self):
        """
        Handler untuk logout action.

        Emit signal logoutRequested yang akan dihandle oleh MainWindow
        untuk melakukan proses logout dan kembali ke halaman login.
        """
        self.logoutRequested.emit()

    def _on_switch_source(self):
        """
        Handler untuk switch source action.

        Emit signal switchSourceRequested yang akan dihandle oleh MainWindow
        untuk kembali ke halaman source selection.
        """
        self.switchSourceRequested.emit()

    def _on_profile(self):
        """
        Handler untuk profile action.

        Emit signal profileRequested yang akan dihandle oleh MainWindow
        untuk membuka halaman Profile dengan History dan Token settings.
        """
        self.profileRequested.emit()
