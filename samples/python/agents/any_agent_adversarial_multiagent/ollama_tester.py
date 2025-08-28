import os
from pathlib import Path
from any_agent import AgentConfig, AnyAgent, AgentFramework
import nest_asyncio


def read_file(file_path: str) -> str:
    """
    Read a file from the file path given and return its content.

    Args:
        file_path: The path of the file to read.
    """
    try:
        with open(file_path) as file:
            content = file.read()
    except Exception as e:
        content = f"Error reading file: {file_path} \n\n {e}"
    return content



nest_asyncio.apply()
model_id = "ollama/granite3.3"

model_args = {"num_ctx": 32000}

agent = AnyAgent.create(
     "tinyagent",
     AgentConfig(
         model_id=model_id,
         instructions="You are an expert summarizer.",
         tools=[read_file],
         model_args=model_args,
     ),
)
    
abs_path = Path("../../demo/app.py").resolve()
agent_trace = agent.run(
    f"Carefully read the file in the path: {abs_path} and return summary of what the code does."
)   


