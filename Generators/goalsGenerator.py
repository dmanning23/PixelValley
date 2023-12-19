import json
from openai import OpenAI
from Memory.goal import Goal

#This class is for our agents to make long and short term goals
class GoalsGenerator:

    createGoalsFunctionDef = {
        'name': 'create_goals',
        'description': 'Create a list of long and short term goals for a character',
        'parameters': {
            "type": "object",
            "properties": {
                "goals": {
                    'type': 'array',
                    "description": "A list of long and short term goals",
                    "items": {
                        "type": "object",
                        "description": "A single long or short term goal",
                        'properties': {
                            'title': {
                                'type': 'string',
                                'description': 'The title of the goal used to identify it'
                            },
                            'timeframe': {
                                'type': 'string',
                                'description': "The time frame of the goal"
                            },
                            'description': {
                                'type': 'string',
                                'description': "A description of this goal",
                            },
                        },
                        "required": ["title", "timeframe", "description"]
                    },
                },
            },
            "required": ["goals",]
        }
    }

    def __init__(self):
        pass

    def _create_goals(self, agent, goals):
        response = []
        for goal in goals:
            response.append(self._create_goal(agent, **goal))
        return response

    def _create_goal(self, agent, title, timeframe, description):
        #generate the goal
        return Goal(agentId=agent._id, title=title, timeframe=timeframe, description=description)

    def _parseResponse(self, agent, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            available_functions = {
                "create_goals": self._create_goals,
            }
            function_to_call = available_functions[function_called]
            return function_to_call(agent, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            return None

    def GenerateGoals(self, agent, scenario, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following description of a character and the scenario they are located in, create a list of long and short term goals for them."},
            {'role': 'user', 'content': f"{agent}"},
            {'role': 'user', 'content': f"{scenario}"}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ GoalsGenerator.createGoalsFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.0,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        goals = self._parseResponse(agent, response.choices[0].message)
        if goals is None:
            goals = []
        return goals