from datetime import datetime
from typing import Optional, List

from sqlalchemy import table, Column, DateTime, text
from sqlmodel import Field, SQLModel, create_engine, Relationship


#Запрета на ORM в задании не было, использую sqlalchemy+sqlmodel

class BaseText(SQLModel):
    """Общая модель текста, от которой будем наследовать реально используемые"""
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    created_date: datetime


class RubricTextLink(SQLModel, table=True):
    """Промежуточная модель, связывающая тексты и рубрики. Она введена, чтобы не ставить связь M2M"""
    text_id: Optional[int] = Field(
        default=None,
        foreign_key="text.id",
        primary_key=True
    )
    rubric_id: Optional[int] = Field(
        default=None,
        foreign_key="rubric.id",
        primary_key=True
    )

class Rubric(SQLModel, table=True):
    """В задании говорилось, что рубрики доложны храниться как списки в таблице текстов, но это не соответсвует  1НФ"""
    id: Optional[int] =  Field(default=None, primary_key=True)
    name: str
    texts: List["Text"] = Relationship(
        back_populates="rubrics",
        link_model=RubricTextLink
    )

class Text(BaseText, table=True):
    """Модель для хранения текста в бд"""
    rubrics: List["Rubric"] = Relationship(
        back_populates="texts",
        link_model=RubricTextLink
    )
    created_at: datetime = Field(
        sa_column=Column(
            "created_at",
            DateTime,
            server_default=text('CURRENT_TIMESTAMP'), #Храним время для автосинхронизации с es
            nullable=False
        )
    )

class TextResponse(BaseText):
    """Модель объекта, который мы будем вохвращать через API"""
    rubrics: List[Rubric] = []
