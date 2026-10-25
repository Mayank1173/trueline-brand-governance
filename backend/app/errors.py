"""Application-specific exceptions."""

from __future__ import annotations


class NotFoundError(Exception):
    pass


class PersistenceError(Exception):
    pass
