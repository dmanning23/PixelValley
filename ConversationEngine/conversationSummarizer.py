import json
from openai import AsyncOpenAI
from py_linq import *

class ConversationSummarizer():

    ignoreConversationFunctionDef = {
        'name': 'ignore_conversation',
        'description': "The conversation was idle chitchat.",
        'parameters': {
        }
    }

    summarizeConversationFunctionDef = {
        'name': 'summarize_conversation',
        'description': 'Create a list of important facts to remember about a conversation',
        'parameters': {
            "type": "object",
            "properties": {
                "facts": {
                    'type': 'array',
                    "description": "A list of important facts that I should remember",
                    "items": {
                        "type": "object",
                        "description": "An important thing to remember",
                        'properties': {
                            'fact': {
                                'type': 'string',
                                'description': 'Description of the important thing I should remember'
                            },
                        },
                        "required": ["fact"]
                    },
                },
            },
            "required": ["facts"]
        }
    }

    def _ignore_conversation(self):
        return []
    
    def _summarize_conversation(self, facts):
        summary =[]
        for fact in facts:
            summary.append(self._createSummary(**fact))
        return summary
    
    def _createSummary(self, fact):
        return fact

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
        
    async def SummarizeConversation(self, agent, conversation, llm = None):
        if not llm:
            llm = AsyncOpenAI()
        messages = [
            {'role': 'system', 'content': f"You are {agent.name}. From your point of view, are there any important facts you should remember from the following conversation?"},
        ]

        for dialogue in conversation.dialogue:
            messages.append({'role': 'user', 'content': f"{dialogue}"})

        functions = [ ConversationSummarizer.ignoreConversationFunctionDef,
                     ConversationSummarizer.summarizeConversationFunctionDef ]
        available_functions = {
            "summarize_conversation": self._summarize_conversation,
            "ignore_conversation": self._ignore_conversation
        }

        response = await llm.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature=0.3,
            messages = messages,
            functions = functions, #Pass in the list of functions available to the LLM
            function_call = 'auto')
        
        conversation = self._parseResponse(response.choices[0].message, available_functions)
        return conversation