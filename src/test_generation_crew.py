class TestGenerationCrew:
    def __init__(self):
        self.agents = []
    
    def kickoff(self):
        if not self.agents:
            raise ValueError("Cannot create crew without agents")
        return "Crew started"