import json
from openai import OpenAI

class InteractionGenerator():

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
                'reasoning': {
                    'type': 'string',
                    'description': 'The reason why I would like use this item'
                }
            },
        "required": [ "action", "itemName", "itemStatus", "emoji", "reasoning" ]
        }
    }

    stopUsingItemFunctionDef = {
        'name': 'stop_using_item',
        'description': 'Stop using the current item',
        'parameters': {
            "type": "object",
            "properties": {
                'itemStatus': {
                    'type': 'string',
                    'description': "If the status of the item is changed due to no longer being in use, this will be the item's new status"
                },
                'emoji': {
                    'type': 'string',
                    'description': "An emoji that expresses the item's new status"
                },
                'reasoning': {
                    'type': 'string',
                    'description': 'The reason why I would like to stop using this item'
                }
            },
            "required": [ "itemStatus", "emoji", "reasoning" ]
        },
    }

    continueCurrentTaskFunctionDef = {
        'name': 'continue_current_task',
        'description': "I do not need to use or stop using any items to continue the current task.",
        'parameters': {
        }
    }

    def _use_item(self, action, itemName, itemStatus, emoji, reasoning):
        #what item is the character trying to use?
        return action, itemName, itemStatus, emoji, reasoning
    
    def _stop_using_item(self, itemStatus, emoji, reasoning):
        #send a message to stop using the current item
        return "Stop using item", None, itemStatus, emoji, reasoning
    
    def _continue_current_task(self):
        #don't make any changes to the agent
        return None, None, None, None, None

    def _parseResponse(self, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None, None, None, None, None

    def UseItem(self, agent, availableItems, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = []
        if agent.usingItem is not None:
            messages.append({'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently using the {agent.usingItem.NameWithStatus()}. Provided is a list of important memories relevant to the planned activity and items that are available for use. Will you choose to do something wih any the available items, stop using the current item, or do nothing?"})
        else:
            messages.append({'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. Provided is a list of important memories relevant to the planned activity and items that are available for use. Will you choose to do something wih any the available items or do nothing?"})

        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"Important memory: {memory}"})

        for item in availableItems:
            messages.append({'role': 'user', 'content': f"Item available for use: {item.NameWithStatus()}: {item.description}"})

        if agent.currentItem is not None:
            messages.append({'role': 'user', 'content': f"You are holding the {agent.currentItem.NameWithStatus()}, and can use it: {agent.currentItem.description}"})
        
        if agent.usingItem is not None:
            messages.append({'role': 'user', 'content': f"You are currently using the {agent.usingItem.NameWithStatus()}, and can continue using it or stop using it: {agent.usingItem.description}"})
        
        #Create the list of function definitions that are available to the LLM
        functions = [
            InteractionGenerator.useItemFunctionDef,
            InteractionGenerator.stopUsingItemFunctionDef,
            InteractionGenerator.continueCurrentTaskFunctionDef,
        ]

        available_functions = {
            "use_item": self._use_item,
            "stop_using_item": self._stop_using_item,
            "continue_current_task": self._continue_current_task
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.6,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(response.choices[0].message, available_functions)