import os
from keys import openAIapikey
from keys import mongoUri
from mongoengine import *
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import (SystemMessage, HumanMessage, AIMessage)
from Repository.agentRepository import AgentRepository
from Memory.memoryRepository import MemoryRepository
from Memory.retrievalStream import RetrievalStream
from langchain.chains import LLMChain
from langchain.prompts import (ChatPromptTemplate, 
                               MessagesPlaceholder, 
                               HumanMessagePromptTemplate)
import asyncio

def InitializeMemory():
    print("resetting memory")
    return ConversationBufferMemory(memory_key="chat_history", return_messages=True)

async def main():
    os.environ["OPENAI_API_KEY"] = openAIapikey
    connect(host=mongoUri, db="pixelValley") #connect for mongoengine

    st.set_page_config(
        page_title="Chat With A Pixel Valleyer",
        page_icon="😺")
    
    if "memory" not in st.session_state:
        st.session_state["memory"]=InitializeMemory()

    chatHistory=st.session_state["memory"]

    #add a button to the sidebar to start a new conversation
    clear_button = st.sidebar.button("New Conversation", key="clear")
    if (clear_button):
        print("Clearing memory")
        chatHistory.clear()

    container = st.container()
    with container:
        with st.form(key="my form", clear_on_submit=True):

            #Choose an agent
            repo = AgentRepository()
            agents = repo.GetAgents("65bbcc69d9e6cf794859d192") #High Elves
            #agents = repo.GetAgents("6580b18f0b38cba6f29e3f88") #Pirate Village
            agent = st.selectbox("Select an agent to chat with:", agents, format_func=lambda x: x.name)
            
            #Get the user input
            user_input  = st.text_area(label="Message: ", key="input", height = 100)

            #Say something to the agent
            submit_button = st.form_submit_button(label="Chat")

        if agent and submit_button and user_input:

            #Get the relevent memories
            memRepo = MemoryRepository()
            retrieval = RetrievalStream(memRepo)
            memories = await retrieval.RetrieveMemories(agent, user_input)

            #Create the system message
            messages = [ SystemMessage(content=f"You are {agent.name}. {agent.description} Given the following relevent memories, continue the next statement in the conversation:") ]
            
            #Add the relevent memories to the chat
            for memory in memories:
                messages.append(SystemMessage(content=f"Relevent memory: {memory.description}" ))

            #Append the chat history
            messages.append(MessagesPlaceholder(variable_name="chat_history"))

            #Add the user's latest statement to the chat
            messages.append(HumanMessagePromptTemplate.from_template("{question}"))

            #Create the llm chain
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.4)
            prompt = ChatPromptTemplate(messages=messages)
            chain = LLMChain(llm=llm, prompt=prompt, memory=chatHistory)

            with st.spinner("Thinking..."):
                question = {'question': user_input}
                response = chain.run(question)
            
            #write the ressponse
            st.subheader(f"Question:\n{user_input}")
            st.subheader(f"Response:\n{response}")

            #write the chat history
            variables = chatHistory.load_memory_variables({})
            messages = variables['chat_history']
            for message in messages:
                if isinstance(message, AIMessage):
                    with st.chat_message('assistant'):
                        st.markdown(message.content)
                elif isinstance(message, HumanMessage):
                    with st.chat_message('user'):
                        st.markdown(message.content)
                else:
                    st.write(f"System message: {message.content}")
    
if __name__ == "__main__":
    asyncio.run(main())