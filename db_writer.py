from pymilvus import MilvusClient
from pymilvus.model.dense import SentenceTransformerEmbeddingFunction, OpenAIEmbeddingFunction

from processing import read_output
from models import ExtendedFunctionDescription, ExtendedFileDescription
from typing import List
from tqdm import tqdm

def get_milvus_client(db_name: str) -> MilvusClient:
    """Sets up and returns a Milvus client."""
    return MilvusClient(db_name)

def setup_milvus_collection(client: MilvusClient, collection_name: str, dimension: int):
    """Sets up the Milvus collection, dropping it if it already exists."""
    if client.has_collection(collection_name=collection_name):
        client.drop_collection(collection_name=collection_name)

    client.create_collection(
        collection_name=collection_name,
        dimension=dimension,
    )


def insert_function_descriptions(client: MilvusClient, collection_name: str, docs: List[ExtendedFunctionDescription], embedding_fn):
    """Encodes documents and inserts them into the Milvus collection."""
    batch_size = 64
    vectors = []
    for i in tqdm(list(range(0, len(docs), batch_size)), desc="Encoding function descriptions"):
        batch_docs = docs[i:i+batch_size]
        vectors.extend(embedding_fn.encode_documents([f"search_document: {d.to_vector_string()}" for d in batch_docs]))


    data = [
        {"id": i,
         "vector": vectors[i],
         "text": docs[i].to_vector_string(),
         "function_name": docs[i].function_name,
         "class_name": docs[i].class_name,
         "tags": ",".join(docs[i].tags),
         "repo_name": docs[i].repo_name,
         "filepath": docs[i].filepath,
         "return_type": docs[i].return_type,
         "functionality": docs[i].functionality,
        }
        for i in range(len(docs))
    ]

    print("Data has", len(data), "entities, each with fields: ", data[0].keys())
    print("Vector dim:", len(data[0]["vector"]))

    client.insert(collection_name=collection_name, data=data)

    print(f'Finished loading function descriptions')

def insert_file_descriptions(client: MilvusClient, collection_name: str, docs: List[ExtendedFileDescription], embedding_fn):
    """Encodes documents and inserts them into the Milvus collection."""
    batch_size = 64
    vectors = []
    for i in tqdm(list(range(0, len(docs), batch_size)), desc="Encoding file descriptions"):
        batch_docs = docs[i:i+batch_size]
        vectors.extend(embedding_fn.encode_documents([f"search_document: {d.to_vector_string()}" for d in batch_docs]))


    data = [
        {"id": i,
         "vector": vectors[i],
         "text": docs[i].to_vector_string(),
         "repo_name": docs[i].repo_name,
         "filepath": docs[i].filepath,
         "overall_purpose_and_domain": docs[i].overall_purpose_and_domain,
         "primary_responsibilities": "\n".join(docs[i].primary_responsibilities),
         "tags": ",".join(docs[i].tags),
        }
        for i in range(len(docs))
    ]

    print("Data has", len(data), "entities, each with fields: ", data[0].keys())
    print("Vector dim:", len(data[0]["vector"]))

    client.insert(collection_name=collection_name, data=data)

    print(f'Finished loading file descriptions')


def search_collection(client: MilvusClient, collection_name: str, query: str, embedding_fn, limit: int = 5):
    """Performs a search on the Milvus collection."""
    query_vectors = embedding_fn.encode_queries([f"search_query: {query}"])

    res = client.search(
        collection_name=collection_name,
        data=query_vectors,
        limit=limit,
        output_fields=["text", "class_name", "function_name", "filepath"],
    )
    for r in res[0]:
        print(r)
        print("\n\n")

def write_data_to_milvus(client: MilvusClient, function_desc_collection: str, file_desc_collection: str, embedding_fn):
    """Reads output and writes data to Milvus collections."""
    output = read_output()
    insert_function_descriptions(client, function_desc_collection, output.function_descriptions, embedding_fn)
    insert_file_descriptions(client, file_desc_collection, output.file_descriptions, embedding_fn)


def interactive_search(client, collection_name: str, embedding_fn):
    """Interactive search function."""
    
    print("Milvus interactive search. Type 'quit' to exit.")
    while True:
        query = input("Enter search query: ")
        if query.lower() == 'quit':
            break
        search_collection(client, collection_name, query, embedding_fn)

def main():
    """Main function to set up, insert data, and search the Milvus collection."""
    client = get_milvus_client("milvus_demo.db")
    model_name = "nomic-ai/nomic-embed-text-v1"
    function_desc_collection = "function_desc"
    file_desc_collection = "file_desc"
    dimension = 768
    # embedding_fn = SentenceTransformerEmbeddingFunction(model_name, trust_remote_code=True)
    embedding_fn = OpenAIEmbeddingFunction(model_name, api_key="some", base_url="http://100.121.75.10:8000/v1/")

    # setup_milvus_collection(client, function_desc_collection, dimension)
    # setup_milvus_collection(client, file_desc_collection, dimension)
    # write_data_to_milvus(client, function_desc_collection, file_desc_collection, embedding_fn)

    interactive_search(client, function_desc_collection, embedding_fn)


if __name__ == '__main__':
    main()
