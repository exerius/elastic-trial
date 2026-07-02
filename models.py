from datetime import datetime
from typing import Optional, List, Any

from pydantic import field_validator
from sqlmodel import Field, SQLModel, Relationship


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


class TextResponse(BaseText):
    """Модель объекта, который мы будем возвращать через API"""
    rubrics: List[str] = []


    @field_validator('rubrics', mode='before')
    @classmethod
    def extract_rubric_names(cls, v: Any) -> List[str]:
        if isinstance(v, list):
            return [item.name if hasattr(item, 'name') else item for item in v]
        return v