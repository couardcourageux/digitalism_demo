from sqlalchemy.orm import DeclarativeBase, registry
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from src.utils.date import get_current_time

from typing import Optional

reg = registry()


class Base(DeclarativeBase):
    registry = reg

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_time,
        onupdate=get_current_time,
        nullable=False
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
