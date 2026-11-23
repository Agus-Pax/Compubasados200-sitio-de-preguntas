from datetime import UTC, datetime


def utcnow_naive() -> datetime:
    """UTC sin tzinfo: es como SQLite/Postgres guardan los DateTime sin zona."""
    return datetime.now(UTC).replace(tzinfo=None)


def a_utc_naive(dt: datetime) -> datetime:
    """Normaliza fechas (con o sin tzinfo) a UTC naive para poder compararlas."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt
