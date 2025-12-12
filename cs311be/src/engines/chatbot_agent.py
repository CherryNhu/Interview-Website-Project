from llama_index.core.agent.workflow.function_agent import FunctionAgent
from llama_index.core.agent.workflow.workflow_events import (
    AgentInput,
    AgentOutput,
    ToolCall,
    ToolCallResult,
    AgentStream,
)
from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer
from src.engines.llm_engine import LLMEngine
from src.services.chatbot_tools import ChatbotTools
from src.prompts.prompt import *
class Agent:    
    """
    QAAgent class that initializes a FunctionAgent, takes queries, and returns responses.
    """

    def __init__(self):
        config = LLMEngine()
        self.llm = config.openai_llm
        self.tools = ChatbotTools()
        self.system_prompt = system_prompt
        self.agent = FunctionAgent(
            name="qa_agent",
            llm=self.llm,
            tools=self.tools.get_tools(),
            system_prompt=self.system_prompt,
        )
    async def run(self, query: str, memory: ChatMemoryBuffer):
        return self.agent.run(query, memory)
    async def stream_query(self, query: str, memory: ChatMemoryBuffer):
        """
        Streaming response from the agent.
        Can add tool call and tool call result to the stream.
        
        """
        handler = self.agent.run(query, memory=memory)
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                yield event.delta
    async def handle_query(self, query: str, memory: ChatMemoryBuffer) -> str:
        """
        Handles a query by running it through the agent.
        Args:
            query (str): The user query.
            memory: memory to pass into the agent.
        Returns:
            str: The response from the agent.
        """
        # Update tools with user_id context
        tools = self.tools.get_tools()
        
        agent = FunctionAgent(
            name="qa_agent",
            tools=tools,
            system_prompt=self.system_prompt,
            llm=self.llm,
        )
        #response = await agent.run(query, memory=memory)
        handler = agent.run(query, memory=memory)

        async for event in handler.stream_events():
            if isinstance(event, ToolCallResult):
                print(
                    f"Result from calling tool {event.tool_name}:\n\n{event.tool_output}"
                )
            if isinstance(event, ToolCall):
                print(
                    f"Calling tool {event.tool_name} with arguments:\n\n{event.tool_kwargs}"
                )

        response = await handler
        return str(response)
    async def translate_to_english(self, query: str) -> str:
        """
        Handles a query by running it through the agent.
        
        Args:
            query (str): The answer in vietnamese.
        
        Returns:
            str: Translate to English
        """

        response = self.llm.complete(tranlate_answer_vietnamese_to_english.format(text=query)).text
        response = response.replace("Translation:","").strip() 
        return str(response)