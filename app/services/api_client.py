import requests
import urllib3
import ssl
import time
from typing import List, Dict, Optional
from app.models.movie import Movie, Episode
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLAdapter(HTTPAdapter):
    """
    Adapter khusus untuk menangani koneksi SSL/TLS dengan pengaturan yang lebih permisif.

    Class ini digunakan untuk mengatasi masalah koneksi SSL dengan server tertentu
    yang mungkin memiliki sertifikat yang tidak valid atau konfigurasi SSL yang ketat.
    """
    def __init__(self, verify_ssl=False, *args, **kwargs):
        """
        Inisialisasi SSLAdapter.

        Args:
            verify_ssl: Boolean untuk mengaktifkan/menonaktifkan verifikasi SSL (default: False)
        """
        self.verify_ssl = verify_ssl
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        """
        Menginisialisasi pool manager dengan konteks SSL yang dikustomisasi.

        Metode ini membuat konteks SSL dengan pengaturan keamanan yang lebih rendah
        untuk memungkinkan koneksi ke server dengan sertifikat yang tidak valid.
        """
        context = create_urllib3_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        if not self.verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        try:
            context.set_ciphers('DEFAULT@SECLEVEL=1')
        except:
            pass
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class APIClient:
    """
    Client untuk berkomunikasi dengan API external (Dramabox, Netshort, Melolo, ShortMax).

    - Dramabox: Menggunakan API dramabox.sansekai.my.id TANPA token
    - Netshort/Melolo/ShortMax: Menggunakan API captain.sapimu.au dengan Bearer token
    - Komik: Menggunakan API Sansekai lama tanpa token
    - Anime: Ditangani terpisah
    """
    # Captain API for Netshort/Melolo/ShortMax - requires Bearer token
    CAPTAIN_BASE_URL = "https://captain.sapimu.au"
    # Dramabox API - NO token required
    DRAMABOX_BASE_URL = "https://dramabox.sansekai.my.id/api/dramabox"
    # Old Sansekai API for Komik - Simple and stable, no token required
    KOMIK_BASE_URL = "https://api.sansekai.my.id/api"

    def __init__(self, verify_ssl=False):
        """
        Inisialisasi APIClient dengan session HTTP dan header.

        Args:
            verify_ssl: Boolean untuk mengaktifkan/menonaktifkan verifikasi SSL (default: False)
        """
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = False

        # Default token for captain.sapimu.au API (Netshort/Melolo/ShortMax)
        self._default_token = "b0cb1c3e8b2ddc08fd24c05e094a33b24625d334b3ca2cca0edf3a08b102b9c9"
        self.captain_token = self._load_token()

        # Base headers (without Authorization - will be added per request)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        })
        self.session.mount("https://", SSLAdapter(verify_ssl=False))
        self.source = "dramabox"
        self.lang = "in"  # Default language Indonesian

        print(f"[API] Dramabox: {self.DRAMABOX_BASE_URL} (no token)")
        print(f"[API] Captain (Netshort/Melolo/ShortMax): {self.CAPTAIN_BASE_URL} (with Bearer token)")
        print(f"[API] Using custom token: {self.captain_token != self._default_token}")
        print(f"[API] API Client initialized successfully")

    def _load_token(self) -> str:
        """Load token dari QSettings, fallback ke default."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("GalaxyStream", "GalaxyStream")
            custom_token = settings.value("captain_token", "")
            if custom_token:
                print(f"[API] Loaded custom token from settings")
                return custom_token
        except Exception as e:
            print(f"[API] Error loading token from settings: {e}")
        return self._default_token

    def reload_token(self):
        """Reload token dari QSettings. Dipanggil setelah token diubah di Profile."""
        old_token = self.captain_token
        self.captain_token = self._load_token()
        if old_token != self.captain_token:
            print(f"[API] Token reloaded and changed")
        else:
            print(f"[API] Token reloaded (no change)")

    def set_source(self, source_type: str):
        """
        Mengubah sumber data API yang akan digunakan.

        Args:
            source_type: Jenis sumber ("dramabox", "netshort", "melolo", "shortmax", "flic", "anime", "komik")
        """
        self.source = source_type.lower()
        print(f"[DEBUG] API Source switched to: {self.source}")

    @property
    def base_url(self):
        """
        Property untuk mendapatkan base URL API berdasarkan source yang aktif.

        Returns:
            String URL dasar API
        """
        if self.source == "dramabox":
            return self.DRAMABOX_BASE_URL
        elif self.source in ["netshort", "melolo"]:
            return self.CAPTAIN_BASE_URL
        elif self.source == "komik":
            return self.KOMIK_BASE_URL
        return self.CAPTAIN_BASE_URL

    def _post(self, endpoint: str, json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> any:
        """
        Metode internal untuk melakukan HTTP POST request.

        Args:
            endpoint: Endpoint API yang akan diakses
            json_data: JSON body untuk request (opsional)
            params: Parameter query untuk request (opsional)

        Returns:
            JSON response dari API atau None jika terjadi error
        """
        # Prepare headers
        headers = {}

        # Route to correct API based on endpoint and source
        if endpoint.startswith("komik/"):
            # Use old Sansekai API for komik (no token)
            url = f"{self.KOMIK_BASE_URL}/{endpoint}"
        elif endpoint.startswith("http"):
            # Full URL provided
            url = endpoint
        elif endpoint.startswith("dramabox/"):
            # Dramabox API - no token required
            # Remove "dramabox/" prefix as it's already in DRAMABOX_BASE_URL
            clean_endpoint = endpoint.replace("dramabox/", "", 1)
            url = f"{self.DRAMABOX_BASE_URL}/{clean_endpoint}"
        elif self.source in ["netshort", "melolo"]:
            # Captain API - requires Bearer token
            url = f"{self.CAPTAIN_BASE_URL}/{endpoint}"
            headers['Authorization'] = f'Bearer {self.captain_token}'
        else:
            # Default to captain API
            url = f"{self.CAPTAIN_BASE_URL}/{endpoint}"

        try:
            print(f"[API POST] {url}")
            if json_data:
                print(f"[API BODY] {json_data}")
            if params:
                print(f"[API PARAMS] {params}")

            response = self.session.post(url, json=json_data, params=params, headers=headers, timeout=20, verify=False)
            response.raise_for_status()

            json_response = response.json()
            print(f"[API RESPONSE] Status: {response.status_code}, Data keys: {list(json_response.keys()) if isinstance(json_response, dict) else 'list'}")

            return json_response
        except Exception as e:
            print(f"[API ERROR] ({endpoint}): {e}")
            return None

    def _get(self, endpoint: str, params: Optional[Dict] = None, max_retries: int = 2) -> any:
        """
        Metode internal untuk melakukan HTTP GET request dengan retry logic.

        Args:
            endpoint: Endpoint API yang akan diakses
            params: Parameter query untuk request (opsional)
            max_retries: Maximum number of retry attempts (default: 2)

        Returns:
            JSON response dari API atau None jika terjadi error
        """
        # Prepare headers
        headers = {}

        # Route to correct API based on endpoint and source
        if endpoint.startswith("komik/"):
            # Use old Sansekai API for komik (no Bearer token)
            url = f"{self.KOMIK_BASE_URL}/{endpoint}"
        elif endpoint.startswith("http"):
            # Full URL provided - check if it needs token
            url = endpoint
            if self.CAPTAIN_BASE_URL in url:
                headers['Authorization'] = f'Bearer {self.captain_token}'
        elif endpoint.startswith("dramabox/"):
            # Dramabox API - NO token required
            # Remove "dramabox/api/" prefix as base URL already includes /api/dramabox
            clean_endpoint = endpoint.replace("dramabox/api/", "", 1)
            url = f"{self.DRAMABOX_BASE_URL}/{clean_endpoint}"
        elif self.source in ["netshort", "melolo", "shortmax"]:
            # Captain API for netshort/melolo/shortmax - requires Bearer token
            url = f"{self.CAPTAIN_BASE_URL}/{endpoint}"
            headers['Authorization'] = f'Bearer {self.captain_token}'
        else:
            # Default fallback
            url = f"{self.CAPTAIN_BASE_URL}/{endpoint}"

        # FIXED: Retry logic dengan exponential backoff
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff: 0.5s, 1s
                    wait_time = 0.5 * (2 ** (attempt - 1))
                    print(f"[API RETRY] Attempt {attempt}/{max_retries} after {wait_time}s wait", flush=True)
                    time.sleep(wait_time)

                print(f"[API REQUEST] {url}")
                if params:
                    print(f"[API PARAMS] {params}")
                if 'Authorization' in headers:
                    print(f"[API AUTH] Using Bearer token")

                # FIXED: Reduced timeout from 30s to 10s untuk faster failure
                # Flic API yang lambat akan fail cepat instead of freeze 30s
                response = self.session.get(url, params=params, headers=headers,
                                           timeout=10,  # ← Reduced from 30s
                                           verify=False)

                print(f"[API RESPONSE] Status: {response.status_code}")

                response.raise_for_status()

                json_data = response.json()
                print(f"[API RESPONSE] Data keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'list'}")

                return json_data

            except requests.exceptions.Timeout:
                print(f"[API ERROR] Request timeout after 10s: {endpoint} (attempt {attempt + 1}/{max_retries + 1})")
                if attempt >= max_retries:
                    print(f"[API ERROR] All retry attempts exhausted for: {endpoint}", flush=True)
                    return None
                # Continue to retry

            except requests.exceptions.ConnectionError as e:
                print(f"[API ERROR] Connection error ({endpoint}): {e}")
                if attempt >= max_retries:
                    return None
                # Continue to retry

            except requests.exceptions.HTTPError as e:
                print(f"[API ERROR] HTTP error ({endpoint}): {e}")
                # Don't retry on HTTP errors (4xx, 5xx) - fail fast
                return None

            except Exception as e:
                print(f"[API ERROR] Unexpected error ({endpoint}): {type(e).__name__}: {e}")
                return None

        return None

    # ==================== SOURCE-SPECIFIC CATEGORIES ====================

    def get_categories(self) -> Dict[str, str]:
        """
        Mendapatkan daftar kategori yang tersedia untuk sumber yang aktif.

        Returns:
            Dictionary berisi nama kategori dan endpoint API-nya
        """
        if self.source == "dramabox":
            return {
                "For You": "dramabox_foryou",
                "New": "dramabox_new",
                "Trending": "dramabox_trending"
            }
        elif self.source == "netshort":
            return {
                "For You": "netshort_foryou",
                "Theaters": "netshort_theaters"
            }
        elif self.source == "melolo":
            return {
                "Bookmall": "melolo_bookmall"
            }
        elif self.source == "komik":
            return {
                "Latest Project": "komik/latest?type=project",
                "Latest Mirror": "komik/latest?type=mirror",
                "Popular": "komik/popular",
                "Manhwa Recommended": "komik/recommended?type=manhwa",
                "Manhua Recommended": "komik/recommended?type=manhua"
            }
        return {}

    # ==================== DRAMABOX NEW API ====================

    def get_dramabox_foryou(self, page: int = 1) -> List[Movie]:
        """Mendapatkan konten For You dari Dramabox."""
        data = self._get("dramabox/api/foryou", params={"lang": self.lang})
        if not data:
            return []

        # Response is array directly, not nested
        items = data if isinstance(data, list) else []
        return self._parse_dramabox_movies(items)

    def get_dramabox_new(self, page: int = 1) -> List[Movie]:
        """Mendapatkan konten terbaru dari Dramabox."""
        data = self._get("dramabox/api/latest", params={"lang": self.lang})
        if not data:
            return []

        items = data if isinstance(data, list) else []
        return self._parse_dramabox_movies(items)

    def get_dramabox_trending(self, page: int = 1) -> List[Movie]:
        """Mendapatkan konten trending dari Dramabox."""
        data = self._get("dramabox/api/trending", params={"lang": self.lang})
        if not data:
            return []

        items = data if isinstance(data, list) else []
        return self._parse_dramabox_movies(items)

    def search_dramabox(self, query: str, page: int = 1) -> List[Movie]:
        """Mencari konten di Dramabox."""
        data = self._get("dramabox/api/search", params={"query": query, "lang": self.lang})
        if not data:
            return []

        items = data if isinstance(data, list) else []
        return self._parse_dramabox_movies(items)

    def get_dramabox_episodes(self, book_id: str) -> List[Episode]:
        """Mendapatkan daftar episode dari Dramabox menggunakan allepisode endpoint."""
        data = self._get(f"dramabox/api/allepisode", params={"bookId": book_id, "lang": self.lang})
        if not data:
            return []

        # allepisode returns array directly, not nested in data.chapterList
        episodes = []
        chapter_list = data if isinstance(data, list) else []

        for chapter in chapter_list:
            chapter_index = chapter.get("chapterIndex", 0)
            chapter_name = chapter.get("chapterName", f"EP {chapter_index + 1}")

            # Extract video URL from cdnList for caching
            video_url = self._extract_video_url_from_cdn(chapter.get("cdnList", []))

            episodes.append(Episode(
                id=str(chapter_index),
                title=chapter_name,
                stream_url=video_url,  # Pre-cache the video URL
                order=chapter_index + 1
            ))

        print(f"[DRAMABOX EPISODES] Found {len(episodes)} episodes for bookId={book_id}")
        return episodes

    def _extract_video_url_from_cdn(self, cdn_list: List[Dict]) -> str:
        """Extract best video URL from cdnList, prioritizing 720p."""
        if not cdn_list:
            return ""

        # Get the default CDN or first one
        default_cdn = None
        for cdn in cdn_list:
            if cdn.get("isDefault") == 1:
                default_cdn = cdn
                break

        if not default_cdn:
            default_cdn = cdn_list[0]

        video_paths = default_cdn.get("videoPathList", [])
        if not video_paths:
            return ""

        # Prioritize 720p
        for video in video_paths:
            if video.get("quality") == 720:
                return video.get("videoPath", "")

        # Fallback to first available quality
        return video_paths[0].get("videoPath", "")

    def get_dramabox_stream(self, book_id: str, chapter_index: int) -> str:
        """
        Mendapatkan URL stream untuk episode Dramabox.

        Menggunakan allepisode endpoint untuk mendapatkan video URL berdasarkan
        chapter_index yang diminta.
        """
        print(f"[DRAMABOX STREAM] Fetching stream for bookId={book_id}, chapterIndex={chapter_index}")

        # Fetch all episodes and find the matching one
        data = self._get(f"dramabox/api/allepisode", params={"bookId": book_id, "lang": self.lang})

        if not data:
            print(f"[DRAMABOX STREAM] No data returned")
            return ""

        chapter_list = data if isinstance(data, list) else []
        print(f"[DRAMABOX STREAM] Found {len(chapter_list)} chapters in response")

        if not chapter_list:
            print(f"[DRAMABOX STREAM] No chapters found")
            return ""

        # Find the chapter with matching chapterIndex
        target_chapter = None
        for chapter in chapter_list:
            if chapter.get("chapterIndex") == chapter_index:
                target_chapter = chapter
                break

        if not target_chapter:
            print(f"[DRAMABOX STREAM] Chapter with index {chapter_index} not found, using first chapter")
            target_chapter = chapter_list[0] if chapter_list else None

        if not target_chapter:
            return ""

        # Extract video URL from the target chapter
        video_url = self._extract_video_url_from_cdn(target_chapter.get("cdnList", []))

        if video_url:
            print(f"[DRAMABOX STREAM] Found video URL for chapter {chapter_index}: {video_url[:100]}...")
        else:
            print(f"[DRAMABOX STREAM] No video URL found for chapter {chapter_index}")

        return video_url

    def _parse_dramabox_movies(self, items: List[Dict]) -> List[Movie]:
        """Parse data Dramabox menjadi Movie objects."""
        movies = []
        for item in items:
            # coverWap untuk home/trending, cover untuk search results
            poster = item.get("coverWap", "") or item.get("cover", "")
            movies.append(Movie(
                id=str(item.get("bookId", "")),
                title=item.get("bookName", "Unknown"),
                poster_url=poster,
                synopsis=item.get("introduction", ""),
                source_type=self.source
            ))
        return movies

    # ==================== NETSHORT NEW API ====================

    def get_netshort_tabs(self) -> List[Dict]:
        """Mendapatkan daftar tag yang tersedia di Netshort."""
        data = self._get("netshort/api/v1/meta/tags")
        if not data or not data.get("success"):
            return []
        return data.get("data", [])

    def get_netshort_home(self, tab_id: str = None, limit: int = 20) -> List[Movie]:
        """Mendapatkan konten home dari Netshort menggunakan /api/v1/explore."""
        data = self._get("netshort/api/v1/explore", params={"offset": 0, "limit": limit})
        if not data or not data.get("success"):
            return []

        # Parse response: data.result[]
        result = data.get("data", {}).get("result", [])
        print(f"[NETSHORT HOME] Found {len(result)} items")

        return self._parse_netshort_movies(result)

    def search_netshort(self, query: str, limit: int = 20) -> List[Movie]:
        """Mencari konten di Netshort menggunakan /api/v1/find."""
        data = self._get("netshort/api/v1/find", params={"q": query, "page": 1, "size": limit})
        if not data or not data.get("success"):
            return []

        # Parse response: data is array directly for search, or data.result[] for explore
        raw_data = data.get("data", [])
        if isinstance(raw_data, list):
            result = raw_data
        else:
            result = raw_data.get("result", [])

        print(f"[NETSHORT SEARCH] Found {len(result)} items")

        return self._parse_netshort_movies(result)

    def get_netshort_episodes(self, short_play_id: str) -> List[Episode]:
        """Mendapatkan daftar episode dari Netshort menggunakan /api/v1/info."""
        data = self._get(f"netshort/api/v1/info/{short_play_id}")
        if not data or not data.get("success"):
            return []

        # Episodes are in data.result[]
        episode_list = data.get("data", {}).get("result", [])
        print(f"[NETSHORT EPISODES] Found {len(episode_list)} episodes")

        episodes = []

        for ep in episode_list:
            episode_no = ep.get("episodeNo", 0)
            video_url = ep.get("videoUrl", "")
            episodes.append(Episode(
                id=str(episode_no),  # Use episodeNo as ID
                title=f"Episode {episode_no}",
                stream_url=video_url,  # Pre-cache video URL
                order=episode_no
            ))

        return episodes

    def get_netshort_stream(self, short_play_id: str, episode_id: str, episode_no: int = 1) -> str:
        """Mendapatkan URL stream untuk episode Netshort menggunakan /api/v1/view."""
        print(f"[NETSHORT STREAM] Fetching stream for shortPlayId={short_play_id}, episodeNo={episode_no}")

        data = self._get(f"netshort/api/v1/view/{short_play_id}/ep/{episode_no}")

        if not data or not data.get("success"):
            print(f"[NETSHORT STREAM] API returned success=false or no data")
            return ""

        # videoUrl is in data.videoUrl
        video_url = data.get("data", {}).get("videoUrl", "")
        if video_url:
            print(f"[NETSHORT STREAM] Found videoUrl: {video_url[:100]}...")
            return video_url

        print(f"[NETSHORT STREAM] No video URL found")
        return ""

    def _parse_netshort_movies(self, items: List[Dict]) -> List[Movie]:
        """Parse data Netshort menjadi Movie objects."""
        import re
        movies = []
        for item in items:
            # Explore API uses 'id', 'name', 'cover'
            # Search API uses 'shortPlayId', 'shortPlayName', 'shortPlayCover'
            # Note: Search API returns id=null, so we need to check for None explicitly
            raw_id = item.get("id")
            movie_id = str(raw_id) if raw_id else str(item.get("shortPlayId", ""))

            raw_name = item.get("name")
            title = raw_name if raw_name else item.get("shortPlayName", "Unknown")
            # Remove HTML tags from title (search results may contain <em> tags)
            title = re.sub(r'<[^>]+>', '', title)

            raw_cover = item.get("cover")
            cover = raw_cover if raw_cover else item.get("shortPlayCover", "")

            # Synopsis bisa dari berbagai field
            synopsis = item.get("introduction", "") or item.get("shotIntroduce", "")

            movies.append(Movie(
                id=movie_id,
                title=title,
                poster_url=cover,
                synopsis=synopsis,
                source_type=self.source
            ))
        return movies

    # ==================== MELOLO NEW SOURCE ====================

    def get_melolo_bookmall(self) -> List[Movie]:
        """Mendapatkan konten dari Melolo Bookmall menggunakan /api/v1/bookmall."""
        data = self._get("melolo/api/v1/bookmall", params={"lang": "id"})
        if not data:
            return []

        # Parse from cell.books[]
        cell = data.get("cell", {})
        books = cell.get("books", [])

        print(f"[MELOLO BOOKMALL] Found {len(books)} books")

        # Parse books to items format
        items = []
        for book in books:
            # Bookmall uses 'thumb_url' for cover, not 'cover'
            cover_url = book.get("thumb_url", "") or book.get("cover", "")
            items.append({
                "book_id": book.get("book_id", ""),
                "title": book.get("book_name", ""),
                "abstract": book.get("abstract", ""),
                "cover": cover_url,  # Use thumb_url as cover
                "author": book.get("author", ""),
                "status": book.get("book_status", "")
            })

        return self._parse_melolo_movies(items)

    def search_melolo(self, query: str) -> List[Movie]:
        """Mencari konten di Melolo menggunakan /api/v1/search."""
        data = self._get("melolo/api/v1/search", params={"query": query, "lang": "id"})
        if not data:
            return []

        items = data.get("items", [])
        return self._parse_melolo_movies(items)

    def get_melolo_series(self, series_id: str) -> Optional[Dict]:
        """Mendapatkan detail series dari Melolo menggunakan /api/v1/series."""
        print(f"[MELOLO SERIES] Fetching series for series_id={series_id}")

        data = self._get(f"melolo/api/v1/series", params={"series_id": series_id, "lang": "id"})

        if not data:
            print(f"[MELOLO SERIES] No data returned")
            return None

        print(f"[MELOLO SERIES] Response keys: {list(data.keys())}")

        return data

    def get_melolo_episodes(self, series_id: str) -> List[Episode]:
        """Mendapatkan daftar episode dari Melolo."""
        print(f"[MELOLO EPISODES] Fetching episodes for series_id={series_id}")

        series_data = self.get_melolo_series(series_id)
        if not series_data:
            print(f"[MELOLO EPISODES] No series data")
            return []

        # Parse episodes from root level 'episodes' array
        episode_list = series_data.get("episodes", [])
        print(f"[MELOLO EPISODES] Found {len(episode_list)} episodes in response")

        episodes = []
        for i, ep in enumerate(episode_list):
            vid = ep.get("vid", "")
            if not vid:
                print(f"[MELOLO EPISODES] Skipping episode {i}: no vid field")
                continue

            episodes.append(Episode(
                id=str(vid),  # vid is used as video_id for streaming
                title=f"Episode {ep.get('index', i+1)}",
                stream_url="",  # Will be fetched separately
                order=ep.get("index", i+1)
            ))

        print(f"[MELOLO EPISODES] Created {len(episodes)} episode objects")
        return episodes

    def get_melolo_stream(self, video_id: str) -> str:
        """Mendapatkan URL stream untuk video Melolo menggunakan /api/v1/video."""
        print(f"[MELOLO STREAM] Fetching stream for videoId={video_id}")

        data = self._get(f"melolo/api/v1/video", params={"video_id": video_id, "lang": "id"})
        if not data:
            print(f"[MELOLO STREAM] No data returned")
            return ""

        # Try main_url first (root level)
        main_url = data.get("main_url", "")
        if main_url:
            print(f"[MELOLO STREAM] Found main_url: {main_url[:100]}...")
            return main_url

        # Try backup_url
        backup_url = data.get("backup_url", "")
        if backup_url:
            print(f"[MELOLO STREAM] Found backup_url: {backup_url[:100]}...")
            return backup_url

        # Try parsed.videos with quality priority (video_3=480p, video_4=720p, etc.)
        parsed = data.get("parsed", {})
        videos = parsed.get("videos", {})

        # Try 720p (video_4), 480p (video_3), 360p (video_2) in order
        for video_key in ["video_4", "video_3", "video_2", "video_1"]:
            if video_key in videos:
                video_main = videos[video_key].get("main_url", "")
                if video_main:
                    quality = videos[video_key].get("definition", "unknown")
                    print(f"[MELOLO STREAM] Found {quality} from parsed.videos: {video_main[:100]}...")
                    return video_main

        print(f"[MELOLO STREAM] No video URL found")
        return ""

    def _parse_melolo_movies(self, items: List[Dict]) -> List[Movie]:
        """Parse data Melolo menjadi Movie objects."""
        movies = []
        for item in items:
            # Melolo uses 'book_id' as the primary ID
            # series_id is only used in /series endpoint response
            book_id = str(item.get("book_id", ""))
            if not book_id:
                print(f"[MELOLO PARSE] Skipping item with no book_id: {item}")
                continue

            title = item.get("title", "") or item.get("book_name", "Unknown")
            cover = item.get("cover", "")
            synopsis = item.get("abstract", "") or item.get("description", "")

            if not cover:
                print(f"[MELOLO PARSE] WARNING: No cover URL for '{title}' (ID: {book_id})")
            else:
                print(f"[MELOLO PARSE] Book '{title[:30]}' has cover: {cover[:80]}...")

            # Note: HEIC images will be converted to JPEG automatically by ImageCache
            movies.append(Movie(
                id=book_id,
                title=title,
                poster_url=cover,
                synopsis=synopsis,
                source_type=self.source
            ))

        print(f"[MELOLO PARSE] Parsed {len(movies)} movies from {len(items)} items")
        return movies

    # ==================== SHORTMAX NEW SOURCE ====================

    def get_shortmax_home(self, lang: str = "en") -> List[Movie]:
        """Mendapatkan konten home dari ShortMax."""
        print(f"[SHORTMAX HOME] Fetching home for lang={lang}")

        data = self._get("shortmax/api/v1/home", params={"lang": lang})
        if not data:
            print(f"[SHORTMAX HOME] No data returned")
            return []

        items = data.get("data", [])
        print(f"[SHORTMAX HOME] Found {len(items)} items")

        return self._parse_shortmax_movies(items)

    def search_shortmax(self, query: str, lang: str = "en") -> List[Movie]:
        """Mencari konten di ShortMax."""
        data = self._get("shortmax/api/v1/search", params={"q": query, "lang": lang})
        if not data:
            return []

        items = data.get("data", [])
        return self._parse_shortmax_movies(items)

    def get_shortmax_episodes(self, movie_id: str, lang: str = "en") -> List[Episode]:
        """Mendapatkan daftar episode dari ShortMax."""
        print(f"[SHORTMAX EPISODES] Fetching episodes for id={movie_id}, lang={lang}")

        # Use 'id' NOT 'code' for episodes endpoint!
        data = self._get(f"shortmax/api/v1/episodes/{movie_id}", params={"lang": lang})
        if not data:
            print(f"[SHORTMAX EPISODES] No data returned")
            return []

        episode_list = data.get("data", [])
        print(f"[SHORTMAX EPISODES] Found {len(episode_list)} episodes")

        episodes = []
        for ep in episode_list:
            episodes.append(Episode(
                id=str(ep.get("id", "")),
                title=f"Episode {ep.get('episode', '')}",
                stream_url="",
                order=ep.get("episode", 0)
            ))

        return episodes

    def get_shortmax_stream(self, movie_id: str, episode_no: int, lang: str = "en") -> str:
        """
        Mendapatkan URL stream untuk episode ShortMax.

        IMPORTANT: ShortMax videos are AES-128-CBC encrypted.
        The returned HLS URL points to encrypted .ts segments that need client-side decryption.
        Decryption should be handled in the video player using:
        - Method: AES-128-CBC
        - IV: 'shortmax00000000' (fixed)
        - Key: Embedded in each .ts file header
        """
        print(f"[SHORTMAX STREAM] Fetching stream for id={movie_id}, episodeNo={episode_no}, lang={lang}")

        # Use 'id' NOT 'code' for play endpoint!
        data = self._get(f"shortmax/api/v1/play/{movie_id}", params={"lang": lang, "ep": episode_no})
        if not data:
            print(f"[SHORTMAX STREAM] No data returned")
            return ""

        # Check if request was successful
        if not data.get("data"):
            print(f"[SHORTMAX STREAM] No data field in response")
            return ""

        video_data = data.get("data", {}).get("video", {})
        print(f"[SHORTMAX STREAM] Available qualities: {list(video_data.keys())}")

        # Prioritize 720p
        if video_data.get("video_720"):
            url = video_data.get("video_720")
            print(f"[SHORTMAX STREAM] Selected 720p (ENCRYPTED): {url[:100]}...")
            return url
        elif video_data.get("video_1080"):
            url = video_data.get("video_1080")
            print(f"[SHORTMAX STREAM] Selected 1080p (ENCRYPTED): {url[:100]}...")
            return url
        elif video_data.get("video_480"):
            url = video_data.get("video_480")
            print(f"[SHORTMAX STREAM] Selected 480p (ENCRYPTED): {url[:100]}...")
            return url

        print(f"[SHORTMAX STREAM] No video URL found")
        return ""

    def _parse_shortmax_movies(self, items: List[Dict]) -> List[Movie]:
        """Parse data ShortMax menjadi Movie objects."""
        movies = []
        for item in items:
            # ShortMax home/search returns both 'id' and 'code'
            # Use 'id' for episodes endpoint (NOT code!)
            movie_id = str(item.get("id", "") or item.get("code", ""))

            movies.append(Movie(
                id=movie_id,
                title=item.get("name", "Unknown"),
                poster_url=item.get("cover", ""),
                synopsis=item.get("summary", ""),
                source_type=self.source
            ))
        return movies

    # ==================== FLIC/FLICKREELS NEW SOURCE ====================

    def get_flic_foryou(self, page: int = 1, lang: str = "in") -> List[Movie]:
        """Mendapatkan konten For You dari Flic."""
        data = self._get("flickreels/api/v1/for-you", params={"lang": lang, "page": page})
        if not data or data.get("status_code") != 1:
            return []

        # For You response: data.list[]
        data_obj = data.get("data", {})
        items = data_obj.get("list", []) if isinstance(data_obj, dict) else []

        print(f"[FLIC FORYOU] Found {len(items)} items")

        return self._parse_flic_movies(items)

    def get_flic_hotrank(self, page: int = 1, lang: str = "in") -> List[Movie]:
        """Mendapatkan konten Hot Rank dari Flic."""
        data = self._get("flickreels/api/v1/hot-rank", params={"lang": lang, "page": page})
        if not data or data.get("status_code") != 1:
            return []

        # Hot rank response has nested structure: data[].data[]
        rank_groups = data.get("data", [])
        all_items = []
        for group in rank_groups:
            if isinstance(group, dict):
                items = group.get("data", [])
                all_items.extend(items)

        print(f"[FLIC HOTRANK] Found {len(all_items)} items from {len(rank_groups)} rank groups")

        return self._parse_flic_movies(all_items)

    def search_flic(self, query: str, lang: str = "in") -> List[Movie]:
        """Mencari konten di Flic."""
        data = self._get("flickreels/api/v1/search", params={"lang": lang, "q": query})
        if not data or data.get("status_code") != 1:
            return []

        items = data.get("data", [])
        return self._parse_flic_movies(items)

    def get_flic_episodes(self, playlet_id: str, lang: str = "in") -> List[Episode]:
        """Mendapatkan daftar episode dari Flic."""
        data = self._get(f"flickreels/api/v1/chapters/{playlet_id}", params={"lang": lang})
        if not data or data.get("status_code") != 1:
            return []

        # Episodes are in data.list[]
        data_obj = data.get("data", {})
        chapter_list = data_obj.get("list", []) if isinstance(data_obj, dict) else []

        print(f"[FLIC EPISODES] Found {len(chapter_list)} chapters")

        episodes = []
        for chapter in chapter_list:
            chapter_num = chapter.get("chapter_num", 0)
            chapter_id = str(chapter.get("chapter_id", ""))

            # IMPORTANT: Flic stream endpoint uses chapter_num, not chapter_id
            # So we use chapter_num as the Episode.id
            episodes.append(Episode(
                id=str(chapter_num),  # Use chapter_num for stream endpoint
                title=f"Episode {chapter_num}",
                stream_url="",
                order=chapter_num,
                duration=chapter_id  # Store chapter_id here for reference
            ))

        print(f"[FLIC EPISODES] Created {len(episodes)} episodes using chapter_num as ID")
        return episodes

    def get_flic_stream(self, playlet_id: str, chapter_num: str, lang: str = "in") -> str:
        """
        Mendapatkan URL stream untuk episode Flic.

        IMPORTANT: Parameter chapter_num adalah chapter_num (bukan chapter_id)
        karena endpoint Flic stream menggunakan chapter_num dalam URL.
        """
        print(f"[FLIC STREAM] Fetching stream for playletId={playlet_id}, chapterNum={chapter_num}")

        # Try stream endpoint first - uses chapter_num in URL
        data = self._get(f"flickreels/api/v1/stream/{playlet_id}/{chapter_num}", params={"lang": lang})

        if not data:
            print(f"[FLIC STREAM] No data from stream endpoint")
        else:
            status_code = data.get("status_code")
            print(f"[FLIC STREAM] Stream response status_code: {status_code}")
            print(f"[FLIC STREAM] Stream response keys: {list(data.keys())}")

            if status_code == 1:
                # Stream endpoint returns data.hls_url
                data_field = data.get("data")

                if data_field is None:
                    print(f"[FLIC STREAM] ERROR: status_code=1 but 'data' field is None!")
                elif not isinstance(data_field, dict):
                    print(f"[FLIC STREAM] ERROR: 'data' field is not a dict, type: {type(data_field)}")
                else:
                    print(f"[FLIC STREAM] data field keys: {list(data_field.keys())}")
                    hls_url = data_field.get("hls_url", "")

                    if hls_url:
                        print(f"[FLIC STREAM] SUCCESS! Found hls_url: {hls_url[:100]}...")
                        return hls_url
                    else:
                        print(f"[FLIC STREAM] data field exists but hls_url is empty")
            else:
                print(f"[FLIC STREAM] Stream endpoint failed with status_code: {status_code}")
                if data.get("msg"):
                    print(f"[FLIC STREAM] Error message: {data.get('msg')}")

        # Fallback to download endpoint v2
        print(f"[FLIC STREAM] Trying download endpoint as fallback...")
        data = self._get(f"flickreels/api/v2/download/{playlet_id}/{chapter_num}", params={"lang": lang})

        if not data:
            print(f"[FLIC STREAM] No data from download endpoint")
        else:
            print(f"[FLIC STREAM] Download response status_code: {data.get('status_code')}")

            if data.get("status_code") == 1:
                # Download endpoint returns data.list[0].down_url
                data_field = data.get("data", {})
                download_list = data_field.get("list", [])

                print(f"[FLIC STREAM] Download list length: {len(download_list) if isinstance(download_list, list) else 'not a list'}")

                if download_list and len(download_list) > 0:
                    down_url = download_list[0].get("down_url", "")
                    if down_url:
                        print(f"[FLIC STREAM] SUCCESS! Found down_url: {down_url[:100]}...")
                        return down_url

        print(f"[FLIC STREAM] FAILED: No video URL found from both endpoints")
        return ""

    def _parse_flic_movies(self, items: List[Dict]) -> List[Movie]:
        """Parse data Flic menjadi Movie objects."""
        movies = []
        for item in items:
            # Handle different field names from different endpoints
            playlet_id = str(item.get("playlet_id", ""))
            title = item.get("playlet_title", "") or item.get("title", "") or "Unknown"
            cover = item.get("cover", "")
            synopsis = item.get("introduce", "")

            movies.append(Movie(
                id=playlet_id,
                title=title,
                poster_url=cover,
                synopsis=synopsis,
                source_type=self.source
            ))
        return movies

    # ==================== UNIFIED INTERFACE METHODS ====================

    def get_foryou(self) -> List[Movie]:
        """Mendapatkan daftar konten rekomendasi utama (For You)."""
        if self.source == "dramabox":
            return self.get_dramabox_foryou()
        elif self.source == "netshort":
            return self.get_netshort_home()
        elif self.source == "melolo":
            return self.get_melolo_bookmall()
        elif self.source == "komik":
            data = self._get("komik/latest", params={"type": "project"})
            return self._parse_movies(data)
        return []

    def get_trending(self) -> List[Movie]:
        """Mendapatkan daftar konten yang sedang trending/populer."""
        if self.source == "dramabox":
            return self.get_dramabox_trending()
        elif self.source == "netshort":
            return self.get_netshort_home()
        elif self.source == "komik":
            data = self._get("komik/popular")
            return self._parse_movies(data)
        return []

    def get_latest(self) -> List[Movie]:
        """Mendapatkan daftar konten terbaru yang dirilis."""
        if self.source == "dramabox":
            return self.get_dramabox_new()
        elif self.source == "netshort":
            return self.get_netshort_home()
        elif self.source == "komik":
            data = self._get("komik/latest", params={"type": "project"})
            return self._parse_movies(data)
        return []

    def get_by_category(self, endpoint: str) -> List[Movie]:
        """
        Mengambil daftar film berdasarkan endpoint kategori tertentu.

        Args:
            endpoint: Endpoint API untuk kategori yang diinginkan

        Returns:
            List objek Movie dari kategori tersebut
        """
        # Handle custom category endpoints
        if endpoint == "dramabox_foryou":
            return self.get_dramabox_foryou()
        elif endpoint == "dramabox_new":
            return self.get_dramabox_new()
        elif endpoint == "dramabox_trending":
            return self.get_dramabox_trending()
        elif endpoint == "netshort_foryou":
            return self.get_netshort_home()
        elif endpoint == "netshort_theaters":
            return self.get_netshort_home()
        elif endpoint == "melolo_search":
            return []  # Requires search query
        elif endpoint == "melolo_bookmall":
            return self.get_melolo_bookmall()
        else:
            # Fallback for komik endpoints
            data = self._get(endpoint)
            return self._parse_movies(data)

    def search(self, query: str) -> List[Movie]:
        """
        Mencari konten berdasarkan query di sumber yang aktif.

        Args:
            query: Kata kunci pencarian

        Returns:
            List objek Movie yang sesuai dengan pencarian
        """
        if self.source == "dramabox":
            return self.search_dramabox(query)
        elif self.source == "netshort":
            return self.search_netshort(query)
        elif self.source == "melolo":
            return self.search_melolo(query)
        elif self.source == "komik":
            data = self._get("komik/search", params={"query": query})
            return self._parse_movies(data)
        return []

    def get_detail(self, book_id: str) -> Optional[Movie]:
        """
        Mendapatkan detail lengkap dari sebuah konten berdasarkan ID.

        Args:
            book_id: ID unik dari konten (or series_id for Melolo)

        Returns:
            Objek Movie dengan informasi detail atau None jika tidak ditemukan
        """
        if self.source == "dramabox":
            # For dramabox, we can use search or just return basic info
            # since detail is included in list responses
            return Movie(
                id=book_id,
                title="",
                poster_url="",
                synopsis="",
                source_type=self.source
            )
        elif self.source == "melolo":
            series_data = self.get_melolo_series(book_id)
            if series_data:
                series_info = series_data.get("series", {})
                return Movie(
                    id=book_id,
                    title=series_info.get("title", ""),
                    poster_url=series_info.get("cover", ""),
                    synopsis=series_info.get("abstract", "") or series_info.get("description", ""),
                    source_type=self.source
                )
        elif self.source == "komik":
            params = {"manga_id": book_id}
            data = self._get("komik/detail", params=params)
            if data:
                item = data.get("data", data) if isinstance(data, dict) else data
                return Movie(
                    id=book_id,
                    title=self._extract_title(item),
                    poster_url=self._extract_poster_url(item),
                    synopsis=item.get("synopsis", "") or item.get("description", ""),
                    source_type=self.source
                )

        return None

    def get_episodes(self, book_id: str) -> List[Episode]:
        """
        Mendapatkan daftar episode/chapter dari sebuah konten.

        Args:
            book_id: ID unik dari konten

        Returns:
            List objek Episode yang tersedia
        """
        if self.source == "dramabox":
            return self.get_dramabox_episodes(book_id)
        elif self.source == "netshort":
            return self.get_netshort_episodes(book_id)
        elif self.source == "melolo":
            return self.get_melolo_episodes(book_id)
        elif self.source == "komik":
            return self._get_chapters(book_id)

        return []

    def get_stream_url(self, episode_id: str, book_id: str = None, episode_no: int = 1) -> str:
        """
        Mendapatkan URL streaming untuk episode tertentu.

        Args:
            episode_id: ID episode (or video_id for Melolo)
            book_id: ID buku/series (required for some sources)
            episode_no: Nomor episode (for some sources)

        Returns:
            URL streaming atau string kosong jika tidak tersedia
        """
        if not episode_id:
            return ""

        if self.source == "dramabox" and book_id:
            return self.get_dramabox_stream(book_id, int(episode_id))
        elif self.source == "netshort" and book_id:
            return self.get_netshort_stream(book_id, episode_id, episode_no)
        elif self.source == "melolo":
            # Melolo uses video_id directly from episode_id
            return self.get_melolo_stream(episode_id)

        # Fallback: return episode_id as URL (for old API compatibility)
        return episode_id

    # ==================== KOMIK METHODS (Old API - Unchanged) ====================

    def get_comic_images(self, chapter_id: str) -> List[str]:
        """
        Mendapatkan daftar URL gambar untuk chapter komik tertentu.

        Args:
            chapter_id: ID chapter komik

        Returns:
            List URL gambar untuk setiap halaman chapter
        """
        data = self._get("komik/getimage", params={"chapter_id": chapter_id})
        if not data:
            return []

        root = data.get("data", data)
        if isinstance(root, dict):
            ch_data = root.get("chapter", root)
            if isinstance(ch_data, dict):
                return ch_data.get("data", [])
        return []

    def _get_chapters(self, book_id: str) -> List[Episode]:
        """
        Helper method untuk mendapatkan chapter list untuk komik.

        Args:
            book_id: ID manga/komik

        Returns:
            List objek Episode untuk setiap chapter
        """
        data = self._get("komik/chapterlist", params={"manga_id": book_id})
        chapters = []
        raw_list = data.get("data", []) if isinstance(data, dict) else []
        for i, item in enumerate(raw_list):
            title = item.get("chapter_name") or f"Chapter {item.get('chapter_number', i+1)}"
            chapters.append(Episode(
                id=str(item.get("chapter_id")),
                title=title,
                stream_url="",
                order=i + 1
            ))
        return list(reversed(chapters))

    def _extract_title(self, item: Dict) -> str:
        """
        Mengekstrak judul dari data item dengan mencoba berbagai kemungkinan key.

        Args:
            item: Dictionary data item

        Returns:
            Judul konten atau "Unknown" jika tidak ditemukan
        """
        keys = ["shortPlayName", "book_name", "judul", "title", "bookName", "name"]
        for k in keys:
            if item.get(k): return item.get(k)
        return "Unknown"

    def _extract_poster_url(self, item: Dict) -> str:
        """
        Mengekstrak URL poster dari data item dengan mencoba berbagai kemungkinan key.

        Args:
            item: Dictionary data item

        Returns:
            URL poster atau string kosong jika tidak ditemukan
        """
        keys = ["thumb_url", "cover", "cover_image_url", "shortPlayCover", "cover_portrait_url", "coverWap", "image"]
        for k in keys:
            val = item.get(k)
            if isinstance(val, str) and val.startswith("http"): return val
        return ""

    def _parse_movies(self, data: any) -> List[Movie]:
        """
        Mem-parsing data response API menjadi list objek Movie.
        Used for komik and fallback scenarios.

        Args:
            data: Data response dari API (bisa berupa list atau dict)

        Returns:
            List objek Movie yang sudah di-parse
        """
        movies = []
        raw_list = []

        if not data:
            return movies

        # Handle different response formats
        if isinstance(data, list):
            raw_list = data
        elif isinstance(data, dict):
            # Try different possible keys for the list
            raw_list = data.get("contentInfos") or data.get("books") or data.get("data") or []

        if not isinstance(raw_list, list):
            return []

        for item in raw_list:
            # Extract ID - try multiple possible keys
            m_id = str(item.get("shortPlayId") or item.get("book_id") or item.get("url") or item.get("manga_id") or item.get("bookId") or item.get("id") or "")

            if not m_id or m_id == "None":
                continue

            movies.append(Movie(
                id=m_id,
                title=self._extract_title(item),
                poster_url=self._extract_poster_url(item),
                source_type=self.source
            ))

        return movies

    # ==================== KOMIK-SPECIFIC METHODS ====================

    def get_komik_latest(self, page: int = 1, type: str = "project") -> List[Movie]:
        """Mendapatkan daftar komik terbaru."""
        if self.source != "komik":
            return []

        data = self._get("komik/latest", params={"type": type})
        return self._parse_movies(data)

    def get_komik_popular(self, page: int = 1) -> List[Movie]:
        """Mendapatkan daftar komik populer."""
        if self.source != "komik":
            return []

        data = self._get("komik/popular")
        return self._parse_movies(data)

    def search_komik(self, query: str) -> List[Movie]:
        """Mencari komik berdasarkan query."""
        if self.source != "komik":
            return []

        data = self._get("komik/search", params={"query": query})
        return self._parse_movies(data)

    def get_komik_detail(self, manga_id: str) -> Optional[Movie]:
        """Mendapatkan detail komik."""
        if self.source != "komik":
            return None

        data = self._get("komik/detail", params={"manga_id": manga_id})

        if not data:
            return None

        # Parse komik detail
        item = data.get("data", data) if isinstance(data, dict) else data
        return Movie(
            id=manga_id,
            title=self._extract_title(item),
            poster_url=self._extract_poster_url(item),
            synopsis=item.get("synopsis", "") or item.get("description", ""),
            source_type=self.source
        )

    def get_komik_chapters(self, manga_id: str) -> List[Episode]:
        """Mendapatkan daftar chapter untuk komik tertentu."""
        return self._get_chapters(manga_id)

    def get_komik_images(self, chapter_id: str) -> List[str]:
        """Mendapatkan daftar URL gambar untuk chapter tertentu."""
        return self.get_comic_images(chapter_id)
