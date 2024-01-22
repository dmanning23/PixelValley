import json
from Interactions.conversationModel import DialogueModel
from Interactions.conversationModel import ConversationModel
from openai import OpenAI
from py_linq import *

class ConversationGenerator():

    createConversationFunctionDef = {
        'name': 'create_conversation',
        'description': 'Create a conversation',
        'parameters': {
            "type": "object",
            "properties": {
                "conversation": {
                    'type': 'array',
                    "description": "A back and forth conversation between several characters",
                    "items": {
                        "type": "object",
                        "description": "A line of dialogue from the conversation",
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Name of the character who is talking'
                            },
                            'dialogue': {
                                'type': 'string',
                                'description': "The text of the dialogue"
                            },
                        },
                        "required": ["name", "dialogue"]
                    },
                },
                "summary":{
                    'type': 'string',
                    'description': "A short summary of the conversation"
                },
            },
            "required": ["conversation", "summary"]
        }
    }

    def _create_conversation(self, conversationModel, conversation, summary):
        #create the conversation text
        dialogues = []
        for text in conversation:
            dialogues.append(self._generate_dialogue(**text))

        #update the conversation object
        conversationModel.dialogue = dialogues
        conversationModel.summary = summary
        return conversationModel

    def _generate_dialogue(self, name, dialogue):
        return DialogueModel(agentName=name, text=dialogue)
    
    def _parseResponse(self, agents, response_message, available_functions):
        if response_message.tool_calls and response_message.tool_calls[0].function.arguments:
            function_called = response_message.tool_calls[0].function.name
            function_args  = json.loads(response_message.tool_calls[0].function.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(agents, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
        
    def CreateConversation(self, scenario, conversationModel, agents, agentPlannedActivities, agentMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f'It is {scenario.currentDateTime}. {agents[0].name} has decided to initiate a conversation. {conversationModel.reasoning} Given the following list of characters in the conversation and relevant context of memories from each character, generate a conversation between them.'},
        ]

        for i in range(len(agents)):
            messages.append({'role': 'system', 'content': f"{agents[i].name} is currently {agents[i].status} and is part of the conversation."})
            messages.append({'role': 'user', 'content': f"{agents[i].name}'s current task is {agentPlannedActivities[i].description}."})

            for memory in agentMemories[i]:
                messages.append({'role': 'user', 'content': f"{agents[i].name} memory: {memory}"})

        functions = [ 
            { "type": "function", "function": ConversationGenerator.createConversationFunctionDef }
        ]
        available_functions = {
            "create_conversation": self._create_conversation,
        }
        
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.3,
            messages = messages,
            tool_choice={"type": "function", "function": {"name": "create_conversation"}},
            tools = functions)
        
        conversation = self._parseResponse(conversationModel, response.choices[0].message, available_functions)
        return conversation