import sys
import os
from dotenv import load_dotenv

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from orchestrator import Orchestrator

def main():
    user_query = "Read the contract, find any risky clauses, and suggest improvements."
    state_summary = """
    - clauses_json: Exists (Extracted)
    - risk_json: Not started
    - negotiation_json: Not started
    - report: Not started
    """

    agent = Orchestrator()
    output_json_str = agent.activate_orchetrator(user_query=user_query, state_summary=state_summary)

    print("\n✅ Orchestrator Output (JSON String):\n")
    print(output_json_str)

    # Validate if it's strictly JSON
    try:
        import json
        parsed = json.loads(output_json_str)
        print("\n✅ Parsed as valid JSON:\n")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Decode Error: {e}")

if __name__ == "__main__":
    main()
