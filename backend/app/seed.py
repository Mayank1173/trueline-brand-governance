"""Idempotent seeding for the clearly labelled demonstration dataset."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .models import ApprovedFact, Brand, Guideline
from .seed_data import demo_seed_payload

logger = logging.getLogger(__name__)


def seed_demo_data(session: Session) -> None:
    brands, guidelines, facts = demo_seed_payload()

    for payload in brands:
        _upsert(session, Brand, payload)

    for payload in guidelines:
        _upsert(session, Guideline, payload)

    for payload in facts:
        _upsert(session, ApprovedFact, payload)

    session.commit()
    logger.info(
        "Seeded illustrative demo data: %s brands, %s guidelines, %s facts",
        len(brands),
        len(guidelines),
        len(facts),
    )


def _upsert(session: Session, model, payload: dict) -> None:
    row = session.get(model, payload["id"])
    if row is None:
        session.add(model(**payload))
        return
    for key, value in payload.items():
        if key != "id":
            setattr(row, key, value)
