import sys
import os
from dotenv import load_dotenv
import json

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from risk_agent import RiskAgent

def main():
    clauses_json = [
        {
            "clause_id": "CLS-001",
            "heading": "Indemnification",
            "full_text": "The Provider shall indemnify and hold harmless the Client against all claims, losses, and damages arising from the Provider's negligence.",
            "summary": "Provider protects Client from negligence claims."
        },
        {
            "clause_id": "CLS-002",
            "heading": "Limitation of Liability",
            "full_text": "In no event shall the Provider be liable for any indirect, incidental, or consequential damages.",
            "summary": "Excludes indirect damages."
        },
        {
            "clause_id": "CLS-003",
            "heading": "Non-Compete",
            "full_text": "Employee shall not work for any competitor worldwide for a period of 10 years after termination.",
            "summary": "10-year worldwide non-compete."
        }
    ]

    # Convert to JSON string as expected
    clauses_str = json.dumps(clauses_json)

    agent = RiskAgent()
    output = agent.analyze_risk(clauses_json=clauses_str)

    print("\n✅ Risk Agent Output (Pydantic Object):\n")
    print(output)

    print("\n✅ Output as JSON dict:\n")
    print(output.model_dump())

if __name__ == "__main__":
    main()
