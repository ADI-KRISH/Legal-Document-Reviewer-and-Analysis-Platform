

from typing import Annotated


class SharedState:
    def __init__(self) -> None:
        self.negotiation_json = None 
        self.risk_json = None
        self.clauses_json = None
        self.report = None
        self.iteration = 0
        self.plan = Annotated[List[str]]
        self.user_query = Annotated[List[str]]
        self.response = None
        self.synthesizer_in = None
        self.synthesizer_out = None
        self.research_json = None
        self.current_agent = None
        self.next_agent = None
        self.research_output = None
        
    
    