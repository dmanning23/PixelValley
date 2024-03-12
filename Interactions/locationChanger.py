import json
from openai import AsyncOpenAI

class LocationChanger():

    ChooseLocationFunctionDef = {
        'name': 'choose_location',
        'description': 'Choose the best location for the current task',
        'parameters': {
            "type": "object",
            "properties": {
                'locationName': {
                    'type': 'string',
                    'description': 'The name of the location'
                },
                'reasoning': {
                    'type': 'string',
                    'description': 'The reason why this location is best for the current task, written in first person perspective'
                },
            },
        "required": ["locationName", "reasoning" ]
        }
    }

    def _choose_location(self, locationName, reasoning):
        #what location is the character trying to move to?
        return locationName, reasoning

    def _parseResponse(self, response_message, available_functions):
        if response_message.tool_calls and response_message.tool_calls[0].function.arguments:
            function_called = response_message.tool_calls[0].function.name
            function_args  = json.loads(response_message.tool_calls[0].function.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None, None

    async def AskToChangeLocation(self, agent, currentLocation, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = AsyncOpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and your current task is {plannedActivity.description}. You are currently in {currentLocation.name}. Given the following relevant memories, where is the best location to continue your task and why?"},
        ]

        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"{memory}"})

        functions = [ 
            { "type": "function", "function": LocationChanger.ChooseLocationFunctionDef }
        ]
        
        available_functions = {
            "choose_location": self._choose_location,
        }
        
        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            tool_choice={"type": "function", "function": {"name": "choose_location"}},
            tools = functions)
        
        return self._parseResponse(response.choices[0].message, available_functions)