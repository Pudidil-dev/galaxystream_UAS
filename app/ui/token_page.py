"""
Token Settings Page untuk pengaturan API token.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QSettings
import requests


class TokenPage(QWidget):
    """Halaman untuk pengaturan API token."""

    tokenChanged = Signal(str)
    backClicked = Signal()
    loadingRequested = Signal(str)
    loadingFinished = Signal()

    def __init__(self):
        super().__init__()
        self.settings = QSettings("GalaxyStream", "GalaxyStream")
        self.setup_ui()
        self._load_token()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with back button
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Kembali")
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #E50914;
            }
        """)
        back_btn.clicked.connect(self.backClicked.emit)
        header_layout.addWidget(back_btn)

        header_layout.addStretch()

        title = QLabel("🔑 Pengaturan API Token")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()
        # Spacer untuk balance
        spacer = QLabel()
        spacer.setFixedWidth(80)
        header_layout.addWidget(spacer)

        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Token API digunakan untuk mengakses konten dari Netshort dan Melolo.\n"
            "Jika token tidak valid, konten dari sumber tersebut tidak dapat diakses."
        )
        desc.setStyleSheet("color: #aaa; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Token input section
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)

        token_label = QLabel("Bearer Token:")
        token_label.setStyleSheet("color: #ccc; font-size: 13px;")
        input_layout.addWidget(token_label)

        # Token input with show/hide toggle
        token_input_layout = QHBoxLayout()

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Masukkan Bearer Token...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setStyleSheet("""
            QLineEdit {
                background: #0a0a0a;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #E50914;
            }
        """)
        token_input_layout.addWidget(self.token_input)

        self.show_btn = QPushButton("👁")
        self.show_btn.setFixedSize(44, 44)
        self.show_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #444;
            }
        """)
        self.show_btn.clicked.connect(self._toggle_token_visibility)
        token_input_layout.addWidget(self.show_btn)

        input_layout.addLayout(token_input_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        self.validate_btn = QPushButton("Validasi Token")
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #444;
            }
            QPushButton:disabled {
                background: #222;
                color: #666;
            }
        """)
        self.validate_btn.clicked.connect(self._validate_token)
        btn_layout.addWidget(self.validate_btn)

        self.save_btn = QPushButton("Simpan Token")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #E50914;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff1a1a;
            }
        """)
        self.save_btn.clicked.connect(self._save_token)
        btn_layout.addWidget(self.save_btn)

        btn_layout.addStretch()

        input_layout.addLayout(btn_layout)

        layout.addWidget(input_frame)

        # Status message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 13px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Info about default token
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: #1a2a1a;
                border: 1px solid #2a4a2a;
                border-radius: 8px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 15, 15, 15)

        info_title = QLabel("ℹ️ Informasi")
        info_title.setStyleSheet("color: #6a6; font-size: 13px; font-weight: bold;")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Jika token kosong atau tidak valid, aplikasi akan menggunakan token default.\n"
            "Token default mungkin memiliki rate limit atau batasan tertentu."
        )
        info_text.setStyleSheet("color: #8a8; font-size: 12px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        layout.addStretch()

    def _load_token(self):
        """Load token dari settings."""
        token = self.settings.value("captain_token", "")
        if token:
            self.token_input.setText(token)

    def _toggle_token_visibility(self):
        """Toggle show/hide token."""
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText("🙈")
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText("👁")

    def _validate_token(self):
        """Validasi token dengan test API call."""
        token = self.token_input.text().strip()

        if not token:
            self._show_status("⚠️ Token tidak boleh kosong", error=True)
            return

        self._show_status("Memvalidasi token...", error=False)
        self.validate_btn.setEnabled(False)

        try:
            # Test dengan endpoint Netshort explore
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "GalaxyStream/1.0"
            }
            response = requests.get(
                "https://captain.sapimu.au/netshort/api/v1/explore?offset=0&limit=1",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self._show_status("✅ Token valid! Anda dapat menyimpan token ini.", error=False)
            elif response.status_code == 401:
                self._show_status("❌ Token tidak valid atau sudah kadaluarsa.", error=True)
            elif response.status_code == 403:
                self._show_status("❌ Token tidak memiliki akses ke API ini.", error=True)
            else:
                self._show_status(f"⚠️ Response tidak terduga: {response.status_code}", error=True)

        except requests.Timeout:
            self._show_status("⚠️ Timeout - Tidak dapat terhubung ke server.", error=True)
        except requests.RequestException as e:
            self._show_status(f"⚠️ Error: {str(e)}", error=True)
        finally:
            self.validate_btn.setEnabled(True)

    def _save_token(self):
        """Simpan token ke settings."""
        token = self.token_input.text().strip()

        if not token:
            # Hapus custom token, gunakan default
            self.settings.remove("captain_token")
            self._show_status("✅ Token dihapus. Menggunakan token default.", error=False)
        else:
            self.settings.setValue("captain_token", token)
            self._show_status("✅ Token berhasil disimpan!", error=False)

        self.tokenChanged.emit(token)

    def _show_status(self, message: str, error: bool = False):
        """Tampilkan pesan status."""
        color = "#E50914" if error else "#6a6"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")
        self.status_label.setText(message)

    def showEvent(self, event):
        """Handler saat halaman ditampilkan."""
        super().showEvent(event)
        self._load_token()

    def stop(self):
        """Stop any ongoing operations."""
        pass

    def reset(self):
        """Reset halaman ke state awal."""
        self.status_label.setText("")
