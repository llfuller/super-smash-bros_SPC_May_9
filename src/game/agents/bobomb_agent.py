"""
Bob-Omb Agent Example

This example demonstrates how to create a LangChain agent that can spawn Bob-Ombs
in the Super Smash Bros game using custom tools.
"""

from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import os

# Path to the bobomb entity template
BOBOMB_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   "entities", "bobomb_entity.json")

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
tools = [
    Tool(
        name="SpawnBobOmb",
        func=create_bobomb,
        description="Spawns a Bob-Omb in the game. Parameters: position_x (int), position_y (int), "
                    "fuse_time (int), damage (int), explosion_radius (int)"
    )
]

# Create a prompt template for the agent
prompt = PromptTemplate.from_template(
    """You are an AI assistant that helps manage items in a Super Smash Bros game.
    You can spawn Bob-Ombs at specific locations with custom properties.
    
    {input}
    """
)

# Initialize the language model
llm = ChatOpenAI(temperature=0)

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Example usage
if __name__ == "__main__":
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