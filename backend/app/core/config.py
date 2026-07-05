from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    chroma_db_path: str
    embedding_model: str
    ollama_base_url: str
    ollama_model: str
    chunk_size: int
    chunk_overlap: int
    top_k_results: int

    class Config:
        env_file = ".env"

settings = Settings()