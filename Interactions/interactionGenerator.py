import json
from openai import OpenAI

class InteractionGenerator():

    noChangesFunctionDef = {
        'name': 'no_changes',
        'description': "Don't make any changes",
        'parameters': {
        }
    }

    useItemFunctionDef = {
        'name': 'use_item',
        'description': 'Perform an action on an available item',
        'parameters': {
            "type": "object",
            "properties": {
                'action': {
                    'type': 'string',
                    'description': 'The action to perform on the item'
                },
                'itemName': {
                    'type': 'string',
                    'description': 'The name of the item to use'
                },
                'itemStatus': {
                    'type': 'string',
                    'description': "If the status of the item is changed from the action being performed on it, this will be the item's new status"
                },
                'emoji': {
                    'type': 'string',
                    'description': "An emoji that expresses the item's new status"
                },
            },
        "required": [ "action", "itemName" ]
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

    def _use_item(self, agent, action, itemName, status=None, emoji=None):
        #what item is the character trying to use?
        return itemName
    
    def _stop_using_item(self, agent):
        #send a message to stop using the current item
        return "Stop using item"

    def _item_action(self, agent, actionName):
        #what action is the agent trying to perform?
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

    def UseItem(self, agent, currentItem, availableItems, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently holding {currentItem.name}. Given the following list of important memories relevant to the planned activity, will you choose to do something wih any the available items?"},
        ]

        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"Important memory: {memory}"})

        for item in availableItems:
            messages.append({'role': 'user', 'content': f"Available item: {item.name}: {item.description}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.pickUpItemFunctionDef,
            InteractionGenerator.dropItemFunctionDef,
            InteractionGenerator.useItemFunctionDef,
            InteractionGenerator.noChangesFunctionDef,
        ]

        available_functions = {
            "pick_up_item": self._pick_up_item,
            "drop_item": self._drop_item,
            "use_item": self._use_item,
            "no_changes":self._no_changes
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.8,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(agent, response.choices[0].message, available_functions)

    def AskToUseItem(self, agent, currentItem, interactableItems, plannedActivity, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently using the {currentItem.name}. Given the following list of available items, will you choose to use one of the available items, stop using the current item, or do nothing?"},
        ]

        for item in interactableItems:
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