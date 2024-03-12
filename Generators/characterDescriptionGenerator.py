import json
from openai import AsyncOpenAI
from py_linq import *
from Models.agentDescriptionModel import AgentDescriptionModel

class CharacterDescriptionGenerator():

    describeCharacterFunctionDef = {
        'name': 'describe_character',
        'description': 'Create a list of physical characteristics of a character',
        'parameters': {
            "type": "object",
            "properties": {
                'hair': {
                    'type': 'string',
                    'description': "A description of the character's hair color and style"
                },
                'eyes': {
                    'type': 'string',
                    'description': "A description of the character's eyes"
                },
                "clothing": {
                    'type': 'array',
                    "description": "A list of clothing worn by the character",
                    "items": {
                        "type": "object",
                        "description": "A single item of clothing",
                        'properties': {
                            'characteristic': {
                                'type': 'string',
                                'description': 'Description of a single item of clothing'
                            },
                        },
                        "required": ["description"]
                    },
                },
                "distinguishing_features": {
                    'type': 'array',
                    "description": "A list of distinguishing features",
                    "items": {
                        "type": "object",
                        "description": "A single distinguishing feature",
                        'properties': {
                            'characteristic': {
                                'type': 'string',
                                'description': 'Description of a single distinguishing feature'
                            },
                        },
                        "required": ["description"]
                    },
                },
            },
            "required": ["hair", "eyes", "clothing", "distinguishing_features"]
        }
    }
    
    def _describe_character(self, hair, eyes, clothing, distinguishing_features):
        model = AgentDescriptionModel(hair=hair, eyes=eyes)
        for characteristic in clothing:
            model.clothing.append(self._returnString(**characteristic))
        for characteristic in distinguishing_features:
            model.distinguishingFeatures.append(self._returnString(**characteristic))
        return model
    
    def _returnString(self, characteristic):
        return characteristic

    def _parseResponse(self, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(*list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
        
    async def DescribeCharacter(self, agent, llm = None):
        if not llm:
            llm = AsyncOpenAI()
        messages = [
            {'role': 'system', 'content': f"Extrapolate the physical appearance of the following character."},
            {'role': 'system', 'content': f"Answer the following questions: What do they look like? What color is their hair? What color are their eyes? What are they wearing? Do they have any distinguishing features? etc."}, 
            {'role': 'system', 'content': f"If any of those questions cannot be answered, make something up."},
            {'role': 'user', 'content': f"{agent.name} is a {agent.age} year old {agent.gender}"},
            {'role': 'user', 'content': f"{agent.description}"},
        ]

        functions = [ 
            CharacterDescriptionGenerator.describeCharacterFunctionDef
        ]
        available_functions = {
            "describe_character": self._describe_character
        }

        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=1.4,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        
        descriptions = self._parseResponse(response.choices[0].message, available_functions)
        return descriptions