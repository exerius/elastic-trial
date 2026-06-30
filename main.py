from venv import logger

from fastapi import FastAPI

app = FastAPI()


@app.get("/texts/search/{string}")
async def search_texts(string: str):
    logger.info(f"Search performed for: '{string}'")
    return 200

@app.delete("textx/delete/{text_id}")
async def delete_text(text_id: int):
    logger.info(f"Deleted text with id {text_id}")
    return 200