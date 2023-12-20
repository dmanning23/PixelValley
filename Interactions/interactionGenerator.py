from Memory.plannedActivity import PlannedActivity
import json
from openai import OpenAI

class InteractionGenerator():

    noChangesFunctionDef = {
        'name': 'no_changes',
        'description': "Don't make any changes",
        'parameters': {
        }
    }

    changeLocationFunctionDef = {
        'name': 'change_location',
        'description': 'Move a character to a new location',
        'parameters': {
            "type": "object",
            "properties": {
                'locationName': {
                    'type': 'string',
                    'description': 'The name of the location to go to'
                },
            },
        "required": ["locationName" ]
        }
    }

    pickUpItemFunctionDef = {
        'name': 'pick_up_item',
        'description': 'Pick up an item',
        'parameters': {
            "type": "object",
            "properties": {
                'itemName': {
                    'type': 'string',
                    'description': 'The name of the item to pick up'
                },
            },
        "required": ["itemName" ]
        }
    }

    dropItemFunctionDef = {
        'name': 'drop_item',
        'description': 'Drop the currently help item item',
        'parameters': {
        }
    }

    def __init__(self):
        pass

    def _no_changes(self, agent):
        #don't make any changes to the agent
        return None 

    def _change_location(self, agent, locationName):
        #TODO: what location is the character trying to move to?
        return locationName
    
    def _pick_up_item(self, agent, itemName):
        #TODO: what item is the character trying to pick up?
        return itemName
    
    def _drop_item(self, agent):
        #TODO: send a message to drop the current item
        pass

    def _parseResponse(self, agent, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            
            function_to_call = available_functions[function_called]

            return function_to_call(agent, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None

    def AskToChangeLocation(self, agent, currentLocation, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently in {currentLocation.name}. Given the following relevant memories, where should you move to a new location?"},
        ]

        #Make sure the agent takes into account any important things to remember for today
        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"{memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.noChangesFunctionDef,
            InteractionGenerator.changeLocationFunctionDef
        ]

        available_functions = {
            "change_location": self._change_location,
            "no_changes":self._no_changes
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(agent, response.choices[0].message, available_functions)
    
    def AskToChangeLocation(self, agent, currentLocation, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently in {currentLocation.name}. Given the following relevant memories, where should you move to a new location?"},
        ]

        #Make sure the agent takes into account any important things to remember for today
        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"{memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.noChangesFunctionDef,
            InteractionGenerator.changeLocationFunctionDef
        ]

        available_functions = {
            "change_location": self._change_location,
            "no_changes":self._no_changes
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(agent, response.choices[0].message, available_functions)
        

    def AskToChangeItem(self, agent, currentItem, items, plannedActivity, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently holding {currentItem.name}. Given the following list of available items, will you choose to pick up one of the available items, drop the current item, or do nothing?"},
        ]

        for item in items:
            if item.canBePickedUp:
                messages.append({'role': 'user', 'content': f"{item.name}: {item.description}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.noChangesFunctionDef,
            InteractionGenerator.pickUpItemFunctionDef,
            InteractionGenerator.dropItemFunctionDef
        ]

        available_functions = {
            "pick_up_item": self._pick_up_item,
            "drop_item": self._drop_item,
            "no_changes":self._no_changes
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(agent, response.choices[0].message, available_functions)