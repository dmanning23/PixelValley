from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI
import json
from Simulation.agent import Agent
from Simulation.scenario import Scenario
from openai import OpenAI
from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.chat_models import ChatOpenAI

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

    def _parseResponse(self, response_message):
        if response_message.function_call and response_message.function_call.arguments:
            #Which function call was invoked?
            function_called = response_message.function_call.name
            
            #Extract the arguments from the AI payload
            function_args  = json.loads(response_message.function_call.arguments)
            
            #Create a list of all the available functions
            available_functions = {
                "generate_characters": self._generate_characters,
            }
            
            fuction_to_call = available_functions[function_called]

            #Call the function with the provided arguments
            return fuction_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None

    def Generate(self, description, llm = None):
        if llm is None:
            llm = ChatOpenAI()
        messages = [
            SystemMessage(content="Expand the following description of an item."),
            HumanMessage(content=description),]
        result = llm.invoke(messages)
        return result.content
    
    def GenerateCharacters(self, scenario, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': "Given the following name and description of a location, generate a list of characters that could be found in that scenario."},
            {'role': 'user', 'content': f"{scenario.name}: {scenario.description}"}
        ]

        #Create the list of function definitions that are available to the LLM
        functions = [ AgentGenerator.generateCharactersFunctionDef ]

        #Call the LLM...
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.2,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        items = self._parseResponse(response.choices[0].message)
        if items is None:
            return [] #if it gets here, there was a problem with the description
        else:
            return items