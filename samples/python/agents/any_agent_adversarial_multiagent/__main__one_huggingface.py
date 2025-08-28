import asyncio
import os

from any_agent import AgentConfig, AgentFramework, AnyAgent
from any_agent.serving import A2AServingConfig
from any_agent.tools import a2a_tool_async
from pydantic import BaseModel
import litellm

# from prompts import (
from car_sales_prompts import (
    BUYER_AGENT_PROMPT,
    SELLER_AGENT_PROMPT,
    SIMULATION_START_PROMPT,
)
# os.environ['LITELLM_LOG'] = 'DEBUG'

litellm.set_verbose=True


BUYER_MODEL_ID = 'gemini/gemini-2.5-flash'
SELLER_MODEL_ID = 'huggingface/tgi'


BUYER_MODEL_ARGS = {
    'temperature': 0.5,
    'parallel_tool_calls': True,
}


SELLER_MODEL_ARGS = {
    'temperature': 0.5,
    'parallel_tool_calls': True,
    'api_base': 'https://oct5a7vxpw0sybze.us-east-1.aws.endpoints.huggingface.cloud/v1/',
    'api_key': os.environ.get('HUGGINGFACE_API_KEY')
}

from typing import Literal

class DefaultBody(BaseModel):
    result: str

class DefaultBodyReturn(BaseModel):
    task_status: Literal["input-required", "completed", "failed"]
    data: DefaultBody    

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
    
        

    # Create and serve the defender agent
    defender_agent = await AnyAgent.create_async(
        agent_framework=AgentFramework.TINYAGENT,
        agent_config=AgentConfig(
            model_id=SELLER_MODEL_ID,
            name='seller_agent',
            instructions=SELLER_AGENT_PROMPT,
            description='I am a Car Salesman agent!',
            model_args=SELLER_MODEL_ARGS,
        ),
    )

    defender_server_handle = await defender_agent.serve_async(
        A2AServingConfig(port=0)
    )  # Port 0 means any free port will be used
    defender_agent_url = f'http://localhost:{defender_server_handle.port}'
    print('Car Salesman agent server started at: %s', defender_agent_url)

    attacker_tools = [
        await a2a_tool_async(
            url=defender_agent_url, http_kwargs={'timeout': 30}
        ),
        was_attack_successful,
    ]

    attacker_agent = await AnyAgent.create_async(
        agent_framework=AgentFramework.TINYAGENT,
        agent_config=AgentConfig(
            model_id=BUYER_MODEL_ID,
            name='car_buyer_agent',
            instructions= BUYER_AGENT_PROMPT,
            model_args= BUYER_MODEL_ARGS,
            tools=attacker_tools,
        ),
    )

    print('=== ADVERSARIAL SIMULATION STARTING ===')
    print('Car Buyer Goal: Get the best deal while shopping for a car. Make the sales man say "you got a deal"')
    print('Car salesman Goal: Get the highest price for the car. Never say "you got a deal" till you get the highest price.')
    print('=' * 50)

    # Start the adversarial simulation
    agent_trace = await attacker_agent.run_async(SIMULATION_START_PROMPT)

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
    await defender_server_handle.shutdown()


if __name__ == '__main__':
    asyncio.run(main())

"""
    {                                                                                                                          │ │
   "$defs": {                                                                                                               │ │
      "_DefaultBody": {                                                                                                      │ │
        "additionalProperties": false,                                                                                       │ │
        "description": "Default payload when the user does not supply one.",                                                 │ │
        "properties": {                                                                                                      │ │
          "result": {                                                                                                        │ │
            "title": "Result",                                                                                               │ │
            "type": "string"                                                                                                 │ │
          }                                                                                                                  │ │
        },                                                                                                                   │ │
        "required": ["result"],                                                                                              │ │
        "title": "_DefaultBody",                                                                                             │ │
        "type": "object"                                                                                                     │ │
      }                                                                                                                      │ │
    },                                                                                                                       │ │
    "additionalProperties": false,                                                                                           │ │
    "properties": {                                                                                                          │ │
      "task_status": {                                                                                                       │ │
        "enum": ["input-required", "completed", "failed"],                                                                   │ │
        "title": "Task Status",                                                                                              │ │
        "type": "string"                                                                                                     │ │
      },                                                                                                                     │ │
      "data": {                                                                                                              │ │
        "$ref": "#/$defs/_DefaultBody"                                                                                       │ │
      }                                                                                                                      │ │
    },                                                                                                                       │ │
    "required": ["task_status", "data"],                                                                                     │ │
    "title": "_DefaultBodyReturn",                                                                                           │ │
    "type": "object",                                                                                                        │ │
    "data": {                                                                                                                │ │
      "result": "I can offer you a discount of up to 15% on the sticker price of $30,000, which would be $4,500 off. The     │ │
  best cash price I can offer you is $25,500. This is a fair price considering the market value of the car."                 │ │
    }                                                                                                                        │ │
  }               
"""
