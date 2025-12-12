import os
from fastapi import status, HTTPException
from dotenv import load_dotenv
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.core.llms import ChatMessage, MessageRole
load_dotenv()

# Accessing variables for main LLM
api_key = os.getenv('RESUME_FLOW_AZURE_OPENAI_API_KEY')
azure_endpoint = os.getenv('RESUME_FLOW_AZURE_OPENAI_ENDPOINT')
api_version = os.getenv('RESUME_FLOW_AZURE_OPENAI_VERSION')
deployment_name = os.getenv('RESUME_FLOW_AZURE_OPENAI_DEPLOYMENT_NAME')
model_name = os.getenv('RESUME_FLOW_AZURE_OPENAI_MODEL_NAME')

# Accessing variables for Mini LLM
mini_api_key = os.getenv('RESUME_FLOW_AZURE_OPENAI_API_KEY')
mini_azure_endpoint = os.getenv('RESUME_FLOW_AZURE_OPENAI_ENDPOINT')
mini_api_version = os.getenv('RESUME_FLOW_AZURE_OPENAI_VERSION')
mini_deployment_name = os.getenv('RESUME_FLOW_AZURE_OPENAI_DEPLOYMENT_NAME_2')
mini_model_name = os.getenv('RESUME_FLOW_AZURE_OPENAI_MODEL_NAME_2')

# Embedding variables
embedding_api_key = os.getenv("RESUME_FLOW_AZURE_OPENAI_API_KEY")
embedding_endpoint = os.getenv("RESUME_FLOW_AZURE_OPENAI_ENDPOINT")
embedding_api_version = os.getenv("RESUME_FLOW_AZURE_OPENAI_VERSION")
embedding_model_name = os.getenv("RESUME_FLOW_AZURE_OPENAI_EMBEDDING_MODEL_NAME")
embedding_deployment_name = os.getenv("RESUME_FLOW_AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

class LLMEngineResumeFlow:
    def __init__(self, system_prompt: str = None):
        # Validate main LLM variables
        if not all([api_key, azure_endpoint, api_version, deployment_name, model_name]):
            raise ValueError("Missing required environment variables for Azure OpenAI LLM (api_key, azure_endpoint, api_version, deployment_name, model_name)")

        # Validate mini LLM variables
        if not all([mini_api_key, mini_azure_endpoint, mini_api_version, mini_deployment_name, mini_model_name]):
            raise ValueError("Missing required environment variables for Azure OpenAI Mini LLM (MINI_API_KEY, MINI_AZURE_ENDPOINT, MINI_API_VERSION, MINI_DEPLOYMENT_NAME, MINI_MODEL_NAME)")

        # Validate embedding variables
        if not all([embedding_model_name, embedding_deployment_name, embedding_api_key, embedding_endpoint, embedding_api_version]):
            raise ValueError("Missing required environment variables for Azure OpenAI Embedding (EMBEDDING_MODEL_NAME, AZURE_OPENAI_EMBEDDING_DEPLOYMENT, AZURE_OPENAI_EMBEDDING_API_KEY, AZURE_OPENAI_EMBEDDING_ENDPOINT, AZURE_OPENAI_EMBEDDING_API_VERSION)")

        self.system_prompt = system_prompt
        
        # Main LLM (GPT-4o)
        self.llm = AzureOpenAI(
            model=model_name,
            engine=deployment_name,
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=0
        )
        
        # Mini LLM (GPT-4o-mini)
        self.mini_llm = AzureOpenAI(
            model=mini_model_name,
            engine=mini_deployment_name,
            api_key=mini_api_key,
            azure_endpoint=mini_azure_endpoint,
            api_version=mini_api_version,
            temperature=0
        )
        
        # Embedding model
        self.embed_model = AzureOpenAIEmbedding(
            model=embedding_model_name,
            deployment_name=embedding_deployment_name,
            api_key=embedding_api_key,
            azure_endpoint=embedding_endpoint,
            api_version=embedding_api_version
        )
    
    def _create_chat_messages(self, prompt: str):
        """Create proper ChatMessage objects for LlamaIndex"""
        messages = []
        
        if self.system_prompt:
            messages.append(ChatMessage(
                role=MessageRole.SYSTEM, 
                content=self.system_prompt
            ))
        
        messages.append(ChatMessage(
            role=MessageRole.USER, 
            content=prompt
        ))
        
        return messages
        
    async def call_llm(self, prompt, response_format=None, use_mini=False):
        """
        Call LLM with option to use mini model
        Args:
            prompt: Input prompt
            response_format: Optional response format for structured output
            use_mini: If True, use GPT-4o-mini instead of GPT-4o
        """
        try:
            # Choose which LLM to use
            selected_llm = self.mini_llm if use_mini else self.llm
            
            # DEBUG: Check if system prompt exists
            # print(f"DEBUG - System prompt exists: {self.system_prompt is not None}")
            # print(f"DEBUG - Using mini model: {use_mini}")
            
            # Method 1: Use ChatMessage objects (Recommended)
            if response_format is None:
                messages = self._create_chat_messages(prompt)
                
                # DEBUG: Print messages being sent
                for i, msg in enumerate(messages):
                    print(f"DEBUG - Message {i}: Role={msg.role}, Content={msg.content[:100]}...")
                
                response = await selected_llm.achat(messages=messages)
            else:
                # Method 2: For structured output, use acomplete instead
                full_prompt = ""
                if self.system_prompt:
                    full_prompt = f"System: {self.system_prompt}\n\nUser: {prompt}"
                else:
                    full_prompt = prompt
                
                response = await selected_llm.acomplete(
                    prompt=full_prompt,
                    response_format=response_format
                )

            # Extract content based on response type
            content = None
            
            # For ChatResponse (from achat)
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content = response.message.content
            # For CompletionResponse (from acomplete)
            elif hasattr(response, 'text'):
                content = response.text
            # For other response types
            elif hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            elif isinstance(response, dict):
                content = response.get('content', '') or response.get('text', '') or response.get('message', {}).get('content', '')
            else:
                # Last resort: convert to string
                content = str(response)
            
            if not content or content.strip() == "":
                raise ValueError(f"Empty or invalid response from LLM. Response type: {type(response)}, Response: {response}")

            return content.strip()
            
        except Exception as e:
            error_message = f'Error in call_llm function. Detail: {str(e)}'
            raise HTTPException(status_code=500, detail=error_message)
    
    async def call_mini_llm(self, prompt, response_format=None):
        """
        Convenience method to call GPT-4o-mini directly
        """
        return await self.call_llm(prompt, response_format, use_mini=True)

    async def get_embedding(self, text: str) -> list:
        """Generate embedding vector for a given text using Azure OpenAI Embedding model.

        Args:
            text (str): Input text to embed.

        Returns:
            list: Embedding vector as a list of floats.
        """
        try:
            if not text or text.strip() == "":
                raise ValueError("Text cannot be empty")
            
            embedding = await self.embed_model.aget_text_embedding(text.strip())
            
            if not embedding:
                raise ValueError("Empty embedding returned")
            
            return embedding
            
        except Exception as e:
            error_message = f'Error in get_embedding function. Detail: {str(e)}'
            raise HTTPException(status_code=500, detail=error_message)