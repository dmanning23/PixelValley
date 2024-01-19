import json
from Interactions.conversation import Dialogue
from Interactions.conversation import Conversation
from openai import OpenAI
from py_linq import *

class ConversationGenerator():

    continueCurrentTaskFunctionDef = {
        'name': 'continue_current_task',
        'description': "Continuing the current task is more important than initiating a conversation.",
        'parameters': {
        }
    }

    initiateConversationFunctionDef = {
        'name': 'initiate_conversation',
        'description': 'Choose to start a conversation with one or more characters',
        'parameters': {
            "type": "object",
            "properties": {
                "characters": {
                    'type': 'array',
                    "description": "A list of people who I want to include in the conversation",
                    "items": {
                        "type": "object",
                        "description": "A person I want to talk to",
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'Name of the character I want to talk to'
                            },
                        },
                    "required": ["name"]
                    },
                },
            },
            "required": ["characters"]
        }
    }

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

    def _continue_current_task(self, agents):
        return None
    
    def _initiate_conversation(self, agents, conversationAgents):
        #Create a list of agents
        agentsList = Enumerable(agents)
        chosenAgents = []
        for conversationAgent in conversationAgents:
            #Find the agent with that name
            chosenAgent = self._addAgentToConversation(agentsList, **conversationAgent)
            if chosenAgent is not None:
                chosenAgents.append(chosenAgent)
        return chosenAgents

    def _addAgentToConversation(self, agentsList, name):
        chosenAgent = agentsList.first_or_default(lambda x: x.name == name)
        return chosenAgent

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
        elif response_message.tool_calls and response_message.tool_calls[0].function.arguments:
            function_called = response_message.tool_calls[0].function.name
            function_args  = json.loads(response_message.tool_calls[0].function.arguments)
            function_to_call = available_functions[function_called]
            return function_to_call(agents, *list(function_args.values()))
        else:
            #The LLM didn't call a function but provided a response
            #return response_message.content
            return None
        
    def StartConversation(self, scenario, agent, agentPlannedActivity, availableAgents, agentMemories, llm = None):
        if not llm:
            #create the client API
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f'It is {scenario.currentDateTime}. {agent.name}\'s current task is {agentPlannedActivity.description}. The following is a list of nearby characters and relevant memories about each character. Decide whether {agent.name} would continue with their current task or initiate a conversation with one or two characters.'},
        ]

        for i in range(len(availableAgents)):
            messages.append({'role': 'user', 'content': f"{availableAgents[i].name} is nearby and is currently {availableAgents[i].status}."})
            for memory in agentMemories[i]:
                messages.append({'role': 'user', 'content': f"Relevant memory about {availableAgents[i].name}: {memory}"})
        
        functions = [ ConversationGenerator.continueCurrentTaskFunctionDef,
                     ConversationGenerator.initiateConversationFunctionDef ]
        available_functions = {
            "continue_current_task": self._continue_current_task,
            "initiate_conversation": self._initiate_conversation,
        }
        
        response = llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.3,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        
        conversationAgents = self._parseResponse(availableAgents, response.choices[0].message, available_functions)
        if conversationAgents is not None and len(conversationAgents) >= 1:
            #Make sure the agent is the first item in the results
            conversationAgents.insert(0, agent)
        return conversationAgents

    def CreateConversation(self, scenario, agents, agentPlannedActivities, agentMemories, llm = None):
        if not llm:
            llm = OpenAI()

        messages = [
            {'role': 'system', 'content': f'It is {scenario.currentDateTime}. {agents[0].name} has decided to initiate a conversation. Given the following list of characters in the conversation and relevant context of memories from each character, generate a conversation between them.'},
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
        
        conversation = self._parseResponse(agents, response.choices[0].message, available_functions)
        return conversation