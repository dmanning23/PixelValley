import json
from openai import OpenAI

class ActionGenerator():

    createActionsFunctionDef = {
        'name': 'create_actions',
        'description': 'Create a list of actions',
        'parameters': {
            "type": "object",
            "properties": {
                "actions": {
                    'type': 'array',
                    "description": "A list of actions",
                    "items": {
                        "type": "object",
                        "description": "A single action",
                        'properties': {
                            'verb': {
                                'type': 'string',
                                "enum": [
                                    "go to",
                                    "pick up",
                                    "take",
                                    "drop",
                                    "eat",
                                    "use",
                                    "talk to",
                                    "sleep",
                                    "wake up",
                                    "greet",
                                    "attack",
                                ],
                                'description': 'The verb of the action to perform. Must be selected from the list of possible actions!'
                            },
                            'item': {
                                'type': 'string',
                                'description': "The person, place, or thing that is the target of the action"
                            },
                        },
                        "required": ["verb"]
                    },
                },
            },
            "required": ["actions",]
        }
    }

    def _create_actions(self, actions):
        response = []
        for action in actions:
            response.append(self._create_action(**action))
        return response

    def _create_action(self, verb, target = None):
        #TODO: create an action?
        #return Item(name, description, hasFiniteStateMachine, canBePickedUp)
        pass

    def _parseResponse(self, agent, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            
            function_to_call = available_functions[function_called]

            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None

    def CreateActions(self, dateTime, agent, currentLocation, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f"The current date and time is {dateTime}. You are {agent.name} and you are currently trying to {plannedActivity.description}. You are currently in {currentLocation.name}. Given the following relevant memories, create a list of actions to complete your current planned activity."},
        ]

        #Make sure the agent takes into account any important things to remember for today
        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"{memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [
            ActionGenerator.createActionsFunctionDef
        ]
        available_functions = {
            "create_actions":self._create_actions
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        return self._parseResponse(agent, response.choices[0].message, available_functions)

    def BreakDownPlannedActivity(self, agent, plannedActivity, importantMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following itinerary item and a list of important things to remember about it, break it down into a list of detailed activities."},
            {'role': 'user', 'content': f"Planned activity: {plannedActivity}"}
        ]

        for memory in importantMemories:
            messages.append({'role': 'user', 'content': f"Important thing to remember: {memory}"})

        #Create the list of function definitions that are available to the LLM
        functions = [ ActionGenerator.createActionsFunctionDef ]
        available_functions = {
            "create_actions":self._create_actions
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.5,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        plannedActivities = self._parseResponse(agent, response.choices[0].message, available_functions)
        if plannedActivities is None:
            plannedActivities = []
        return plannedActivities