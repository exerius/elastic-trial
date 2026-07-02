import os
from typing import Optional, List

from elasticsearch import Elasticsearch
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from database import get_session
from models import Text, TextResponse
from dotenv import load_dotenv


load_dotenv()

es_client = Elasticsearch(hosts=[os.getenv("ES_LINK")], http_auth=(os.getenv('ELASTICSEARCH_USER'), os.getenv('ELASTICSEARCH_PASSWORD')))


def get_es() -> Elasticsearch:
    return es_client


app = FastAPI()


@app.get("/texts/search/", response_model=List[TextResponse])
async def search_texts(search: Optional[str] = None, session: Session = Depends(get_session),
                       es: Elasticsearch = Depends(get_es)):
    if search is None:
        raise HTTPException(
            status_code=404,
            detail="You must include search argument"
        )
    else:
        es_request_body = {
            "query": {"match": {"text": {"query": search}}},
            "_source": ["id"],
            "size": 20
        }
        response = es.search(index=os.getenv("ES_INDEX"), **es_request_body)
        ids = [hit["_source"]["id"] for hit in response["hits"]["hits"]]
        db_query = (
            select(Text)
            .where(Text.id.in_(ids))
            .options(selectinload(Text.rubrics))
            .order_by(Text.created_date)
        )
        texts = session.exec(db_query).all()
        if len(texts) == 0:
            raise HTTPException(
                status_code=404,
                detail="Nothing was found"
            )
    return texts


@app.delete("/text/delete/{text_id}")
async def delete_text(text_id: int, session: Session = Depends(get_session), es: Elasticsearch = Depends(get_es)):
    text = session.get(Text, text_id)
    if text is None:
        raise HTTPException(status_code=404, detail=f"Text with id {text_id} not found")
    try:
        es.delete_by_query(index=os.getenv("ES_INDEX"), **{"query": {"match": {"id": {"query": text_id}}}}, refresh=True)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Elasticsearch error: {str(e)}"
        )
    try:
        session.delete(text)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {"status": "success", "id": text_id}
