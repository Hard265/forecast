from dataclasses import dataclass
from datetime import datetime
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True, slots=True)
class CacheRecord:
    key: str
    payload: bytes
    created_at: datetime
    expires_at: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at
