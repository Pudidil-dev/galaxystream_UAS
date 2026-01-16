from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Episode:
    """
    Model data untuk merepresentasikan episode dari sebuah film/drama/anime.

    Attributes:
        id: Identifikasi unik untuk episode
        title: Judul episode
        stream_url: URL untuk streaming atau membaca episode
        order: Urutan episode (nomor episode)
        duration: Durasi episode (format string, opsional)
    """
    id: str
    title: str
    stream_url: str
    order: int
    duration: str = ""

@dataclass
class Movie:
    """
    Model data untuk merepresentasikan film/drama/anime.

    Attributes:
        id: Identifikasi unik untuk film/drama/anime
        title: Judul film/drama/anime
        poster_url: URL gambar poster
        synopsis: Sinopsis atau deskripsi cerita
        rating: Rating atau nilai (0.0 - 10.0)
        year: Tahun rilis
        source_type: Jenis sumber data (default: "dramabox")
        genres: Daftar genre yang terkait
        episodes: Daftar episode yang tersedia
        total_chapters: Total jumlah chapter/episode yang tersedia
    """
    id: str
    title: str
    poster_url: str
    synopsis: str = ""
    rating: float = 0.0
    year: str = ""
    source_type: str = "dramabox" # Default to dramabox
    genres: List[str] = field(default_factory=list)
    episodes: List[Episode] = field(default_factory=list)
    total_chapters: int = 0
