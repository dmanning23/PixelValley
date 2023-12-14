
class Scenario:

    def __init__(self, name, description = None, locations = None, agents = None, _id = None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.locations = locations
        self.agents = agents

    def __str__(self) -> str:
        return self.name
    
    def GetLocations(self):
        locations = self.locations
        for location in self.locations:
            locations = locations + location.GetLocations()

        return locations

