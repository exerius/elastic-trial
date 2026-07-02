import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from sqlmodel import Session, create_engine, SQLModel

from models import Text, RubricTextLink, Rubric
import pandas as pd

load_dotenv()

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
            "id": row[0],
            "text": row[1].text
        }


sqlite_url = os.getenv("DB_LINK")
es = Elasticsearch(hosts=[os.getenv("ES_LINK")], http_auth=(os.getenv('ELASTICSEARCH_USER'), os.getenv('ELASTICSEARCH_PASSWORD')))
index_name = os.getenv("ES_INDEX")
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body={
        "settings": {
            "analysis": {
                "filter": {
                    "trigrams_filter": {
                        "type": "ngram",
                        "min_gram": 3, # Датасет многоязычный, поэтому триграммы
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
                "text": {
                    "type": "text",
                    "analyzer": "trigrams_analyzer",
                    "search_analyzer": "trigrams_analyzer"
                }
            }
        }
    })
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

SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    for i, rubric_name in enumerate(unique_rubrics):
        session.add(Rubric(id=i, name=rubric_name))
    session.commit()

    for row in texts_table.iterrows():
        session.add(Text(id=row[0], text=row[1].text, created_date=row[1].created_date))
    session.commit()
    for row in linkage_table:
        session.add(RubricTextLink(text_id=row["text_id"], rubric_id=row["rubric_id"]))
    session.commit()


success, errors = helpers.bulk(es, es_bulk_actions(), chunk_size=1500)
print(f"Индексировано: {success}, ошибок: {len(errors)}")
es.indices.refresh(index="texts_index")
