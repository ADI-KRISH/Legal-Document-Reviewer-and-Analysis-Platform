import sys
import os
from dotenv import load_dotenv
import json

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from negotiation_agent import Negotiation_Agent

def main():
    clauses_json = {
        "sections": [
            {
                "heading": "Termination",
                "full_text": "Either party may terminate this Agreement at any time without notice.",
                "summary": "This allows termination instantly without warning."
            },
            {
                "heading": "Liability",
                "full_text": "The vendor shall be liable for any and all damages of any kind without limitation.",
                "summary": "Unlimited liability clause for the vendor."
            }
        ],
        "key_entities": {
            "parties": ["Client", "Vendor"],
            "dates": [],
            "durations": [],
            "financial_terms": [],
            "obligations": [],
            "liabilities": ["Unlimited liability for vendor"],
            "termination_clauses": ["Terminate anytime without notice"],
            "confidentiality_clauses": [],
            "arbitration_clauses": [],
            "governing_law": []
        }
    }

    risk_json = {
        "overall_risk_level": "High",
        "risk_analysis": [
            {
                "clause_reference": "Termination",
                "clause_text": "Either party may terminate this Agreement at any time without notice.",
                "risk_level": "High",
                "risk_reason": "No notice period creates operational and financial instability."
            },
            {
                "clause_reference": "Liability",
                "clause_text": "The vendor shall be liable for any and all damages of any kind without limitation.",
                "risk_level": "High",
                "risk_reason": "Unlimited liability exposes the vendor to extreme financial risk."
            }
        ],
        "missing_clauses": [],
        "conflicts_and_ambiguities": [],
        "compliance_flags": [
            {
                "flag": "No",
                "issue": "",
                "related_clause_reference": ""
            }
        ],
        "recommendations": [
            {
                "clause_reference": "Termination",
                "recommendation": "Add a notice period and termination for cause provisions."
            },
            {
                "clause_reference": "Liability",
                "recommendation": "Introduce a liability cap and exclude indirect damages."
            }
        ]
    }

    # Convert to JSON string as expected by the agent
    clauses_str = json.dumps(clauses_json)
    risk_str = json.dumps(risk_json)

    agent = Negotiation_Agent()
    output = agent.negotiate(clauses_json=clauses_str, risk_json=risk_str)

    print("\n✅ Negotiation Agent Output (Pydantic Object):\n")
    print(output)

    print("\n✅ Output as JSON dict:\n")
    print(output.model_dump())

if __name__ == "__main__":
    main()
