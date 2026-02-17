import sys
import os
from dotenv import load_dotenv

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from research_agent import ResearchAgent

def main():
    user_query = "Is a non-compete clause for 10 years enforceable?"
    jurisdiction = "California, USA"
    clauses_json = """
    [
        {
            "heading": "Non-Compete",
            "full_text": "Employee shall not work for any competitor worldwide for a period of 10 years after termination."
        }
    ]
    """

    agent = ResearchAgent()
    output = agent.run(user_query=user_query, clauses_json=clauses_json, jurisdiction=jurisdiction)

    print("\n✅ Research Agent Output (Pydantic Object):\n")
    print(output)

    print("\n✅ Output as JSON dict:\n")
    print(output.model_dump())

if __name__ == "__main__":
    main()
