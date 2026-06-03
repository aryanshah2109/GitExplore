from backend.app.core.qdrant_setup import client

client.delete_collection(
    collection_name="gitexplore"
)