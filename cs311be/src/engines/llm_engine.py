import os
from functools import lru_cache
from typing import List, Dict
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()

from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.llms import ChatMessage

try:
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
except Exception:
    AzureOpenAIEmbedding = None  # optional

# Env (giữ nguyên theo dự án hiện tại)
api_key = os.getenv('AZURE_OPENAI_API_KEY')
azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_version = os.getenv('AZURE_OPENAI_API_VERSION')

deployment_name = os.getenv("deployment_name_2")
model_name = os.getenv("model_name_2")

deployment_name_2 = os.getenv("AZURE_OPENAI_DEPLOYMENT")
model_name_2 = os.getenv("AZURE_OPENAI_MODEL_NAME")

embeding_model_name = os.getenv("EMBEDDING_MODEL_NAME")
embeding_model_deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
embedding_api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or api_key
embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or azure_endpoint
embedding_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION") or api_version

class LLMEngine:
    def __init__(self):
        # Giữ tương thích với practice
        self.openai_llm = AzureOpenAI(
            model=model_name or model_name_2,
            engine=deployment_name or deployment_name_2,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )
        # llm2 cho practice (fallback nếu biến thiếu)
        self.llm2 = AzureOpenAI(
            model=model_name_2 or model_name or (model_name or model_name_2),
            engine=deployment_name_2 or deployment_name or (deployment_name or deployment_name_2),
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
        )
        # Embedding optional
        self.embed_model = None
        if AzureOpenAIEmbedding and embeding_model_name and embeding_model_deployment_name:
            try:
                self.embed_model = AzureOpenAIEmbedding(
                    model=embeding_model_name,
                    deployment_name=embeding_model_deployment_name,
                    api_key=embedding_api_key,
                    azure_endpoint=embedding_endpoint,
                    api_version=embedding_api_version,
                )
            except Exception as e:
                print(f"[LLMEngine] Embedding init skipped: {e}")

    async def call_llm(self, prompt, response_format=None):
        try:
            response = await self.openai_llm.acomplete(prompt, response_format=response_format)
            return response.text
        except Exception as e:
            message = f'Error in call_llm function. Detail: {e}'
            print(message)
            raise HTTPException(status_code=500, detail=message)

    # Thêm chat cho mock
    def chat(self, messages: List[Dict[str, str]]) -> str:
        try:
            chat_msgs = [ChatMessage(role=m["role"], content=m["content"]) for m in messages]
            resp = self.openai_llm.chat(chat_msgs)
            return resp.message.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLMEngine.chat error: {e}")

@lru_cache(maxsize=1)
def get_llm_engine() -> LLMEngine:
    return LLMEngine()