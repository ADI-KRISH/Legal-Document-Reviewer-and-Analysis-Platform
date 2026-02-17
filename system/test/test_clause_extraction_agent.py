import sys
import os
from dotenv import load_dotenv

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from clause_extraction_agent import Clause_Extraction_Agent

def main():
    test_text = """
    EMPLOYMENT AGREEMENT

    1. TERM. This Agreement shall commence on January 1, 2024 and continue for a period of two (2) years.
    2. COMPENSATION. The Employee shall receive an annual base salary of $100,000, payable in monthly installments.
    3. TERMINATION. Either party may terminate this Agreement with 30 days' prior written notice.
    4. CONFIDENTIALITY. Employee agrees not to disclose any proprietary info to third parties during or after the term.
    """
    
    source_name = "sample_employment_agreement.txt"

    agent = Clause_Extraction_Agent()
    output = agent.extract_clauses(text=test_text, source=source_name)

    print("\n✅ Clause Extraction Agent Output (Pydantic Object):\n")
    print(output)

    print("\n✅ Output as JSON dict:\n")
    print(output.model_dump())

if __name__ == "__main__":
    main()
