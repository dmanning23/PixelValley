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
        'description': 'Drop the currently help item',
        'parameters': {
        }
    }

    useItemFunctionDef = {
        'name': 'use_item',
        'description': 'Use an item',
        'parameters': {
            "type": "object",
            "properties": {
                'itemName': {
                    'type': 'string',
                    'description': 'The name of the item to use'
                },
            },
        "required": ["itemName" ]
        }
    }

    stopUsingItemFunctionDef = {
        'name': 'stop_using_item',
        'description': 'Stop using the current item',
        'parameters': {
        }
    }

    itemActionFunctionDef = {
        'name': 'item_action',
        'description': 'Use an item',
        'parameters': {
            "type": "object",
            "properties": {
                'action': {
                    'type': 'string',
                    'description': 'The action to perform on the item'
                },
            },
        "required": ["action" ]
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

    def _use_item(self, agent, itemName):
        #TODO: what item is the character trying to use?
        return itemName
    
    def _stop_using_item(self, agent):
        #TODO: send a message to stop using the current item
        pass

    def _item_action(self, agent, actionName):
        #TODO: what action is the agent trying to perform?
        return actionName

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
    
    def AskToUseItem(self, agent, currentItem, items, plannedActivity, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently using the {currentItem.name}. Given the following list of available items, will you choose to use one of the available items, stop using the current item, or do nothing?"},
        ]

        if currentItem.canInteract:
            messages.append({'role': 'user', 'content': f"{item.name}: {item.description}"})

        for item in items:
            if item.canInteract:
                messages.append({'role': 'user', 'content': f"{item.name}: {item.description}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.noChangesFunctionDef,
            InteractionGenerator.useItemFunctionDef,
            InteractionGenerator.stopUsingItemFunctionDef
        ]

        available_functions = {
            "use_item": self._use_item,
            "stop_using_item": self._stop_using_item,
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
    
    def PerformItemAction(self, agent, currentItem, plannedActivity, memories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You have decided to use the {currentItem.name}. Given the following list of knwoledge items that you know about the {currentItem.name}, what action will you perform on the item?"},
        ]

        for memory in memories:
            messages.append({'role': 'user', 'content': f"{memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.noChangesFunctionDef,
            InteractionGenerator.itemActionFunctionDef,
        ]

        available_functions = {
            "item_action": self._item_action,
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