"""
Bob-Omb Agent Example

This example demonstrates how to create a LangChain agent that can spawn Bob-Ombs
in the Super Smash Bros game using custom tools.
"""

import json
import os

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from dotenv import load_dotenv
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain_community.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field


# Load environment variables
load_dotenv()

# Initialize OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"


class BobombInput(BaseModel):
    position_x: int = Field(default=300, description="X position of the Bob-omb")
    position_y: int = Field(default=100, description="Y position of the Bob-omb")
    fuse_time: int = Field(default=180, description="Time before the Bob-omb explodes")
    damage: int = Field(default=25, description="Damage caused by the explosion")
    explosion_radius: int = Field(default=100, description="Radius of the explosion")

def create_bobomb(position_x=300, position_y=100, fuse_time=180, damage=25, explosion_radius=100):
    """
    Creates a Bob-Omb entity in the game at the specified position with custom properties.
    
    Args:
        position_x (int): X coordinate for Bob-Omb spawn
        position_y (int): Y coordinate for Bob-Omb spawn
        fuse_time (int): Time in frames until explosion
        damage (int): Damage dealt by explosion
        explosion_radius (int): Radius of explosion effect
    
    Returns:
        dict: Information about the created Bob-Omb
    """
    # In a real implementation, this would interact with the game engine
    # Here we're just creating a representation of what would be spawned
    
    bobomb_data = {
        "entity": "bobomb",
        "position": {"x": position_x, "y": position_y},
        "properties": {
            "fuse_time": fuse_time,
            "damage": damage,
            "explosion_radius": explosion_radius
        },
        "status": "spawned"
    }
    
    print(f"Created Bob-Omb at position ({position_x}, {position_y})")
    print(f"Fuse time: {fuse_time} frames, Damage: {damage}, Explosion radius: {explosion_radius}")
    
    return bobomb_data


# Path to the bobomb entity template
BOBOMB_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   "entities", "bobomb_entity.json")

def get_bobomb_template():
    """Retrieves the Bob-Omb entity template from the JSON file."""
    try:
        with open(BOBOMB_TEMPLATE_PATH, 'r') as f:
            data = json.load(f)
            # Extract the template from the entities list
            for entity in data.get("entities", []):
                if entity.get("id") == "bobomb_template":
                    return entity
            return None
    except Exception as e:
        print(f"Error loading Bob-Omb template: {e}")
        return None


# Define the tools for the agent
bobomb_tool = StructuredTool.from_function(
    func=create_bobomb,
    name="CreateBobomb",
    description="Create a Bob-omb with specific position, fuse time, damage, and explosion radius.",
    args_schema=BobombInput
)

tools=[bobomb_tool]

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-1106")
system_prompt = SystemMessage(
    content=(
        "You are an AI assistant that helps manage items in a Super Smash Bros game. "
        "You can spawn Bob-Ombs at specific locations with custom properties such as fuse time, damage, and explosion radius."
    )
)

prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])


# agent = initialize_agent(
#     tools=[bobomb_tool],
#     llm=llm,
#     agent=AgentType.OPENAI_FUNCTIONS,
#     verbose=True
# )
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# # Create a prompt template for the agent
# prompt = PromptTemplate.from_template(
#     """You are an AI assistant that helps manage items in a Super Smash Bros game.
#     You can spawn Bob-Ombs at specific locations with custom properties.
    
#     {input}
#     """
# )

# # Create the agent
# agent = create_react_agent(llm, tools, prompt)

# # Create the agent executor
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# # Example usage
if __name__ == "__main__":

    # response = agent_executor.invoke("Create a Bob-omb at position 500, 250 with a short fuse of 60 seconds and radius of 200.")
    # print(response)

    # Example 1: Basic Bob-Omb spawning
    result1 = agent_executor.invoke(
        {"input": "Create a Bob-Omb at position (400, 200) with default properties"}
    )
    print("\nResult 1:", result1["output"])
    
    # Example 2: Custom Bob-Omb with specific properties
    result2 = agent_executor.invoke(
        {"input": "Spawn a powerful Bob-Omb at coordinates (250, 150) with "
                 "fuse time 120 frames, damage 40, and explosion radius 150"}
    )
    print("\nResult 2:", result2["output"])
    
    # Example 3: Multiple Bob-Ombs in sequence
    result3 = agent_executor.invoke(
        {"input": "Create 3 Bob-Ombs: one at (300, 100), another at (400, 100), "
                 "and a third at (500, 100). Each should have the default properties."}
    )
    print("\nResult 3:", result3["output"]) 