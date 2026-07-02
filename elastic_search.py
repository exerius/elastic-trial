from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

print("MAPPING:")
print(es.indices.get_mapping(index="texts_index"))

# 2. Анализ
print("\nANALYZE:")
sample = "попытка"
tokens = es.indices.analyze(index="texts_index", body={"field": "source.text", "text": sample})
print([t['token'] for t in tokens['tokens']])

# 3. Поиск
body = {"query": {"match": {"text": "попытка"}}}
resp = es.search(index="texts_index", body=body)

print(f"\nSEARCH: {resp['hits']['total']['value']}")

# 4. Попробуем терм-вектор для первого документа
resp_all = es.search(index="texts_index", body={"query": {"match_all": {}}, "size": 1})
if resp_all['hits']['hits']:
    doc_id = resp_all['hits']['hits'][0]['_id']
    tv = es.termvectors(index="texts_index", id=doc_id, fields=["text"])
    print(f"\nTERMVECTORS for doc {doc_id}:")
    print(list(tv['term_vectors']['text']['terms'].keys())[:20])