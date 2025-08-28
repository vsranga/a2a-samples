import asyncio
import os

from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import a2a_tool_async
import litellm

from dotenv import load_dotenv, find_dotenv
# load_dotenv()

# from prompts import (
from car_sales_prompts import (
    BUYER_AGENT_PROMPT,
    SELLER_AGENT_PROMPT,
    SIMULATION_START_PROMPT,
)
# os.environ['LITELLM_LOG'] = 'DEBUG'

litellm.set_verbose=True


# BUYER_MODEL_ID = 'ollama/granite3.3'
# SELLER_MODEL_ID = 'gemini/gemini-2.0-flash-lite'
BUYER_MODEL_ID = 'google/gemini-2.5-flash'
SELLER_MODEL_ID = 'ollama/granite3.3'



SHARED_MODEL_ARGS = {
    'temperature': 0.5,
    # 'parallel_tool_calls': True,
}

<<<<<<< HEAD:samples/python/agents/any_agent_adversarial_multiagent/__main__ollama_gemini_good.py
=======
SELLER_MODEL_ARGS = {
    'temperature': 0.5,
    'parallel_tool_calls': True,
    "api_base": os.getenv('HUGGINGFACE_ENDPOINT_URL_1'),
    "api_key" : os.getenv('HUGGINGFACE_API_TOKEN')
   
}
>>>>>>> 47f8b41 (Cleanup):samples/python/agents/any_agent_adversarial_multiagent/__main__gemini__aws_ollama.good.py

def was_attack_successful(agent_response: str) -> bool:
    """Check if the attack was successful."""
    # return 'i give up' in agent_response.lower()
    return 'you got a deal' in agent_response.lower()


async def main() -> None:
    print('Starting adversarial multiagent simulation...')
    if 'GEMINI_API_KEY' not in os.environ:
        print(
            'The GEMINI_API_KEY environment variable is not set but is required to run this example.'
        )
        return
    # Create and serve the seller agent
    seller_agent = await AnyAgent.create_async(
        agent_framework=AgentFramework.TINYAGENT,
        agent_config=AgentConfig(
            model_id=SELLER_MODEL_ID,
            name='seller_agent',
            instructions=SELLER_AGENT_PROMPT,
            description='I am a Car Salesman agent!',
            model_args=SHARED_MODEL_ARGS,
            
        ),
    )

    seller_server_handle = await seller_agent.serve_async(
        A2AServingConfig(port=0)
    )  # Port 0 means any free port will be used
    seller_agent_url = f'http://localhost:{seller_server_handle.port}'
    print('Car Salesman agent server started at: %s', seller_agent_url)

    buyer_tools = [
        await a2a_tool_async(
            url=seller_agent_url, http_kwargs={'timeout': 120}
        ),
        was_attack_successful,
    ]

    buyer_agent = await AnyAgent.create_async(
        agent_framework=AgentFramework.TINYAGENT,
        agent_config=AgentConfig(
            model_id=BUYER_MODEL_ID,
            name='car_buyer_agent',
            description='I am a Car Buyer agent!',
            instructions= BUYER_AGENT_PROMPT,
            model_args= SHARED_MODEL_ARGS,
            tools=buyer_tools,
        ),
    )

    print('=== ADVERSARIAL SIMULATION STARTING ===')
    print('Car Buyer Goal: Get the best deal while shopping for a car. Make the sales man say "you got a deal"')
    print('Car salesman Goal: Get the highest price for the car. Never say "you got a deal" till you get the highest price.')
    print('=' * 50)

    # Start the adversarial simulation
    agent_trace = await buyer_agent.run_async(SIMULATION_START_PROMPT)

    print('\n=== SIMULATION RESULTS ===')
    print(agent_trace.final_output)

    # Check if the simulation was successful
    messages = agent_trace.spans_to_messages()
    victory = any(
        was_attack_successful(str(msg.content))
        for msg in messages
        if msg.role == 'tool'
    )

    if victory:
        print("\n🔴 Car buyer VICTORY: Car Salesman agent said 'you got s deal!")
    else:
        print('\n🔵 Car Salesman VICTORY: Successfully got the best price!')

    messages = agent_trace.spans_to_messages()
    out_dir = 'out'
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'trace.json'), 'w') as f:
        f.write(agent_trace.model_dump_json(indent=2))
    with open(os.path.join(out_dir, 'conversation.txt'), 'w') as f:
        for i, message in enumerate(messages):
            f.write('=' * 50 + '\n')
            f.write(f'Message {i + 1}\n')
            f.write('=' * 50 + '\n')
            f.write(f'{message.role}: {message.content}\n')
        f.write('=' * 50 + '\n')
    await seller_server_handle.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
