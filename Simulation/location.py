from Simulation.item import Item

class Location:
    """
    A class to represent a location in the simulated environment

    Attributes:
    name: string
        The name of the location
    description: string
        A short description of the location
    locations:
        A collection of places in this location. Can be empty
    items:
        A collection of things that can be interacted with in this environment.

    """
    def __init__(self, 
                 name,
                 description,
                 canSubdivide = False,
                 locations=None,
                 items=None,
                 agents = None,
                 _id = None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.canSubdivide = canSubdivide
        self.locations = locations
        self.items = items
        self.agents = agents

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    def GetLocations(self):
        locations = []
        if self.locations is not None:
            locations = self.locations
            for location in self.locations:
                locations = locations + location.GetLocations()

        return locations
    
    def GetAgents(self):
        #Add my agents
        agents = []
        if self.agents is not None:
            agents = agents + self.agents

        #Add agents of all child locations
        if self.locations is not None:
            for location in self.locations:
                agents = agents + location.GetAgents()

        return agents