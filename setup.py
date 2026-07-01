from elasticsearch import Elasticsearch, helpers
from sqlmodel import Session, create_engine, SQLModel

from models import Text, RubricTextLink, Rubric
import pandas as pd

"""Это скрипт создания базы данных и индекса"""

def get_linkage_table_strings(rubrics_list: list) -> list:
    rubric_indices = list()
    for rubric in rubrics_list:
        index = rubric_to_index_conversion[rubric]
        rubric_indices.append(index)
    return rubric_indices

def es_bulk_actions():
    for row in texts_table.iterrows():
        yield {
            "_index": index_name,
            "_id": row[0],
            "source":
                {
                    "id": row[0],
                    "text": row[1].text
                }
        }


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
es = Elasticsearch(['http://localhost:9200'])
index_name = "texts_index"
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body={
    "settings": {
        "analysis": {
            "filter": {
                "trigrams_filter": {
                    "type": "ngram",
                    "min_gram": 3, # Датасет многоязычен (русский, казахский, арабский, возможно др.), поэтому триграммы
                    "max_gram": 3
                }
            },
            "analyzer": {
                "trigrams_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "trigrams_filter"]
                }
            }
        }
    },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "text": {"type": "text", "analyzer": "russian"},
            }
        }
    })
engine = create_engine(sqlite_url, echo=True)


if es.indices.exists(index="texts_index"):
    es.indices.delete(index="texts_index")



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

SQLModel.metadata.create_all(engine)

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


success, errors = helpers.bulk(es, es_bulk_actions(), chunk_size=1500)
print(f"Индексировано: {success}, ошибок: {len(errors)}")
