"""Test VideoAgent query on ingested Sintel trailer."""
import asyncio

from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from mmct.config.providers import VideoAgentProviderConfig
from mmct.providers.azure import (
    AISearchChapterProvider,
    AISearchKeyframesProvider,
    AISearchObjectCollectionProvider,
    AzureEmbeddingProvider,
    AzureLLMProvider,
    AzureStorageProvider,
)
from mmct.providers.local import ClipImageEmbeddingProvider
from mmct.video_pipeline import VideoAgent

credentials = ChainedTokenCredential(AzureCliCredential(), DefaultAzureCredential())

provider = VideoAgentProviderConfig(
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
)


async def main():
    print("=== VideoAgent Query Test ===\n")

    video_agent = VideoAgent(
        query="What is happening in this video? Describe the characters and key events.",
        video_id="sintel-trailer-test-001",
        use_critic_agent=True,
        stream=False,
        cache=False,
        provider=provider,
    )

    print("Running VideoAgent query...")
    response = await video_agent()

    print(f"\n--- Response ---")
    if isinstance(response, dict):
        for key, value in response.items():
            print(f"{key}: {value}")
    else:
        print(response)


if __name__ == "__main__":
    asyncio.run(main())
