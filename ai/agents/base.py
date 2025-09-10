"""
Base Agent Class

Provides the foundational structure and common functionality for all
specialized agents in the rule generation pipeline.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from google import genai
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result structure for agent operations"""

    success: bool
    data: Any
    metadata: Dict[str, Any] = None
    errors: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.errors is None:
            self.errors = []


class BaseAgent(ABC):
    """
    Base class for all AI agents in the rule generation pipeline.

    Each agent is responsible for a specific aspect of processing regulatory
    documents and generating compliance rules.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", **kwargs):
        """
        Initialize the base agent.

        Args:
            model_name: Google Gemini model to use
            **kwargs: Additional configuration options
        """
        self.model_name = model_name
        # Get the client from the ai module
        from ai import client

        self.client = client
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Return the human-readable name of this agent"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this agent does"""
        pass

    @abstractmethod
    async def process(
        self, input_data: Any, context: Dict[str, Any] = None
    ) -> AgentResult:
        """
        Process input data and return results.

        Args:
            input_data: The data to process (varies by agent type)
            context: Additional context from previous agents

        Returns:
            AgentResult containing the processed data
        """
        pass

    async def _call_llm(self, prompt: str, system_instruction: str = None) -> str:
        """
        Make a call to the LLM with error handling.

        Args:
            prompt: The prompt to send to the LLM
            system_instruction: Optional system instruction

        Returns:
            The LLM response text
        """
        try:
            if not self.client:
                raise Exception("AI client not initialized")

            # Prepare the prompt with system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"

            response = self.client.models.generate_content(
                model=self.model_name, contents=full_prompt
            )
            return response.text

        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise

    async def _call_llm_stream(
        self, prompt: str, system_instruction: str = None
    ) -> AsyncGenerator[str, None]:
        """
        Make a streaming call to the LLM.

        Args:
            prompt: The prompt to send to the LLM
            system_instruction: Optional system instruction

        Yields:
            Chunks of the LLM response
        """
        try:
            if not self.client:
                raise Exception("AI client not initialized")

            # Prepare the prompt with system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"

            stream = self.client.models.generate_content_stream(
                model=self.model_name, contents=full_prompt
            )

            for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            self.logger.error(f"Streaming LLM call failed: {str(e)}")
            raise

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM with error handling.

        Args:
            response_text: The raw response text from LLM

        Returns:
            Parsed JSON data
        """
        try:
            # Try to find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            self.logger.error(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from {self.agent_name}")

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """
        Validate that required fields are present in the data.

        Args:
            data: The data to validate
            required_fields: List of required field names

        Returns:
            List of missing field names
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        return missing_fields

    def log_progress(self, message: str, level: str = "info"):
        """
        Log progress messages.

        Args:
            message: The message to log
            level: Log level (debug, info, warning, error)
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(f"[{self.agent_name}] {message}")
