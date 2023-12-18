import json

#This class is for our agents to make long and short term goals
class GoalsStream:

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

    def __init__(self, memoryRepository):
        self.memoryRepository = memoryRepository

    def _generate_characters(self, characters):
        response = []
        for character in characters:
            response.append(self._generate_character(**character))
        return response

    def _generate_character(self, name, age, gender, description):
        #TODO: generate the goals
        # return Agent(name, age, gender, description)
        pass

    def _parseResponse(self, response_message):
        #TODO: clean this up!
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            function_args  = json.loads(response_message.function_call.arguments)
            
            #Create a list of all the available functions
            available_functions = {
                "generate_characters": self._generate_characters,
            }
            
            function_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None

    

    
