"""Test video ingestion pipeline with Big Buck Bunny sample video."""
import asyncio
import os

from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from mmct.config.providers import IngestionProviderConfig
from mmct.providers.azure import (
    AISearchChapterProvider,
    AISearchKeyframesProvider,
    AISearchObjectCollectionProvider,
    AzureEmbeddingProvider,
    AzureLLMProvider,
    AzureStorageProvider,
    WhisperTranscriptionProvider,
)
from mmct.providers.local import ClipImageEmbeddingProvider
from mmct.video_pipeline.core.ingestion.ingestion_pipeline import IngestionPipeline
from mmct.video_pipeline.core.ingestion.languages import Languages

credentials = ChainedTokenCredential(AzureCliCredential(), DefaultAzureCredential())

provider = IngestionProviderConfig(
    llm_provider=AzureLLMProvider(
        endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
        deployment_name="gpt-4o",
        model_name="gpt-4o",
        api_version="2024-08-01-preview",
        credentials=credentials,
    ),
    embedding_provider=AzureEmbeddingProvider(
        endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
        deployment_name="text-embedding-ada-002",
        api_version="2024-08-01-preview",
        credentials=credentials,
    ),
    image_embedding_provider=ClipImageEmbeddingProvider(),
    vectordb_chapter=AISearchChapterProvider(
        endpoint="https://msrxct-mmct-search.search.windows.net",
        index_name="mmct-chapters",
        credentials=credentials,
    ),
    vectordb_keyframes=AISearchKeyframesProvider(
        endpoint="https://msrxct-mmct-search.search.windows.net",
        index_name="mmct-keyframes",
        credentials=credentials,
    ),
    vectordb_object_registry=AISearchObjectCollectionProvider(
        endpoint="https://msrxct-mmct-search.search.windows.net",
        index_name="mmct-objects",
        credentials=credentials,
    ),
    storage_provider=AzureStorageProvider(
        storage_account_name="msrxctmmctsa",
        keyframe_container_name="mmct-framescontainer",
        credentials=credentials,
    ),
    transcription_provider=WhisperTranscriptionProvider(
        endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
        deployment_name="whisper",
        api_version="2024-08-01-preview",
        credentials=credentials,
    ),
)

VIDEO_PATH = os.path.join(os.path.dirname(__file__), "test_data", "big_buck_bunny.mp4")

pipeline = IngestionPipeline(
    video_path=VIDEO_PATH,
    video_id="big-buck-bunny-test-001",
    provider=provider,
    language=Languages.ENGLISH_UNITED_STATES,
    verbosity=1,
)

print(f"Starting ingestion for: {VIDEO_PATH}")
report = asyncio.run(pipeline.run())
print(f"\nIngestion complete! Status: {report.status}")
print(f"Report: {report}")
