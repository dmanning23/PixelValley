import json
from Interactions.conversation import Dialogue
from Interactions.conversation import Conversation
from openai import OpenAI
from py_linq import *

class ConversationGenerator():

    createConversationFunctionDef = {
        'name': 'create_conversation',
        'description': 'Create a conversation between two or more characters',
        'parameters': {
            "type": "object",
            "properties": {
                "conversation": {
                    'type': 'array',
                    "description": "A back and forth conversation between two or more characters",
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

    def _create_conversation(self, agents, conversation, summary):
        #create the conversation text
        dialogues = []
        for text in conversation:
            dialogues.append(self._generate_dialogue(**text))

        agentIds = Enumerable(agents).select(lambda x: x._id).to_list()
        #create the conversation object
        return Conversation(agents=agentIds, summary=summary, dialogue=dialogues)

    def _generate_dialogue(self, name, dialogue):
        return Dialogue(agentName=name, text=dialogue)

    def _parseResponse(self, agents, response_message, available_functions):
        if response_message.function_call and response_message.function_call.arguments:
            function_called = response_message.function_call.name
            function_args  = json.loads(response_message.function_call.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(agents, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
    
    def CreateConversation(self, scenario, agent1, agent2, agent1PlannedActivity, agent2PlannedActivity, agent1Memories, agent2Memories, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f'It is {scenario.currentDateTime}. {agent1.name}\'s current task is {agent1PlannedActivity.description}. They have decided to initiate a conversation with {agent2.name}, who is currently {agent2.status}. Given the relevant context of memories from each character, generate a conversation between them.'},
        ]

        for memory in agent1Memories:
            messages.append({'role': 'user', 'content': f"{agent1.name} memory: {memory}"})

        for memory in agent2Memories:
            messages.append({'role': 'user', 'content': f"{agent2.name} memory: {memory}"})

        functions = [ ConversationGenerator.createConversationFunctionDef ]
        available_functions = {
            "create_conversation": self._create_conversation,
        }
        
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.7,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        
        conversation = self._parseResponse(response.choices[0].message, available_functions)
        return conversation
    
    def CreateConversation(self, scenario, agents, agentPlannedActivities, agentMemories, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f'It is {scenario.currentDateTime}. {agents[0].name}\'s current task is {agentPlannedActivities[0].description}. They have decided to initiate a conversation. Given the following list of characters in the conversation and relevant context of memories from each character, generate a conversation between them.'},
        ]

        for i in range(len(agents)):
            messages.append({'role': 'user', 'content': f"{agents[i].name} is currently {agents[i].status} and is part of the conversation."})
            messages.append({'role': 'user', 'content': f"{agents[i].name}'s current task is {agentPlannedActivities[i].description}."})

            for memory in agentMemories[i]:
                messages.append({'role': 'user', 'content': f"{agents[i].name} memory: {memory}"})

        functions = [ ConversationGenerator.createConversationFunctionDef ]
        available_functions = {
            "create_conversation": self._create_conversation,
        }
        
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.6,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        
        conversation = self._parseResponse(agents, response.choices[0].message, available_functions)
        return conversation