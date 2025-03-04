"""
Configuration for LLM models and other settings.
"""

import os
from typing import Union

import dotenv
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel

# Load environment variables
dotenv.load_dotenv()

# Default model configuration
DEFAULT_MODEL: Union[str, Model] = "groq:llama-3.3-70b-versatile"

# Alternative model configurations
TOGETHER_MODEL: Model = OpenAIModel(
    model_name=os.getenv("LLM_MODEL", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"),
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY"),
)

OPENROUTER_MODEL: Model = OpenAIModel(
    model_name="microsoft/phi-3-medium-128k-instruct:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_KEY"),
)

# Model to use across the application
# Change this to switch between different models
ACTIVE_MODEL: Union[str, Model] = DEFAULT_MODEL
