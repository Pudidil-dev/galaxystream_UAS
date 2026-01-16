import os
import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt
from app.ui.sidebar import Sidebar
from app.ui.top_bar import TopBar
from app.ui.home_page import HomePage
from app.ui.player import PlayerPage
from app.ui.browse_page import BrowsePage
from app.ui.search_page import SearchPage
from app.ui.anime_page import AnimePage
from app.ui.anime_episode_page import AnimeEpisodePage
from app.ui.source_selection import SourceSelectionPage
from app.ui.comic_reader import ComicReader
from app.ui.detail_page import DetailPage
from app.ui.loading_overlay import LoadingOverlay
from app.ui.login_page import LoginPage
from app.ui.history_page import HistoryPage
from app.ui.token_page import TokenPage
from app.services.api_client import APIClient
from app.services.auth_client import AuthClient
from app.services.image_cache import ImageCache


class MainWindow(QMainWindow):
    """
    Jendela utama aplikasi GalaxyStream.

    Class ini mengatur seluruh tampilan aplikasi, termasuk sidebar, top bar,
    navigasi antar halaman, dan integrasi dengan API client dan image cache.
    """
    def __init__(self):
        """
        Inisialisasi main window dengan semua komponen UI dan service.
        """
        super().__init__()
        self.setWindowTitle("GalaxyStream")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 600)  # Set minimum window size to prevent layout issues

        self.api = APIClient()
        self.cache = ImageCache()
        self.auth = AuthClient()

        # Debounce flag untuk mencegah rapid source switching
        self._switching_source = False

        self.setup_ui()
        self.load_styles()

    def setup_ui(self):
        """
        Menyiapkan semua komponen UI termasuk sidebar, top bar, dan semua halaman.

        Metode ini membuat struktur UI utama dengan stacked widget untuk navigasi
        antar halaman, dan menghubungkan semua signal-slot yang diperlukan.
        """
        self.central = QWidget()
        self.central.setObjectName("CentralWidget")
        self.setCentralWidget(self.central)
        layout = QHBoxLayout(self.central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main Area (contains sidebar + rest)
        self.main_container = QStackedWidget()

        # 0. Login Page
        self.login_page = LoginPage(self.auth)
        self.login_page.loginSuccess.connect(self._on_login_success)
        self.main_container.addWidget(self.login_page)

        # 1. Source Selection
        self.source_selection = SourceSelectionPage()
        self.source_selection.sourceSelected.connect(self._on_source_selected)
        self.main_container.addWidget(self.source_selection)

        # 2. Main App Content
        self.app_content = QWidget()
        self.app_layout = QHBoxLayout(self.app_content)
        self.app_layout.setContentsMargins(0, 0, 0, 0)
        self.app_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigationChanged.connect(self._navigate)
        self.app_layout.addWidget(self.sidebar)

        # Content Area
        self.content_container = QWidget()
        self.content_container.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # TopBar
        self.top_bar = TopBar()
        self.top_bar.searchChanged.connect(self._on_search)
        self.top_bar.logoutRequested.connect(self._on_logout)
        self.top_bar.switchSourceRequested.connect(self._on_switch_source)
        self.top_bar.profileRequested.connect(self._on_profile_requested)
        self.content_layout.addWidget(self.top_bar)

        # Stack for pages
        self.stack = QStackedWidget()

        # Home Page
        self.home = HomePage(self.api, self.cache)
        self.home.movieClicked.connect(self._show_detail)
        self.home.loadingRequested.connect(self.show_loading)
        self.home.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.home)

        # Player Page
        self.player = PlayerPage(self.api)
        self.player.backClicked.connect(self._back_to_browse)
        self.player.toggleFullScreen.connect(self._toggle_full_screen)
        self.player.loadingRequested.connect(self.show_loading)
        self.player.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.player)

        # Comic Reader
        self.comic_reader = ComicReader(self.api, self.cache)
        self.comic_reader.backClicked.connect(self._back_to_browse)
        self.comic_reader.loadingRequested.connect(self.show_loading)
        self.comic_reader.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.comic_reader)

        # Browse Page
        self.browse = BrowsePage(self.api, self.cache)
        self.browse.movieClicked.connect(self._show_detail)
        self.browse.loadingRequested.connect(self.show_loading)
        self.browse.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.browse)

        # Search Page
        self.search_page = SearchPage(self.api, self.cache)
        self.search_page.movieClicked.connect(self._show_detail)
        self.search_page.loadingRequested.connect(self.show_loading)
        self.search_page.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.search_page)

        # Detail Page
        self.detail_page = DetailPage(self.api, self.cache)
        self.detail_page.backClicked.connect(self._back_to_browse)
        self.detail_page.playClicked.connect(self._play_content)
        self.detail_page.loadingRequested.connect(self.show_loading)
        self.detail_page.loadingFinished.connect(self.hide_loading)
        self.stack.addWidget(self.detail_page)

        # Anime Page
        print("[MAIN WINDOW] Creating AnimePage...", flush=True)
        self.anime_page = AnimePage(self.cache)
        print("[MAIN WINDOW] AnimePage created, connecting signals...", flush=True)
        self.anime_page.loadingRequested.connect(self.show_loading)
        self.anime_page.loadingFinished.connect(self.hide_loading)
        self.anime_page.animeClicked.connect(self._show_anime_episode)  # Connect to episode page
        self.stack.addWidget(self.anime_page)
        print("[MAIN WINDOW] AnimePage added to stack", flush=True)

        # Anime Episode Page
        print("[MAIN WINDOW] Creating AnimeEpisodePage...", flush=True)
        self.anime_episode_page = AnimeEpisodePage(self.cache)
        self.anime_episode_page.loadingRequested.connect(self.show_loading)
        self.anime_episode_page.loadingFinished.connect(self.hide_loading)
        self.anime_episode_page.backClicked.connect(self._back_to_anime_list)
        self.stack.addWidget(self.anime_episode_page)
        print("[MAIN WINDOW] AnimeEpisodePage added to stack", flush=True)

        # History Page
        print("[MAIN WINDOW] Creating HistoryPage...", flush=True)
        self.history_page = HistoryPage(self.cache)
        self.history_page.loadingRequested.connect(self.show_loading)
        self.history_page.loadingFinished.connect(self.hide_loading)
        self.history_page.historyClicked.connect(self._on_history_item_clicked)
        self.stack.addWidget(self.history_page)
        print("[MAIN WINDOW] HistoryPage added to stack", flush=True)

        # Token Page
        print("[MAIN WINDOW] Creating TokenPage...", flush=True)
        self.token_page = TokenPage()
        self.token_page.loadingRequested.connect(self.show_loading)
        self.token_page.loadingFinished.connect(self.hide_loading)
        self.token_page.backClicked.connect(self._back_from_token)
        self.token_page.tokenChanged.connect(self._on_token_changed)
        self.stack.addWidget(self.token_page)
        print("[MAIN WINDOW] TokenPage added to stack", flush=True)

        self.content_layout.addWidget(self.stack)
        self.app_layout.addWidget(self.content_container)

        self.main_container.addWidget(self.app_content)
        layout.addWidget(self.main_container)

        # Loading Overlay
        self.loading = LoadingOverlay(self)

        # Start with login or source selection
        self.auth.restore_session()
        if self.auth.has_session():
            self.main_container.setCurrentWidget(self.source_selection)
        else:
            self.main_container.setCurrentWidget(self.login_page)
            self.sidebar.hide()
            self.top_bar.hide()

        # Track navigation history for back button
        self.history = []

    def _on_login_success(self, session):
        """
        Handler ketika login berhasil.

        Args:
            session: Session object dari Supabase setelah login sukses
        """
        self.login_page.reset()
        self.main_container.setCurrentWidget(self.source_selection)
        self.sidebar.show()
        self.top_bar.show()

    def _on_logout(self):
        """
        Handler ketika user klik logout.

        Melakukan proses logout:
        1. Stop semua halaman yang sedang berjalan
        2. Clear session dari auth client
        3. Reset semua halaman ke state awal
        4. Kembali ke halaman login
        """
        print("[LOGOUT] User requested logout", flush=True)

        # Stop all ongoing operations
        self.player.stop()
        self.comic_reader.stop()
        self.home.stop()
        self.browse.stop()
        self.search_page.stop()
        self.detail_page.stop()
        self.anime_page.stop()

        # Clear authentication session
        try:
            self.auth.sign_out()
            print("[LOGOUT] Session cleared successfully", flush=True)
        except Exception as e:
            print(f"[LOGOUT] Error during sign out: {e}", flush=True)

        # Reset navigation history
        self.history = []

        # Reset all pages to initial state
        self.home.reset()
        self.browse.reset()
        self.search_page.reset()
        self.detail_page.reset()  # FIXED: Now has reset() method

        # Clear search input
        self.top_bar.search_input.clear()

        # Hide sidebar and topbar
        self.sidebar.hide()
        self.top_bar.hide()

        # Reset login page
        self.login_page.reset()

        # Switch to login page
        self.main_container.setCurrentWidget(self.login_page)

        print("[LOGOUT] Logout completed, showing login page", flush=True)

    def _on_switch_source(self):
        """
        Handler ketika user klik switch source dari profile menu.

        Menghentikan semua operasi yang sedang berjalan dan kembali
        ke halaman source selection untuk memilih sumber konten baru.
        """
        # FIXED: Debounce untuk prevent rapid switching
        if self._switching_source:
            print("[SWITCH SOURCE] Already switching, ignoring duplicate request...", flush=True)
            return

        self._switching_source = True
        print("[SWITCH SOURCE] User requested switch source", flush=True)

        # Stop all ongoing operations first
        print("[SWITCH SOURCE] Stopping all pages...", flush=True)
        self.player.stop()
        self.comic_reader.stop()
        self.home.stop()
        self.browse.stop()
        self.search_page.stop()
        self.detail_page.stop()
        self.anime_page.stop()

        # Reset all pages to clear any cached data and widgets
        print("[SWITCH SOURCE] Resetting all pages...", flush=True)
        self.home.reset()
        self.browse.reset()
        self.search_page.reset()
        self.detail_page.reset()  # FIXED: Now has reset() method
        if hasattr(self.anime_page, 'reset'):
            self.anime_page.reset()

        # FIXED: Async cache clearing - tidak blocking UI
        print("[SWITCH SOURCE] Starting async cache clear...", flush=True)
        self.cache.clear_cache(async_mode=True)  # Async mode

        # REMOVED: processEvents() yang unnecessary dan bisa hang
        # from PySide6.QtWidgets import QApplication
        # QApplication.processEvents()  # ❌ REMOVED

        # Reset navigation history
        self.history = []

        # Clear search input
        self.top_bar.search_input.clear()

        # Hide sidebar and topbar
        self.sidebar.hide()
        self.top_bar.hide()

        # Switch to source selection page
        self.main_container.setCurrentWidget(self.source_selection)
        print("[SWITCH SOURCE] Switch source completed", flush=True)

        # Reset debounce flag setelah delay
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._reset_switching_flag)

    def _reset_switching_flag(self):
        """Reset flag switching source setelah delay."""
        self._switching_source = False
        print("[SWITCH SOURCE] Debounce flag reset", flush=True)

    def _on_source_selected(self, source_type):
        """
        Handler ketika user memilih sumber konten (dramabox/netshort/melolo/shortmax/flic/anime/komik).

        Args:
            source_type: Jenis sumber yang dipilih oleh user
        """
        print(f"[SOURCE SELECT] User selected source: {source_type}", flush=True)
        self.show_loading("Initializing Source...")

        # FIXED: Async cache clearing - tidak blocking UI
        print("[SOURCE SELECT] Starting async cache clear...", flush=True)
        self.cache.clear_cache(async_mode=True)

        # REMOVED: processEvents() yang bisa hang
        # from PySide6.QtWidgets import QApplication
        # QApplication.processEvents()  # ❌ REMOVED

        # Jika user pilih anime, langsung ke anime page tanpa sidebar
        if source_type == "anime":
            print("[MAIN WINDOW] Anime source selected, navigating to anime page...", flush=True)
            self.main_container.setCurrentWidget(self.app_content)
            self.sidebar.hide()  # Sembunyikan sidebar untuk anime
            self.top_bar.show()
            # Navigate to anime page
            self.stack.setCurrentWidget(self.anime_page)
            # Removed refresh() call - showEvent will trigger load automatically
            self.hide_loading()
            return

        # Untuk dramabox/netshort/melolo/shortmax/flic/komik, set source dan load home dengan sidebar
        print(f"[SOURCE SELECT] Setting API source to: {source_type}", flush=True)
        self.api.set_source(source_type)

        # Reset pages before loading new data
        print("[SOURCE SELECT] Resetting pages...", flush=True)
        self.home.reset()
        self.browse.reset()
        self.search_page.reset()

        # CRITICAL FIX: Set stack to home page to hide anime page
        print("[SOURCE SELECT] Switching stack to home page...", flush=True)
        self.stack.setCurrentWidget(self.home)

        # Now load fresh data from new source
        print("[SOURCE SELECT] Loading fresh data...", flush=True)
        self.home.refresh_data()

        self.main_container.setCurrentWidget(self.app_content)
        self.sidebar.show()  # Tampilkan sidebar untuk dramabox/netshort
        self.top_bar.show()
        self.hide_loading()

    def load_styles(self):
        """
        Memuat file QSS stylesheet untuk mengatur tampilan aplikasi.

        Method ini mendukung loading stylesheet baik saat development maupun
        saat aplikasi sudah di-bundle menjadi executable dengan PyInstaller.

        Prioritas loading:
        1. Coba load dari file .qss eksternal (development & bundled)
        2. Jika gagal, gunakan embedded stylesheet dari Python code
        """
        # Detect if running as bundled executable
        if getattr(sys, 'frozen', False):
            # Running as bundled .exe - PyInstaller sets sys._MEIPASS
            base_path = sys._MEIPASS
        else:
            # Running in normal Python environment
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        path = os.path.join(base_path, "styles", "dark_space.qss")
        print(f"[STYLES] Loading stylesheet from: {path}", flush=True)

        # Try to load from file first
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                print(f"[STYLES] ✓ Stylesheet loaded successfully from file", flush=True)
                return
            except Exception as e:
                print(f"[STYLES] ✗ Failed to load stylesheet from file: {e}", flush=True)
        else:
            print(f"[STYLES] WARNING: Stylesheet file not found at: {path}", flush=True)

        # Fallback: Use embedded stylesheet
        print(f"[STYLES] Using embedded stylesheet as fallback...", flush=True)
        try:
            from app.styles.embedded_styles import get_stylesheet
            self.setStyleSheet(get_stylesheet())
            print(f"[STYLES] ✓ Embedded stylesheet loaded successfully", flush=True)
        except Exception as e:
            print(f"[STYLES] ✗ CRITICAL: Failed to load embedded stylesheet: {e}", flush=True)

    def _navigate(self, page_id):
        """
        Navigasi ke halaman tertentu berdasarkan ID yang diberikan dari sidebar.

        Args:
            page_id: ID halaman tujuan (home/popular/foryou/random/search/mylist)
        """
        # Stop any ongoing fetches on hidden pages
        self.home.stop()
        self.browse.stop()
        self.search_page.stop()
        self.detail_page.stop()
        self.anime_page.stop()
        self.comic_reader.stop()
        self.history = [] # Reset history when using sidebar navigation

        if page_id == "home":
            self.stack.setCurrentWidget(self.home)
            self.top_bar.show()
        elif page_id == "popular":
            self.browse.load_category("popular")
            self.stack.setCurrentWidget(self.browse)
            self.top_bar.show()
        elif page_id == "foryou":
            self.browse.load_category("foryou")
            self.stack.setCurrentWidget(self.browse)
            self.top_bar.show()
        elif page_id == "random":
            self.browse.load_category("random")
            self.stack.setCurrentWidget(self.browse)
            self.top_bar.show()
        elif page_id == "search":
            self.stack.setCurrentWidget(self.search_page)
            self.top_bar.show()
            self.top_bar.search_input.setFocus()
        elif page_id == "history":
            self.stack.setCurrentWidget(self.history_page)
            self.history_page.refresh()
            self.top_bar.show()
        elif page_id == "mylist":
            self.stack.setCurrentWidget(self.home)
            self.top_bar.show()

    def _on_search(self, query):
        """
        Handler ketika user melakukan pencarian.

        Args:
            query: Kata kunci pencarian yang dimasukkan user
        """
        if query:
            self.history = [] # Reset history on new search
            self.search_page.search(query)
            self.stack.setCurrentWidget(self.search_page)

    def _show_detail(self, movie):
        """
        Menampilkan halaman detail untuk movie/drama/anime yang dipilih.

        Args:
            movie: Objek Movie yang akan ditampilkan detailnya
        """
        self.history.append(self.stack.currentWidget())
        self.stack.setCurrentWidget(self.detail_page)
        self.detail_page.load_movie(movie)

    def _show_anime_episode(self, anime):
        """
        Menampilkan halaman episode untuk anime yang dipilih.

        Args:
            anime: Objek Movie (anime) yang akan ditampilkan episode-nya
        """
        print(f"[MAIN WINDOW] Navigating to anime episode page for: {anime.title}", flush=True)
        self.history.append(self.stack.currentWidget())
        self.stack.setCurrentWidget(self.anime_episode_page)
        self.anime_episode_page.load_anime(anime)

    def _back_to_anime_list(self):
        """Kembali dari anime episode page ke anime list page."""
        print("[MAIN WINDOW] Back to anime list", flush=True)
        self.anime_episode_page.stop()

        if self.history:
            prev_page = self.history.pop()
            self.stack.setCurrentWidget(prev_page)
        else:
            self.stack.setCurrentWidget(self.anime_page)

    def _on_profile_requested(self):
        """Handler ketika user klik Token Settings dari menu."""
        print("[MAIN WINDOW] Opening token settings", flush=True)
        self.history.append(self.stack.currentWidget())
        self.stack.setCurrentWidget(self.token_page)

    def _back_from_token(self):
        """Kembali dari token page ke halaman sebelumnya."""
        print("[MAIN WINDOW] Back from token settings", flush=True)
        if self.history:
            prev_page = self.history.pop()
            self.stack.setCurrentWidget(prev_page)
        else:
            self.stack.setCurrentWidget(self.home)

    def _on_history_item_clicked(self, history_item):
        """Handler ketika user klik item history untuk melanjutkan tontonan."""
        from app.services.history_service import HistoryItem
        from app.models.movie import Movie

        print(f"[MAIN WINDOW] Resuming from history: {history_item.title}", flush=True)

        # Buat Movie object dari history
        movie = Movie(
            id=history_item.content_id,
            title=history_item.title,
            poster_url=history_item.poster_url,
            source_type=history_item.source
        )

        # Set source di API client
        if history_item.source:
            self.api.set_source(history_item.source)

        # Navigasi ke player
        self.history.append(self.stack.currentWidget())
        self.stack.setCurrentWidget(self.player)
        self.player.play_movie(movie)
        self.top_bar.hide()
        self.sidebar.hide()

    def _on_token_changed(self, token: str):
        """Handler ketika token berubah dari profile page."""
        print(f"[MAIN WINDOW] Token changed, reloading API client", flush=True)
        self.api.reload_token()

    def _play_content(self, movie, episode_index=0):
        """
        Memutar konten (video player atau comic reader) berdasarkan jenis source.

        Args:
            movie: Objek Movie yang akan diputar
            episode_index: Index episode yang akan diputar (default: 0)
        """
        self.history.append(self.stack.currentWidget())

        # Route to appropriate viewer based on source type
        if movie.source_type == "komik":
            self.stack.setCurrentWidget(self.comic_reader)
            self.comic_reader.load_comic(movie, episode_index)
        else:
            # All other content uses video player (dramabox, netshort, anime)
            self.stack.setCurrentWidget(self.player)
            # Pass episode_index to play_movie to start from selected episode
            self.player.play_movie(movie, initial_episode=episode_index)

        self.top_bar.hide()
        self.sidebar.hide()

    def _back_to_browse(self):
        """
        Kembali ke halaman sebelumnya berdasarkan navigation history.

        Metode ini juga menghentikan player/reader yang sedang berjalan dan
        keluar dari mode fullscreen jika aktif.
        """
        if self.isFullScreen():
            self._toggle_full_screen()
        self.player.stop()
        self.comic_reader.stop()
        self.detail_page.stop()

        if self.history:
            prev_page = self.history.pop()
            self.stack.setCurrentWidget(prev_page)
        else:
            self.stack.setCurrentWidget(self.home)

        self.top_bar.show()
        self.sidebar.show()

    def _toggle_full_screen(self):
        """
        Toggle mode fullscreen untuk video player.
        """
        if self.isFullScreen():
            self.showNormal()
            self.player.set_full_screen_mode(False)
        else:
            self.showFullScreen()
            self.player.set_full_screen_mode(True)

    def show_loading(self, message="Loading..."):
        """
        Menampilkan overlay loading dengan pesan tertentu.

        Args:
            message: Pesan yang ditampilkan saat loading (default: "Loading...")
        """
        self.loading.show_loading(message)

    def hide_loading(self):
        """
        Menyembunyikan overlay loading.
        """
        self.loading.hide_loading()

    def resizeEvent(self, event):
        """
        Handler event resize window untuk menyesuaikan ukuran loading overlay.

        Args:
            event: Event resize dari Qt
        """
        super().resizeEvent(event)
        if hasattr(self, 'loading'):
            self.loading.resize(self.size())

    def closeEvent(self, event):
        """
        Handler event penutupan aplikasi.

        Menghentikan semua halaman yang sedang berjalan dan membersihkan cache
        untuk menghemat storage.

        Args:
            event: Event close dari Qt
        """
        print("[SHUTDOWN] Closing application...", flush=True)

        # Debug: Show active threads
        import threading
        print(f"[SHUTDOWN] Active threads: {threading.active_count()}", flush=True)
        for thread in threading.enumerate():
            print(f"[SHUTDOWN]   - {thread.name} (daemon={thread.daemon}, alive={thread.is_alive()})", flush=True)

        # Stop all pages
        print("[SHUTDOWN] Stopping all pages...", flush=True)
        self.player.stop()
        self.comic_reader.stop()
        self.home.stop()
        self.browse.stop()
        self.search_page.stop()
        self.detail_page.stop()
        self.anime_page.stop()

        # Stop anime episode page if exists
        if hasattr(self, 'anime_episode_page'):
            self.anime_episode_page.stop()

        # Stop history and token pages if they exist
        if hasattr(self, 'history_page'):
            self.history_page.stop()
        if hasattr(self, 'token_page'):
            self.token_page.stop()

        # Clear cache completely when closing app
        print("[SHUTDOWN] Clearing cache...", flush=True)
        self.cache.clear_cache()

        # Shutdown OAuth server if running
        if hasattr(self.auth, '_oauth_server') and self.auth._oauth_server:
            print("[SHUTDOWN] Stopping OAuth server...", flush=True)
            try:
                self.auth._oauth_server.stop()
                print("[SHUTDOWN] OAuth server stopped successfully", flush=True)
            except Exception as e:
                print(f"[SHUTDOWN] Error stopping OAuth server: {e}", flush=True)

        # Debug: Show remaining threads
        print(f"[SHUTDOWN] Remaining threads: {threading.active_count()}", flush=True)
        for thread in threading.enumerate():
            print(f"[SHUTDOWN]   - {thread.name} (daemon={thread.daemon}, alive={thread.is_alive()})", flush=True)

        # Force quit application
        print("[SHUTDOWN] Calling super().closeEvent()...", flush=True)
        super().closeEvent(event)

        # Force quit QApplication
        print("[SHUTDOWN] Calling QApplication.quit()...", flush=True)
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

        print("[SHUTDOWN] Application closed.", flush=True)

        # Ultimate fallback: Force exit after 2 seconds if still running
        import os
        from threading import Timer
        def force_exit():
            print("[SHUTDOWN] Force exit after timeout!", flush=True)
            os._exit(0)

        Timer(2.0, force_exit).start()

