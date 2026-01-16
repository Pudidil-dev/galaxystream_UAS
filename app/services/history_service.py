"""
History Service untuk menyimpan dan mengelola riwayat tontonan.

Service ini menggunakan QSettings untuk penyimpanan persisten.
Data disimpan dalam format JSON array dengan maksimal 100 item.
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QSettings


class HistoryItem:
    """Model untuk satu item history."""

    def __init__(
        self,
        id: str = None,
        source: str = "",
        content_id: str = "",
        title: str = "",
        poster_url: str = "",
        episode_id: str = "",
        episode_title: str = "",
        episode_path: str = "",
        watched_at: str = None,
        duration: int = 0,
        position: int = 0,
        extra: Dict[str, Any] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.source = source
        self.content_id = content_id
        self.title = title
        self.poster_url = poster_url
        self.episode_id = episode_id
        self.episode_title = episode_title
        self.episode_path = episode_path
        self.watched_at = watched_at or datetime.now().isoformat()
        self.duration = duration
        self.position = position
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        """Konversi ke dictionary untuk serialisasi JSON."""
        return {
            "id": self.id,
            "source": self.source,
            "content_id": self.content_id,
            "title": self.title,
            "poster_url": self.poster_url,
            "episode_id": self.episode_id,
            "episode_title": self.episode_title,
            "episode_path": self.episode_path,
            "watched_at": self.watched_at,
            "duration": self.duration,
            "position": self.position,
            "extra": self.extra
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryItem':
        """Buat instance dari dictionary."""
        return cls(
            id=data.get("id"),
            source=data.get("source", ""),
            content_id=data.get("content_id", ""),
            title=data.get("title", ""),
            poster_url=data.get("poster_url", ""),
            episode_id=data.get("episode_id", ""),
            episode_title=data.get("episode_title", ""),
            episode_path=data.get("episode_path", ""),
            watched_at=data.get("watched_at"),
            duration=data.get("duration", 0),
            position=data.get("position", 0),
            extra=data.get("extra", {})
        )


class HistoryService:
    """
    Service untuk mengelola riwayat tontonan.

    Menyimpan data ke QSettings dengan key 'watch_history'.
    Maksimal 100 item untuk mencegah bloat storage.
    """

    MAX_HISTORY_ITEMS = 100
    SETTINGS_KEY = "watch_history"

    def __init__(self):
        """Inisialisasi history service dengan QSettings."""
        self.settings = QSettings("GalaxyStream", "GalaxyStream")
        print("[HISTORY] History service initialized", flush=True)

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history dari QSettings."""
        raw = self.settings.value(self.SETTINGS_KEY, "")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[HISTORY] Error loading history: {e}", flush=True)
            return []

    def _save_history(self, history: List[Dict[str, Any]]) -> bool:
        """Simpan history ke QSettings."""
        try:
            json_str = json.dumps(history)
            self.settings.setValue(self.SETTINGS_KEY, json_str)
            return True
        except (TypeError, ValueError) as e:
            print(f"[HISTORY] Error saving history: {e}", flush=True)
            return False

    def add_history(
        self,
        source: str,
        content_id: str,
        title: str,
        poster_url: str = "",
        episode_id: str = "",
        episode_title: str = "",
        episode_path: str = "",
        duration: int = 0,
        position: int = 0,
        extra: Dict[str, Any] = None
    ) -> HistoryItem:
        """
        Tambahkan item baru ke history.

        Jika konten + episode yang sama sudah ada, akan di-update timestamp-nya.
        History dibatasi maksimal MAX_HISTORY_ITEMS item.

        Args:
            source: Sumber konten (dramabox/netshort/melolo)
            content_id: ID movie/book
            title: Judul konten
            poster_url: URL gambar poster
            episode_id: ID episode
            episode_title: Judul episode
            episode_path: URL stream video
            duration: Durasi video dalam detik
            position: Posisi terakhir dalam ms
            extra: Data tambahan

        Returns:
            HistoryItem yang baru ditambahkan
        """
        history = self._load_history()

        # Cek apakah konten yang sama sudah ada (berdasarkan content_id saja)
        # Jika sudah ada, update episode info bukan append baru
        existing_idx = None
        existing_id = None
        for idx, item in enumerate(history):
            if item.get("content_id") == content_id:
                existing_idx = idx
                existing_id = item.get("id")  # Preserve original history ID
                break

        # Buat item baru (atau update existing)
        new_item = HistoryItem(
            id=existing_id,  # Use existing ID if updating
            source=source,
            content_id=content_id,
            title=title,
            poster_url=poster_url,
            episode_id=episode_id,
            episode_title=episode_title,
            episode_path=episode_path,
            duration=duration,
            position=position,
            extra=extra or {}
        )

        # Jika sudah ada, hapus yang lama (akan di-replace dengan yang baru di atas)
        if existing_idx is not None:
            history.pop(existing_idx)
            print(f"[HISTORY] Updated: {title} - {episode_title}", flush=True)
        else:
            print(f"[HISTORY] Added: {title} - {episode_title}", flush=True)

        # Tambahkan di awal (paling baru di atas)
        history.insert(0, new_item.to_dict())

        # Batasi jumlah item
        if len(history) > self.MAX_HISTORY_ITEMS:
            history = history[:self.MAX_HISTORY_ITEMS]

        # Simpan
        self._save_history(history)

        return new_item

    def update_position(self, content_id: str, episode_id: str, position: int) -> bool:
        """
        Update posisi terakhir tontonan.

        Args:
            content_id: ID movie/book
            episode_id: ID episode
            position: Posisi terakhir dalam ms

        Returns:
            True jika berhasil update
        """
        history = self._load_history()

        for item in history:
            if item.get("content_id") == content_id and item.get("episode_id") == episode_id:
                item["position"] = position
                item["watched_at"] = datetime.now().isoformat()
                self._save_history(history)
                return True

        return False

    def get_history(self, limit: int = 50) -> List[HistoryItem]:
        """
        Ambil daftar history.

        Args:
            limit: Jumlah maksimal item yang diambil

        Returns:
            List of HistoryItem, diurutkan dari yang paling baru
        """
        history = self._load_history()
        items = []
        for data in history[:limit]:
            try:
                items.append(HistoryItem.from_dict(data))
            except Exception as e:
                print(f"[HISTORY] Error parsing item: {e}", flush=True)
        return items

    def get_last_watched(self, content_id: str) -> Optional[HistoryItem]:
        """
        Ambil item history terakhir untuk konten tertentu.

        Args:
            content_id: ID movie/book

        Returns:
            HistoryItem terakhir untuk konten tersebut, atau None
        """
        history = self._load_history()
        for data in history:
            if data.get("content_id") == content_id:
                return HistoryItem.from_dict(data)
        return None

    def delete_item(self, history_id: str) -> bool:
        """
        Hapus satu item history.

        Args:
            history_id: ID item history yang akan dihapus

        Returns:
            True jika berhasil dihapus
        """
        history = self._load_history()
        original_len = len(history)
        history = [item for item in history if item.get("id") != history_id]

        if len(history) < original_len:
            self._save_history(history)
            print(f"[HISTORY] Deleted item: {history_id}", flush=True)
            return True
        return False

    def clear_history(self) -> bool:
        """
        Hapus semua history.

        Returns:
            True jika berhasil
        """
        self._save_history([])
        print("[HISTORY] All history cleared", flush=True)
        return True

    def get_history_count(self) -> int:
        """Dapatkan jumlah item history."""
        return len(self._load_history())
