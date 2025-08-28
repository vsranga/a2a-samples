import os
from any_agent import AgentConfig, AnyAgent, AgentFramework
from pathlib import Path
from httpx import AsyncClient

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


def ollama_test():
    if os.getenv("IN_PYTEST") == "1":
        # Don't need to worry about this when running locally.
        # We use this for out automated testing https://github.com/mozilla-ai/any-agent/blob/main/.github/workflows/tests-cookbook.yaml
        # HF_ENDPOINT points to a Qwen/Qwen3-1.7B running in https://endpoints.huggingface.co/
        # See https://docs.litellm.ai/docs/providers/huggingface#dedicated-inference-endpoints for more info.
        model_id = "huggingface/tgi"
        model_args = {"api_base": os.environ["HF_ENDPOINT"]}
    else:
        model_id = "ollama/granite3.3"
        model_args = {"num_ctx": 32000}


    agent = AnyAgent.create(
        AgentFramework.TINYAGENT,
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
    print(agent_trace.final_output)

if __name__ == "__main__":
    ollama_test()
