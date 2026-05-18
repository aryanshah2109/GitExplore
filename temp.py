from rank_bm25 import BM25Okapi

documents = [
    "FastAPI dependency injection tutorial",
    "Python async programming",
    "Dependency injection in Spring Boot"
]

tokenized_docs = [doc.lower().split() for doc in documents]
print(tokenized_docs)

bm25 = BM25Okapi(tokenized_docs)

query = "dependecy injection".split()

score = bm25.get_scores(query)

print(score)

top_docs = bm25.get_top_n(query, documents, n=2)

print(top_docs)