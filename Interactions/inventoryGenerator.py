import json
from openai import OpenAI

class InventoryGenerator():

    continueCurrentTaskFunctionDef = {
        'name': 'continue_current_task',
        'description': "I do not need to pick up or drop any items to continue the current task.",
        'parameters': {
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
                'reasoning': {
                    'type': 'string',
                    'description': 'The reason why I would like to pick up this item'
                }
            },
        "required": ["itemName", "reasoning" ]
        }
    }

    dropItemFunctionDef = {
        'name': 'drop_item',
        'description': 'Drop the currently help item',
        'parameters': {
            "type": "object",
            "properties": {
                'reasoning': {
                    'type': 'string',
                    'description': 'The reason why I would like to drop this item'
                }
            },
        "required": [ "reasoning" ]
        }
    }

    def _continue_current_task(self):
        #don't make any changes to the agent
        return None, None
    
    def _pick_up_item(self, itemName, reasoning):
        #what item is the character trying to pick up?
        return itemName, reasoning
    
    def _drop_item(self, reasoning):
        #send a message to drop the current item
        return "Drop current item", reasoning

    def _parseResponse(self, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None, None

    def ManageInventory(self, agent, currentItem, pickableItems, plannedActivity, llm = None):
        if not llm:
            llm = OpenAI()

        #TODO: update this to take a list of enums for possible actions
            
        #TODO: add important memories to this call?

        messages = []
        if currentItem is None:
            messages.append({'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. Given the following list of available items, will you choose to pick up one of the available items, or do nothing?"})
        else:
            messages.append({'role': 'system', 'content': f"You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently holding {currentItem.name}. You can only hold one item at a time. Given the following list of available items, will you choose to pick up one of the available items, drop the current item, or do nothing?"})

        for item in pickableItems:
            messages.append({'role': 'user', 'content': f"{item.name}: {item.description}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            InventoryGenerator.continueCurrentTaskFunctionDef,
            InventoryGenerator.pickUpItemFunctionDef,
            InventoryGenerator.dropItemFunctionDef
        ]

        available_functions = {
            "continue_current_task": self._continue_current_task,
            "drop_item": self._drop_item,
            "pick_up_item":self._pick_up_item
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.6,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(response.choices[0].message, available_functions)