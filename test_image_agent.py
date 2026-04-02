"""Quick test of ImageAgent with Azure OpenAI."""
import asyncio

from azure.identity import AzureCliCredential, ChainedTokenCredential, DefaultAzureCredential

from mmct.config.providers import ImageAgentProviderConfig
from mmct.image_pipeline import ImageAgent, ImageQnaTools
from mmct.providers.azure import AzureLLMProvider

credentials = ChainedTokenCredential(AzureCliCredential(), DefaultAzureCredential())

provider = ImageAgentProviderConfig(
    llm_provider=AzureLLMProvider(
        endpoint="https://msrxct-mmct-aoai.openai.azure.com/",
        deployment_name="gpt-4o",
        model_name="gpt-4o",
        api_version="2024-08-01-preview",
        credentials=credentials,
    )
)

image_agent = ImageAgent(
    query="What objects are visible in this image?",
    image_path=".venv/Lib/site-packages/ultralytics/assets/bus.jpg",
    tools=[ImageQnaTools.vit, ImageQnaTools.object_detection, ImageQnaTools.ocr, ImageQnaTools.recog],
    use_critic_agent=True,
    stream=False,
    provider=provider,
)

response = asyncio.run(image_agent())
print(f"\nResponse: {response}")
