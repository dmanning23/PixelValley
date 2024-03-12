import json
from openai import AsyncOpenAI

class StatusGenerator():

    noChangesFunctionDef = {
        'name': 'no_changes',
        'description': "Don't make any changes",
        'parameters': {
        }
    }
    setStatusFunctionDef = {
        'name': 'set_status',
        'description': "Set a character's status",
        'parameters': {
            "type": "object",
            "properties": {
                'status': {
                    'type': 'string',
                    'description': "The character's new status"
                },
                'emoji': {
                    'type': 'string',
                    'description': "An emoji that expresses the status"
                },
            },
        "required": ["status", "emoji" ]
        }
    }

    def _no_changes(self, agent):
        #don't make any changes to the agent
        return None, None
    
    def _set_status(self, status, emoji=None):
        return status, emoji

    def _parseResponse(self, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None, None

    async def SetStatus(self, scenario, agent, currentItem, usingItem, currentLocation, plannedActivity, llm = None):
        if not llm:
            llm = AsyncOpenAI()

        messages = [
            {'role': 'system', 'content': f"Given the following sitution, set your status to an appropriate message."},
            {'role': 'user', 'content': f"The current date and time are {scenario.currentDateTime}"},
            {'role': 'user', 'content': f"You are {agent.name}"},
            {'role': 'user', 'content': f"Your current status message is {agent.status}"},
            {'role': 'user', 'content': f"Your current emoji is {agent.emoji}"},
            {'role': 'user', 'content': f"You are currently {plannedActivity.description}"},
            {'role': 'user', 'content': f"You are in the {currentLocation.name}"},
        ]

        if currentItem is not None:
            messages.append({'role': 'user', 'content': f"You have a {currentItem.name}"})
        if usingItem is not None:
            messages.append({'role': 'user', 'content': f"You are using the {usingItem.name}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            StatusGenerator.noChangesFunctionDef,
            StatusGenerator.setStatusFunctionDef,
        ]

        available_functions = {
            "set_status": self._set_status,
            "no_changes":self._no_changes
        }

        #Call the LLM...
        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.65,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(response.choices[0].message, available_functions)