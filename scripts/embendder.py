#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "langchain-chroma",
#     "langchain-docling",
#     "langchain-openai",
#     "langchain-text-splitters",
#     "python-dotenv",
#     "typer>=0.19.2",
# ]
# ///


import json
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import typer
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_docling.loader import DoclingLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

TARGET_DIR: str = "RAG-Cartoes"  # Where to look for documents
COLLECTION_NAME: str = "banco_collection"  # Name of our collection
PERSISTENCE_DIR: str = "./chroma_db"  # Name of our vector store
EMBEDDING_MODEL: str = "text-embedding-3-large"  # Model to create vectors


def clean_metadata_value(v):
    """Clean metadata section from invalid values. It ignores scalar values,
    join lists into strings split by comma and serialize complex types into
    json."""
    # Allowed scalar types: str, int, float, bool, None
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    # If it's a list of scalars, join into a string
    if isinstance(v, list) and all(isinstance(x, (str, int, float, bool)) for x in v):
        return ",".join(map(str, v))
    # Fallback: serialize everything else to JSON (dicts, lists with dicts,
    # complex objects)
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


def clean_document(d: Document) -> Document:
    """Clear a document from noise."""
    cleaned_meta = {k: clean_metadata_value(val) for k, val in d.metadata.items()}
    return Document(page_content=d.page_content, metadata=cleaned_meta)


def gather_documents(rootdir: Path) -> Iterator[Path]:
    """Gather files from a rootdir, operates recursively using `rglob`"""
    if not rootdir.exists():
        raise IOError(f"Error {rootdir} does not exist")
    return (item for item in rootdir.rglob("*") if item.is_file())


def lazy_load_documents(files: Iterable[Path]) -> Iterator[Document]:
    """Lazy load Documents from a list of files"""
    loader = DoclingLoader(file_path=map(str, files))
    return loader.lazy_load()


def split_documents(
    docs: Iterable[Document], size: int = 256, overlap: int = 64
) -> Sequence[Document]:
    """Split documents into chunks to improve loading speeds, accepts an overlap
    that controls how the splitings is made."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size, chunk_overlap=overlap, add_start_index=True
    )
    return text_splitter.split_documents(docs)


def main(
    target_dir: str = TARGET_DIR,
    embedding_model: str = EMBEDDING_MODEL,
    persist_dir: str = PERSISTENCE_DIR,
    collection_name: str = COLLECTION_NAME,
):
    """
    Script to create a vector store from our documents database.
    To use this script you need access to an OpenAI Embendding Model.

    This project is licensed under the MIT License -- see https://mit-license.org/ for details.
    """

    files = gather_documents(Path(target_dir))
    docs = split_documents(lazy_load_documents(files))
    clean_docs = [clean_document(d) for d in docs]

    embeddings = OpenAIEmbeddings(model=embedding_model)

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    _ = vector_store.add_documents(documents=clean_docs)

    print("Embeddings completed.")


if __name__ == "__main__":
    typer.run(main)
