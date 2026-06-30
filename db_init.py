from sqlmodel import Session, create_engine

from models import Text, RubricTextLink, Rubric
import pandas as pd

"""Это скрипт создания базы данных"""

def get_linkage_table_strings(rubrics_list: list) -> list:
    rubric_indices = list()
    for rubric in rubrics_list:
        index = rubric_to_index_conversion[rubric]
        rubric_indices.append(index)
    return rubric_indices


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)



all_data = pd.read_csv("data/posts.csv", parse_dates=["created_date"])
rubrics = all_data["rubrics"]
all_data["rubrics"] = rubrics.str.replace(r"\[|\]|\ |\'", "", regex=True).str.split(",") #Преобразовываем рубрики в списки
unique_rubrics = all_data["rubrics"].explode(ignore_index=True).drop_duplicates(ignore_index=True)
rubric_to_index_conversion = {unique_rubrics[i]:i for i in unique_rubrics.index}
posts_rubrics = all_data.rubrics.apply(get_linkage_table_strings)
all_data["rubrics"] = posts_rubrics
linkage_table = list()
for index, row in zip(all_data.index, all_data.rubrics):
    for rubric in row:
     linkage_table.append({"text_id": index, "rubric_id": rubric})
texts_table = all_data.drop(columns=["rubrics"])
linkage_table = linkage_table

with Session(engine) as session:
    for rubric_name in unique_rubrics:
        session.add(Rubric(name=rubric_name))
    session.commit()

    for row in texts_table.iterrows():
        session.add(Text(text=row[1].text, created_date=row[1].created_date))
    session.commit()
    for row in linkage_table:
        session.add(RubricTextLink(text_id=row["text_id"], rubric_id=row["rubric_id"]))
    session.commit()
