"""
Anime API Client - Client untuk berkomunikasi dengan wajik-anime-api lokal.

Menghandle request ke server Node lokal (Otakudesu & Kuramanime) dan
memetakan data ke model Movie/Episode untuk kompatibilitas dengan UI yang ada.
"""
import requests
from typing import List, Dict, Optional
from app.models.movie import Movie, Episode


class AnimeClient:
    """
    Client untuk berkomunikasi dengan wajik-anime-api lokal.

    Mendukung dua sumber anime:
    - Otakudesu: Ongoing, Completed, Search, Anime Detail, Episode, Server
    - Kuramanime: Ongoing, Completed, Search, Episode
    """
    BASE_URL = "http://127.0.0.1:3001"

    def __init__(self):
        """Inisialisasi AnimeClient dengan session HTTP."""
        print("[ANIME CLIENT] __init__ called - Creating AnimeClient", flush=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        print(f"[ANIME CLIENT] Base URL: {self.BASE_URL}", flush=True)
        print("[ANIME CLIENT] AnimeClient initialized successfully", flush=True)

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> any:
        """
        Metode internal untuk melakukan HTTP GET request.

        Args:
            endpoint: Endpoint API yang akan diakses
            params: Parameter query untuk request (opsional)

        Returns:
            JSON response dari API atau None jika terjadi error
        """
        url = f"{self.BASE_URL}/{endpoint}"
        print(f"[ANIME CLIENT] GET request to: {url}", flush=True)
        if params:
            print(f"[ANIME CLIENT] Params: {params}", flush=True)

        try:
            # Reduced timeout from 15 to 10 seconds
            response = self.session.get(url, params=params, timeout=10)
            print(f"[ANIME CLIENT] Response status: {response.status_code}", flush=True)
            response.raise_for_status()
            json_data = response.json()
            print(f"[ANIME CLIENT] Response received, type: {type(json_data)}", flush=True)
            return json_data
        except requests.exceptions.Timeout:
            print(f"[ANIME CLIENT] Timeout error ({endpoint}) - Request took too long", flush=True)
            return None
        except requests.exceptions.ConnectionError:
            print(f"[ANIME CLIENT] Connection error ({endpoint}) - API server may be down", flush=True)
            return None
        except Exception as e:
            print(f"[ANIME CLIENT] Error ({endpoint}): {e}", flush=True)
            import traceback
            traceback.print_exc()
            return None

    # ==================== OTAKUDESU ====================

    def get_otakudesu_ongoing(self, page: int = 1) -> List[Movie]:
        """
        Mendapatkan daftar anime ongoing dari Otakudesu.

        Args:
            page: Nomor halaman untuk pagination

        Returns:
            List objek Movie yang sedang ongoing
        """
        data = self._get("otakudesu/ongoing", params={"page": page})
        return self._parse_anime_list(data, source="otakudesu")

    def get_otakudesu_completed(self, page: int = 1) -> List[Movie]:
        """
        Mendapatkan daftar anime completed dari Otakudesu.

        Args:
            page: Nomor halaman untuk pagination

        Returns:
            List objek Movie yang sudah completed
        """
        data = self._get("otakudesu/completed", params={"page": page})
        return self._parse_anime_list(data, source="otakudesu")

    def search_otakudesu(self, query: str) -> List[Movie]:
        """
        Mencari anime di Otakudesu.

        Args:
            query: Kata kunci pencarian

        Returns:
            List objek Movie hasil pencarian
        """
        data = self._get("otakudesu/search", params={"q": query})
        return self._parse_anime_list(data, source="otakudesu")

    def get_otakudesu_anime_detail(self, anime_id: str) -> Dict:
        """
        Mendapatkan detail anime dari Otakudesu beserta episode list.

        Args:
            anime_id: ID anime dari Otakudesu

        Returns:
            Dictionary berisi detail anime dan episode list
        """
        data = self._get(f"otakudesu/anime/{anime_id}")
        if not data:
            print(f"[ANIME CLIENT] get_otakudesu_anime_detail: No data received", flush=True)
            return {"movie": None, "episodes": []}

        # Response structure: {"statusCode": 200, "data": {"details": {...}}}
        if isinstance(data, dict) and "data" in data:
            details = data.get("data", {}).get("details", {})
        else:
            details = data

        print(f"[ANIME CLIENT] Details keys: {list(details.keys())}", flush=True)

        # Parse anime detail
        title = details.get("title", "Unknown")
        poster = details.get("poster", "")
        synopsis_data = details.get("synopsis", {})

        # Synopsis might be in paragraphList
        synopsis = ""
        if isinstance(synopsis_data, dict):
            paragraphs = synopsis_data.get("paragraphList", [])
            synopsis = " ".join(paragraphs) if paragraphs else ""
        elif isinstance(synopsis_data, str):
            synopsis = synopsis_data

        movie = Movie(
            id=anime_id,
            title=title,
            poster_url=poster,
            synopsis=synopsis,
            source_type="otakudesu"
        )

        # Parse episodes from episodeList
        episodes = []
        episode_list = details.get("episodeList", [])
        print(f"[ANIME CLIENT] Found {len(episode_list)} episodes", flush=True)

        for i, ep in enumerate(episode_list):
            ep_id = ep.get("episodeId", "")
            ep_title = ep.get("title", f"Episode {i+1}")

            episodes.append(Episode(
                id=ep_id,
                title=f"Episode {ep_title}",
                stream_url=ep_id,  # Store episode_id in stream_url for later fetching
                order=i + 1
            ))

        print(f"[ANIME CLIENT] Created {len(episodes)} episode objects", flush=True)

        return {"movie": movie, "episodes": episodes}

    def get_otakudesu_episode_servers(self, episode_id: str) -> List[Dict]:
        """
        Mendapatkan daftar server untuk episode tertentu di Otakudesu.

        Args:
            episode_id: ID episode dari Otakudesu

        Returns:
            List dictionary berisi info server (serverId, title, quality)
        """
        data = self._get(f"otakudesu/episode/{episode_id}")
        if not data:
            print(f"[ANIME CLIENT] get_otakudesu_episode_servers: No data received", flush=True)
            return []

        # Response structure: {"statusCode": 200, "data": {"details": {"server": {...}}}}
        if isinstance(data, dict) and "data" in data:
            details = data.get("data", {}).get("details", {})
        else:
            details = data

        server_data = details.get("server", {})
        quality_list = server_data.get("qualityList", [])

        print(f"[ANIME CLIENT] Found {len(quality_list)} quality options", flush=True)

        # Flatten server list from all qualities
        servers = []
        for quality in quality_list:
            quality_name = quality.get("title", "").strip()
            server_list = quality.get("serverList", [])

            for server in server_list:
                servers.append({
                    "id": server.get("serverId", ""),
                    "name": server.get("title", "Unknown"),
                    "quality": quality_name
                })

        print(f"[ANIME CLIENT] Total servers: {len(servers)}", flush=True)
        return servers

    def get_otakudesu_server_url(self, server_id: str) -> str:
        """
        Resolve URL streaming dari server ID.

        Args:
            server_id: ID server dari Otakudesu

        Returns:
            URL streaming atau string kosong jika gagal
        """
        data = self._get(f"otakudesu/server/{server_id}")
        if not data:
            print(f"[ANIME CLIENT] get_otakudesu_server_url: No data received", flush=True)
            return ""

        # Response structure: {"statusCode": 200, "data": {"details": {"url": "..."}}}
        if isinstance(data, dict) and "data" in data:
            details = data.get("data", {}).get("details", {})
            url = details.get("url", "")
        else:
            url = data.get("url", "")

        print(f"[ANIME CLIENT] Resolved server URL: {url[:80]}...", flush=True)
        return url

    # ==================== KURAMANIME ====================

    def get_kuramanime_ongoing(self, page: int = 1) -> List[Movie]:
        """
        Mendapatkan daftar anime ongoing dari Kuramanime.

        Args:
            page: Nomor halaman untuk pagination

        Returns:
            List objek Movie yang sedang ongoing
        """
        data = self._get("kuramanime/anime", params={"status": "ongoing", "page": page})
        return self._parse_anime_list(data, source="kuramanime")

    def get_kuramanime_completed(self, page: int = 1) -> List[Movie]:
        """
        Mendapatkan daftar anime completed dari Kuramanime.

        Args:
            page: Nomor halaman untuk pagination

        Returns:
            List objek Movie yang sudah completed
        """
        data = self._get("kuramanime/anime", params={"status": "completed", "page": page})
        return self._parse_anime_list(data, source="kuramanime")

    def search_kuramanime(self, query: str) -> List[Movie]:
        """
        Mencari anime di Kuramanime.

        Args:
            query: Kata kunci pencarian

        Returns:
            List objek Movie hasil pencarian
        """
        data = self._get("kuramanime/anime", params={"search": query})
        return self._parse_anime_list(data, source="kuramanime")

    def get_kuramanime_episode_url(self, anime_id: str, anime_slug: str, episode_id: str) -> str:
        """
        Mendapatkan URL streaming untuk episode Kuramanime.

        Args:
            anime_id: ID anime dari Kuramanime
            anime_slug: Slug anime dari Kuramanime
            episode_id: ID episode dari Kuramanime

        Returns:
            URL streaming atau string kosong jika gagal
        """
        data = self._get(f"kuramanime/episode/{anime_id}/{anime_slug}/{episode_id}")
        if not data:
            return ""

        return data.get("url", "")

    # ==================== HELPER METHODS ====================

    def _parse_anime_list(self, data: any, source: str) -> List[Movie]:
        """
        Mem-parsing data response API menjadi list objek Movie.

        Args:
            data: Data response dari API
            source: Nama source (otakudesu/kuramanime)

        Returns:
            List objek Movie yang sudah di-parse
        """
        movies = []

        if not data:
            print(f"[ANIME CLIENT] _parse_anime_list: data is None or empty", flush=True)
            return movies

        print(f"[ANIME CLIENT] _parse_anime_list: data type = {type(data)}", flush=True)

        # Handle different response structures
        anime_list = []
        if isinstance(data, dict):
            print(f"[ANIME CLIENT] data keys: {list(data.keys())}", flush=True)
            # Check for nested data structure from wajik-anime-api
            if "data" in data and isinstance(data["data"], dict):
                print(f"[ANIME CLIENT] Found nested data dict, keys: {list(data['data'].keys())}", flush=True)
                anime_list = (
                    data["data"].get("animeList", []) or
                    data["data"].get("anime", []) or
                    data["data"].get("results", [])
                )
            else:
                # Fallback to direct data access
                anime_list = data.get("data", []) or data.get("anime", []) or data.get("results", [])
        elif isinstance(data, list):
            anime_list = data

        print(f"[ANIME CLIENT] anime_list length: {len(anime_list)}", flush=True)

        for i, item in enumerate(anime_list):
            if not isinstance(item, dict):
                print(f"[ANIME CLIENT] Item {i} is not a dict, skipping", flush=True)
                continue

            # Extract ID based on source
            anime_id = ""
            if source == "otakudesu":
                anime_id = item.get("id", "") or item.get("animeId", "")
            elif source == "kuramanime":
                anime_id = item.get("id", "") or item.get("animeId", "")

            if not anime_id:
                print(f"[ANIME CLIENT] Item {i} has no ID, skipping. Keys: {list(item.keys())}", flush=True)
                continue

            # Extract title
            title = item.get("title", "") or item.get("name", "Unknown")

            # Extract poster
            poster = item.get("poster", "") or item.get("image", "") or item.get("thumbnail", "")

            print(f"[ANIME CLIENT] Parsed anime #{i+1}: id={anime_id}, title={title}, poster={poster[:50] if poster else 'None'}...", flush=True)

            # Store additional info for Kuramanime
            additional_data = {}
            if source == "kuramanime" and "episodes" in item:
                # Store episode list for kuramanime ongoing
                additional_data["kuramanime_episodes"] = item.get("episodes", [])
                additional_data["slug"] = item.get("slug", "")

            movie = Movie(
                id=anime_id,
                title=title,
                poster_url=poster,
                synopsis=item.get("synopsis", "") or item.get("description", ""),
                source_type=source
            )

            # Store additional data in a way that can be retrieved later
            # Using the genres field as a workaround to store metadata
            if additional_data:
                movie.genres = [f"__metadata__:{key}:{value}" for key, value in additional_data.items()]

            movies.append(movie)

        print(f"[ANIME CLIENT] _parse_anime_list: returning {len(movies)} movies", flush=True)
        return movies
