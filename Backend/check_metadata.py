import chromadb
import os


chroma_client = chromadb.PersistentClient(
    path=os.path.join(
        os.getcwd(),
        "chroma_db"
    )
)


collection = chroma_client.get_collection(
    name="who_medication_safety_day1"
)


data = collection.get(
    limit=5,
    include=[
        "documents",
        "metadatas"
    ]
)


print("\nMETADATA:")


for i, metadata in enumerate(
    data["metadatas"]
):

    print(f"\n{i + 1}:")

    print(metadata)
    