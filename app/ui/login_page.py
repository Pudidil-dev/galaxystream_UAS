from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QUrl
from PySide6.QtGui import QDesktopServices


class AuthWorker(QThread):
    """
    Thread worker untuk operasi authentication (sign in / sign up).

    Attributes:
        success: Signal yang emit session object jika berhasil
        failure: Signal yang emit error message jika gagal
        signup_pending: Signal yang emit ketika signup berhasil tapi perlu email confirmation
    """
    success = Signal(object)
    failure = Signal(str)
    signup_pending = Signal(str)  # New signal for pending email confirmation

    def __init__(self, fn, *args, is_signup=False):
        """
        Initialize auth worker.

        Args:
            fn: Function to call (sign_in_email or sign_up_email)
            *args: Arguments to pass to function
            is_signup: True jika ini operasi signup (default: False)
        """
        super().__init__()
        self.fn = fn
        self.args = args
        self.is_signup = is_signup

    def run(self):
        try:
            session = self.fn(*self.args)
            if session:
                self.success.emit(session)
            else:
                # No session - different handling for signup vs signin
                if self.is_signup:
                    # For signup, no session might mean email confirmation required
                    self.signup_pending.emit("Account created! Check your email for confirmation link.")
                else:
                    self.failure.emit("No session returned")
        except Exception as e:
            self.failure.emit(str(e))


class OAuthWaiter(QThread):
    success = Signal(object)
    failure = Signal(str)

    def __init__(self, auth_client, server):
        super().__init__()
        self.auth_client = auth_client
        self.server = server

    def run(self):
        try:
            result = self.server.wait_for_result(timeout=180)
            self.server.stop()
            if not isinstance(result, dict):
                self.failure.emit("oauth_invalid_response")
                return
            if "error" in result:
                self.failure.emit(result.get("error", "oauth_failed"))
                return

            code = result.get("code")
            if not code:
                self.failure.emit("missing_code")
                return

            session = self.auth_client.exchange_code_for_session(code)
            if session:
                self.success.emit(session)
            else:
                self.failure.emit("No session returned")
        except Exception as e:
            self.failure.emit(str(e))


class LoginPage(QWidget):
    loginSuccess = Signal(object)
    loginFailed = Signal(str)

    def __init__(self, auth_client):
        super().__init__()
        self.auth_client = auth_client
        self.worker = None
        self.oauth_worker = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("background-color: #0B0D12;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("LoginCard")
        card.setMaximumWidth(460)
        card.setStyleSheet(
            "#LoginCard { background-color: #161a21; border: 1px solid #2a2e37; "
            "border-radius: 12px; }"
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)

        title = QLabel("GalaxyStream")
        title.setStyleSheet("font-size: 32px; font-weight: 900; color: #E5E5E5; background: #161a21;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Sign in to continue")
        subtitle.setStyleSheet("color: #E5E5E5; font-size: 14px; background: #161a21;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(subtitle)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #E5E5E5; font-size: 12px; background: #161a21;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.error_label)

        self.google_btn = QPushButton("Sign in with Google")
        self.google_btn.setFixedHeight(44)
        self.google_btn.setStyleSheet(
            "QPushButton {"
            "background: #161a21; color: #E5E5E5; border-radius: 6px; "
            "font-weight: bold; border: 1px solid #2a2e37;"
            "}"
            "QPushButton:hover { background: #1c222b; }"
        )
        self.google_btn.clicked.connect(self._on_google_clicked)
        card_layout.addWidget(self.google_btn)

        divider = QLabel("OR")
        divider.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider.setStyleSheet("color: #E5E5E5; font-size: 12px; background: #161a21;")
        card_layout.addWidget(divider)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setFixedHeight(40)
        self.email_input.setStyleSheet(
            "background: #161a21; color: #fff; border: 1px solid #2a2e37; "
            "border-radius: 6px; padding: 0 12px;"
        )
        card_layout.addWidget(self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(40)
        self.password_input.setStyleSheet(
            "background: #161a21; color: #fff; border: 1px solid #2a2e37; "
            "border-radius: 6px; padding: 0 12px;"
        )
        card_layout.addWidget(self.password_input)

        btn_row = QHBoxLayout()
        self.sign_in_btn = QPushButton("Sign In")
        self.sign_in_btn.setFixedHeight(44)
        self.sign_in_btn.setObjectName("PrimaryButton")
        self.sign_in_btn.clicked.connect(self._on_sign_in)
        btn_row.addWidget(self.sign_in_btn)

        self.sign_up_btn = QPushButton("Create Account")
        self.sign_up_btn.setFixedHeight(44)
        self.sign_up_btn.setObjectName("SecondaryButton")
        self.sign_up_btn.clicked.connect(self._on_sign_up)
        btn_row.addWidget(self.sign_up_btn)

        card_layout.addLayout(btn_row)
        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _set_loading(self, is_loading, message=""):
        self.error_label.setText(message if message else "")
        self.google_btn.setEnabled(not is_loading)
        self.sign_in_btn.setEnabled(not is_loading)
        self.sign_up_btn.setEnabled(not is_loading)

    def _on_sign_in(self):
        self._clear_error()
        if not self.auth_client.is_available():
            self._show_error("Supabase not configured")
            return
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            self._show_error("Email and password required")
            return
        self._set_loading(True, "Signing in...")
        self.worker = AuthWorker(self.auth_client.sign_in_email, email, password)
        self.worker.success.connect(self._on_login_success)
        self.worker.failure.connect(self._on_login_failed)
        self.worker.start()

    def _on_sign_up(self):
        """Handle sign up button click."""
        self._clear_error()
        if not self.auth_client.is_available():
            self._show_error("Supabase not configured")
            return
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or not password:
            self._show_error("Email and password required")
            return
        self._set_loading(True, "Creating account...")
        self.worker = AuthWorker(self.auth_client.sign_up_email, email, password, is_signup=True)
        self.worker.success.connect(self._on_login_success)
        self.worker.failure.connect(self._on_login_failed)
        self.worker.signup_pending.connect(self._on_signup_pending)
        self.worker.start()

    def _on_google_clicked(self):
        self._clear_error()
        if not self.auth_client.is_available():
            self._show_error("Supabase not configured")
            return
        self._set_loading(True, "Opening Google login...")
        try:
            auth_url, server = self.auth_client.start_google_oauth()
        except Exception as e:
            self._on_login_failed(str(e))
            return

        if auth_url:
            QDesktopServices.openUrl(QUrl(auth_url))
        else:
            self._on_login_failed("Missing auth URL")
            return

        self.oauth_worker = OAuthWaiter(self.auth_client, server)
        self.oauth_worker.success.connect(self._on_login_success)
        self.oauth_worker.failure.connect(self._on_login_failed)
        self.oauth_worker.start()

    def _on_login_success(self, session):
        """Handle successful login/signup with session."""
        self._set_loading(False)
        self.loginSuccess.emit(session)

    def _on_signup_pending(self, message):
        """Handle successful signup but pending email confirmation."""
        self._set_loading(False)
        # Show success message with detailed instructions
        detailed_msg = (
            " Account created!\n\n"
            "1. Check your email for confirmation link\n"
            "2. Click the confirmation link\n"
            "3. Close the browser tab (ignore 'localhost' error)\n"
            "4. Return here and login with your credentials"
        )
        self.error_label.setStyleSheet(
            "color: #4CAF50; font-size: 12px; background: #161a21; "
            "padding: 10px; border: 1px solid #4CAF50; border-radius: 4px;"
        )
        self.error_label.setText(detailed_msg)
        # Note: Don't emit loginSuccess - user needs to confirm email first

    def _on_login_failed(self, message):
        """Handle failed login/signup."""
        self._set_loading(False)
        if message == "No session returned" and self.auth_client.has_session():
            self._on_login_success(self.auth_client.get_session())
            return
        self._show_error(message)
        self.loginFailed.emit(message)

    def _show_error(self, message):
        """Show error message in red."""
        self.error_label.setStyleSheet("color: #E5E5E5; font-size: 12px; background: #161a21;")  # Red for error
        self.error_label.setText(message)

    def _clear_error(self):
        self.error_label.setText("")

    def reset(self):
        self.email_input.clear()
        self.password_input.clear()
        self._clear_error()
