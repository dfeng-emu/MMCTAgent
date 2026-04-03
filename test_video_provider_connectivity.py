"""Test VideoAgent provider connectivity and RBAC access."""
import asyncio
import sys

from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

credentials = ChainedTokenCredential(AzureCliCredential(), DefaultAzureCredential())


async def test_llm():
    """Test Azure OpenAI LLM access."""
    from mmct.providers.azure import AzureLLMProvider

    print("--- Testing LLM Provider (gpt-4o) ---")
    try:
        provider = AzureLLMProvider(
            endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
            deployment_name="gpt-4o",
            model_name="gpt-4o",
            api_version="2024-08-01-preview",
            credentials=credentials,
        )
        response = await provider.chat_completion(
            messages=[{"role": "user", "content": "Say hello in one word."}]
        )
        print(f"  SUCCESS: {response}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")


async def test_embedding():
    """Test Azure OpenAI Embedding access."""
    from mmct.providers.azure import AzureEmbeddingProvider

    print("\n--- Testing Embedding Provider (text-embedding-ada-002) ---")
    try:
        provider = AzureEmbeddingProvider(
            endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
            deployment_name="text-embedding-ada-002",
            api_version="2024-08-01-preview",
            credentials=credentials,
        )
        result = await provider.embedding("test query")
        print(f"  SUCCESS: got embedding with {len(result)} dimensions")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")


async def test_search():
    """Test Azure AI Search access."""
    from mmct.providers.azure import AISearchChapterProvider

    print("\n--- Testing AI Search Provider (chapters index) ---")
    try:
        provider = AISearchChapterProvider(
            endpoint="https://msrxct-mmct-search.search.windows.net",
            index_name="mmct-chapters",
            credentials=credentials,
        )
        # Try a search — will fail if index doesn't exist or no RBAC
        results = await provider.search(query="test", query_vector=[0.0] * 1536)
        print(f"  SUCCESS: search returned {len(results)} results")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")


async def test_storage():
    """Test Azure Blob Storage access."""
    from mmct.providers.azure import AzureStorageProvider

    print("\n--- Testing Storage Provider (msrxctmmctsa) ---")
    try:
        provider = AzureStorageProvider(
            storage_account_name="msrxctmmctsa",
            keyframe_container_name="mmct-framescontainer",
            credentials=credentials,
        )
        # Try to get a URL — tests connectivity
        url = await provider.get_file_url(
            container_name="mmct-framescontainer", blob_name="nonexistent.jpg"
        )
        print(f"  SUCCESS: got URL: {url}")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
    finally:
        try:
            await provider.close()
        except Exception:
            pass


async def test_image_embedding():
    """Test CLIP image embedding provider (local, no Azure needed)."""
    from mmct.providers.local import ClipImageEmbeddingProvider

    print("\n--- Testing CLIP Image Embedding Provider (local) ---")
    try:
        provider = ClipImageEmbeddingProvider()
        result = await provider.image_embedding("a photo of a cat")
        print(f"  SUCCESS: got embedding with {len(result)} dimensions")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
    finally:
        try:
            await provider.close()
        except Exception:
            pass


async def main():
    print("=== VideoAgent Provider Connectivity Test ===\n")
    await test_llm()
    await test_embedding()
    await test_search()
    await test_storage()
    await test_image_embedding()
    print("\n=== Done ===")


if __name__ == "__main__":
    asyncio.run(main())
