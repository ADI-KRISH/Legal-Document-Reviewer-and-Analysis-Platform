import sys
import os
from dotenv import load_dotenv

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from synthesizer_agent import Synthesizer_Agent

def main():
    context = """
    [Risk Analysis]
    The 'Termination without notice' clause is High Risk because it disrupts business continuity.
    The 'Unlimited Liability' clause is High Risk because it exposes the vendor to bankruptcy.
    
    [Negotiation Strategy]
    We recommend changing termination to '30 days notice'.
    We recommend capping liability at 12 months' fees.
    """
    
    query = "Summarize the major risks and proposed changes for the client."

    agent = Synthesizer_Agent()
    output = agent.respond(context=context, query=query)

    print("\n✅ Synthesizer Agent Output (Pydantic Object):\n")
    print(output)

    print("\n✅ Output as JSON dict:\n")
    print(output.model_dump())

if __name__ == "__main__":
    main()
