import json
from Simulation.agent import Agent
from openai import OpenAI

class AgentGenerator():

    generateCharactersFunctionDef = {
        'name': 'generate_characters',
        'description': 'Create a list of characters',
        'parameters': {
            "type": "object",
            "properties": {
                "characters": {
                    'type': 'array',
                    "description": "A list of characters",
                    "items": {
                        "type": "object",
                        "description": "A single character",
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Name of the character'
                            },
                            'age': {
                                'type': 'integer',
                                'description': "The age of the character"
                            },
                            'gender': {
                                'type': 'string',
                                'description': "The character's chosen gender",
                            },
                            'description': {
                                'type': 'string',
                                'description': "A description of this character, including appearance and personality",
                            },
                        },
                        "required": ["name", "age", "gender", "description"]
                    },
                },
            },
            "required": ["characters",]
        }
    }

    def _generate_characters(self, characters):
        response = []
        for character in characters:
            response.append(self._generate_character(**character))
        return response

    def _generate_character(self, name, age, gender, description):
        return Agent(name, age, gender, description)

    def _parseResponse(self, response_message, available_functions):
        if response_message.tool_calls and response_message.tool_calls[0].function.arguments:
            function_called = response_message.tool_calls[0].function.name
            function_args  = json.loads(response_message.tool_calls[0].function.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None

    def GenerateCharacters(self, scenario, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following name and description of a location, generate a list of 5 or more characters that could be found in that scenario."},
            {'role': 'user', 'content': f"{scenario}"}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ 
            { "type": "function", "function": AgentGenerator.generateCharactersFunctionDef }
        ]
        available_functions = {
            "generate_characters": self._generate_characters,
        }

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.2,
            messages = messages,
            tool_choice={"type": "function", "function": {"name": "generate_characters"}},
            tools = functions)
        items = self._parseResponse(response.choices[0].message, available_functions)
        if items is None:
            return [] #if it gets here, there was a problem with the description
        else:
            return items