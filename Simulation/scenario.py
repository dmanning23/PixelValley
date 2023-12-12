
class Scenario:

    def __init__(self, name, description = None, locations = None, _id = None):
        if _id is not None:
            self._id = _id
        self.name = name
        self.description = description
        self.locations = locations

    def __str__(self) -> str:
        return self.name
