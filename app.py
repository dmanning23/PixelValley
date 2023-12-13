import os
import streamlit as st
from openai import OpenAI
from keys import openAIapikey
from keys import mongoUri
import json
import random
import sys
from mongoengine import *
from Generators.scenarioGenerator import ScenarioGenerator
from Generators.locationGenerator import LocationGenerator
from Generators.itemGenerator import ItemGenerator
from Generators.agentGenerator import AgentGenerator
from Simulation.location import Location
from Simulation.item import Item
from Simulation.scenario import Scenario
from Generators.finiteStateMachineGenerator import FiniteStateMachineGenerator
from Repository.scenarioRepository import ScenarioRepository
from Repository.locationRepository import LocationRepository
from Repository.itemRepository import ItemRepository
from Repository.userAccessRepository import UserAccessRepository

def initializeScenario():
    if "scenario" in st.session_state and st.session_state['scenario'] is not None:
        scenario = st.session_state["scenario"]
        displayScenario(scenario)

    else:
        st.subheader("Select an existing scenario, or create a new one")

        #Get the user's scenarios
        userId = st.session_state["userId"]
        scenarios = ScenarioRepository.GetScenarios(userId)
        if scenarios:
            selectContainer = st.container()
            with selectContainer:
                with st.form(key="select scenario", clear_on_submit=True):
                    selectedScenario  = st.selectbox("Select an existing scenario:", scenarios)
                    select_button = st.form_submit_button(label="Select")
                    if select_button:
                        fetchScenario(userId, selectedScenario._id)

        createContainer = st.container()
        with createContainer:
            with st.form(key="create scenario", clear_on_submit=True):
                user_input  = st.text_area(label="Enter a short description of the scenario: ", key="input", height = 100)
                create_button = st.form_submit_button(label="Create")

                if create_button:
                    if not user_input:
                        user_input = f"A cozy little village"
                    createScenario(userId, user_input)

def fetchScenario(userId, scenarioId):
    
    #load up the scenario
    with st.spinner("Loading scenario..."):
        scenario = ScenarioRepository.Get(userId, scenarioId)

    #load the locations
    with st.spinner("Loading locations..."):
        scenario.locations = LocationRepository.FetchScenario(scenario._id)

    #load the items
    with st.spinner("Loading items..."):
        for location in scenario.locations:
            ItemRepository.FetchLocation(location)

    #TODO: load the agents
    with st.spinner("Loading agents..."):
        pass

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def createScenario(userId, scenarioDescription):
    with st.spinner("Creating scenario..."):
        #expand the setting
        settingGen = ScenarioGenerator()
        scenario = settingGen.Generate(scenarioDescription)

    with st.spinner("Populating locations..."):
        #create the initial list of locations
        locationGen = LocationGenerator()
        scenario.locations = locationGen.Generate(scenario)

        #decompose each location into children if application
        for location in scenario.locations:
            locationGen.GenerateChildLocations(location)

        items = []
        itemGen = ItemGenerator()
        for location in scenario.locations:
            with st.spinner(F"Populating items for {location.name}..."):
                items = items + itemGen.PopulateLocations(location)

    with st.spinner("Reticulating splines..."):
        for item in items:
            itemGen.GenerateFiniteStateMachine(item)

    #TODO: create all the villagers
    with st.spinner("Creating villagers..."):
        pass

    with st.spinner("Saving scenario..."):
        #Store the scenario
        ScenarioRepository.CreateOrUpdate(userId, scenario)

    with st.spinner("Saving locations..."):
        for location in scenario.locations:
            LocationRepository.CreateOrUpdateLocations(location, scenario._id)

    with st.spinner("Saving items..."):
        for location in scenario.locations:
            ItemRepository.CreateOrUpdateFromLocation(location)

    #TODO: save all the villagers
    with st.spinner("Saving villagers..."):
        pass

    #store the scenario
    st.session_state["scenario"] = scenario
    st.rerun()

def displayScenario(scenario):

    #output the user's prompt
    st.markdown(scenario.name)
    st.markdown(scenario.description)

    for location in scenario.locations:
        writeLocation(location)

    #TODO: write out villagers

def writeLocation(location, level = 0):
    #write the location
    st.header(location)

    #write all the items
    st.subheader(f"Items in {location.name}:")
    for item in location.items:
        st.write(item)

    if location.locations:
        level = level + 1
        st.subheader(f"Child locations of {location.name}:")
        for child in location.locations:
            writeLocation(child, level)

def stateMachine():
    #Get the user's input
    container = st.container()
    with container:
        with st.form(key="my form", clear_on_submit=True):
            user_input  = st.text_area(label="Enter a short description of an item: ", key="input", height = 100)
            submit_button = st.form_submit_button(label="Generate")

        client = OpenAI()
        if submit_button:
            if not user_input:
                #If the user doesn't enter any input, use a default prompt
                user_input = f"coffee pot"
                
            with st.spinner("Thinking..."):
                #output the user's prompt
                st.markdown(user_input)

                #expand the state machine
                fsmGenerator = FiniteStateMachineGenerator()
                stateMachine = fsmGenerator.GenerateStateMachine(user_input)
                st.markdown(stateMachine)

def item():
    #Get the user's input
    container = st.container()
    with container:
        with st.form(key="my form", clear_on_submit=True):
            user_input  = st.text_area(label="Enter a short description of an item: ", key="input", height = 100)
            submit_button = st.form_submit_button(label="Generate")

        client = OpenAI()
        if submit_button:
            if not user_input:
                #If the user doesn't enter any input, use a default prompt
                user_input = f"coffee pot"
                
            with st.spinner("Creating item..."):
                #expand the item
                itemGenerator = ItemGenerator()
                description = itemGenerator.Generate(user_input)

            with st.spinner("Reticulating splines..."):
                fsmGenerator = FiniteStateMachineGenerator()
                stateMachine = fsmGenerator.GenerateStateMachine(user_input)

            #Create the item
            item = Item(user_input, description, stateMachine=stateMachine)

            #Output the item
            st.markdown(item)

            #store the item?
            ItemRepository.Create(item, locationId="6579f88e3f9d19b41993c082")
            item._id = None
            ItemRepository.Create(item, characterId="6579f88e3f9d19b41993c082")

            GetItems()

def GetItems():
    #get the item?
    st.subheader("Fetch by location:")
    items = ItemRepository.GetItems(locationId="6579f88e3f9d19b41993c082")
    for thing in items:
        st.write(thing)

    items = ItemRepository.GetItems(characterId="6579f88e3f9d19b41993c082")
    st.subheader("Fetch by character inventory:")
    for thing in items:
        st.write(thing)

def items():
    #Get the user's input
    container = st.container()
    with container:
        with st.form(key="my form", clear_on_submit=True):
            user_input  = st.text_area(label="Enter a location description: ", key="input", height = 100)
            submit_button = st.form_submit_button(label="Create Items")

        if submit_button:
            descriptions = []
            if user_input:
                descriptions.append(user_input)
            else:
                #If the user doesn't enter any input, use a default prompt
                descriptions.append(Location("Training Grounds", "Open spaces surrounded by trees where ninjas practice martial arts, stealth techniques, and engage in sparring sessions."))
                descriptions.append(Location("Small Huts", "A group of huts."))
                descriptions.append(Location("Apartment building", "A multi-tenant building with many apartments."))
                descriptions.append(Location("Main square", "The heart of the village, full of small shops and cafes."))
                descriptions.append(Location("Cozy cottages", "Tiny, picturesque homes with thatched roofs and blooming gardens."))
                descriptions.append(Location("Local pub", "A warm and friendly watering hole where villagers gather for drinks and conversation."))
                descriptions.append(Location("Country market", "A bustling market where artisans and farmers sell their wares."))

            with st.spinner("Thinking..."):
                for description in descriptions:
                    #output the user's prompt
                    st.header(description.describe())

                    generator = ItemGenerator()
                    llm = OpenAI()
                    items = generator.GenerateItems(description, llm)
                    for item in items:
                        #If the item can be interacted with, generate a state machine for it
                        generator.GenerateStateMachine(item, llm)
                        st.markdown(f"{item}\n\n")

def characters():
    container = st.container()
    with container:
        with st.form(key="my form", clear_on_submit=True):
            user_input  = st.text_area(label="Enter a short description of the scenario: ", key="input", height = 100)
            submit_button = st.form_submit_button(label="Generate Characters")

        client = OpenAI()
        if submit_button:
            descriptions = []
            if user_input:
                descriptions.append(user_input)
            else:
                #If the user doesn't enter any input, use a default prompt
                descriptions.append(f"A cozy little village")
                
            with st.spinner("Thinking..."):
                for description in descriptions:
                    #output the user's prompt
                    st.markdown(description)

                    setting = Scenario("A cozy little village", """Nestled at the foot of rolling hills, the cozy little village exudes an enchanting charm that captivates all who visit. With its picturesque houses adorned with colorful flower boxes and quaint cobblestone streets, it feels like stepping into a storybook. The air is perpetually filled with the soothing melodies of chirping birds and the occasional clip-clop of horses pulling carriages, adding to the idyllic atmosphere.

A central square serves as the heart of the village, bustling with activity as locals gather to chat, children play, and artisans display their wares. The scent of freshly baked bread wafts from the local bakery, enticing passersby with its mouthwatering aroma. Nearby, a cozy café beckons with the promise of warm drinks and friendly conversation, its outdoor seating area adorned with charming umbrellas and fairy lights.

As you wander the winding streets, you stumble upon hidden nooks and crannies that hold surprises at every turn. A babbling brook meanders through the village, its crystal-clear waters reflecting the surrounding greenery. Bridges adorned with flowers connect different parts of the village, inviting leisurely strolls and moments of reflection.

Surrounded by lush countryside, the village is a haven for nature lovers. Meandering trails lead to scenic viewpoints and peaceful picnic spots, where one can immerse themselves in the beauty of the landscape. The distant sound of sheep grazing in the fields and the scent of wildflowers in bloom create a sense of tranquility that washes away the stresses of everyday life.

As the sun sets, the village takes on a magical glow, with the warm light from cozy windows casting a soft and welcoming ambiance. The village inn, an ancient building steeped in history, offers a place of respite for weary travelers. Its roaring fireplace and comfortable armchairs invite guests to unwind and share tales of their adventures.

In this cozy little village, time seems to slow down, allowing for a simple and peaceful way of life. Whether you're seeking a retreat from the hustle and bustle of the modern world or a place to find inspiration and connection, this enchanting village offers a haven where the beauty of simplicity and community thrive.""")

                    #expand the setting
                    #settingGen = SettingGenerator()
                    #setting = settingGen.Generate(description)
                    st.markdown(setting.description)

                    #create the list of characters
                    agentGen = AgentGenerator()
                    characters = agentGen.GenerateCharacters(setting)

                    for character in characters:
                        st.markdown(character)

def storeScenario():

    #create the scenario
    setting = Scenario("A cozy little village", """Nestled at the foot of rolling hills, the cozy little village exudes an enchanting charm that captivates all who visit. With its picturesque houses adorned with colorful flower boxes and quaint cobblestone streets, it feels like stepping into a storybook. The air is perpetually filled with the soothing melodies of chirping birds and the occasional clip-clop of horses pulling carriages, adding to the idyllic atmosphere.

A central square serves as the heart of the village, bustling with activity as locals gather to chat, children play, and artisans display their wares. The scent of freshly baked bread wafts from the local bakery, enticing passersby with its mouthwatering aroma. Nearby, a cozy café beckons with the promise of warm drinks and friendly conversation, its outdoor seating area adorned with charming umbrellas and fairy lights.

As you wander the winding streets, you stumble upon hidden nooks and crannies that hold surprises at every turn. A babbling brook meanders through the village, its crystal-clear waters reflecting the surrounding greenery. Bridges adorned with flowers connect different parts of the village, inviting leisurely strolls and moments of reflection.

Surrounded by lush countryside, the village is a haven for nature lovers. Meandering trails lead to scenic viewpoints and peaceful picnic spots, where one can immerse themselves in the beauty of the landscape. The distant sound of sheep grazing in the fields and the scent of wildflowers in bloom create a sense of tranquility that washes away the stresses of everyday life.

As the sun sets, the village takes on a magical glow, with the warm light from cozy windows casting a soft and welcoming ambiance. The village inn, an ancient building steeped in history, offers a place of respite for weary travelers. Its roaring fireplace and comfortable armchairs invite guests to unwind and share tales of their adventures.

In this cozy little village, time seems to slow down, allowing for a simple and peaceful way of life. Whether you're seeking a retreat from the hustle and bustle of the modern world or a place to find inspiration and connection, this enchanting village offers a haven where the beauty of simplicity and community thrive.""")

    #try to store the scenario
    ScenarioRepository.Create(1, setting)

def updateScenario():
    scenario = ScenarioRepository.Get(1, "65777ac9e2d1fcfa43e015ef")
    scenario.name = "Too cozy!!!"
    scenario.save()

def main():

    #Set up the api key for OpenAI
    #os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    os.environ["OPENAI_API_KEY"] = openAIapikey

     #spin up mongoDB
    connect(host=mongoUri, db="pixelValley") #connect for mongoengine

    initializeScenario()
    #stateMachine()
    #item()
    #GetItems()
    #items()
    #characters()
    #storeScenario()
    #updateScenario()

def clearSession():
    st.session_state["scenario"]=None