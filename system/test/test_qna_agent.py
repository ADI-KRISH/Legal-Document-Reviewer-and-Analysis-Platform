import sys
import os
from dotenv import load_dotenv
from unittest.mock import MagicMock

# Add current directory (system) to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace(os.sep + 'test', ''))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Mock document_parser globally BEFORE importing QnA_Agent
sys.modules['document_parser'] = MagicMock()

# Setup mock vector_store behavior
mock_vector_store = MagicMock()
sys.modules['document_parser'].vector_store = mock_vector_store

from QnA_Agent import QnA_Agent

def main():
    # Configure the mock return value
    mock_doc = MagicMock()
    mock_doc.page_content = "The termination notice period is 30 days written notice."
    mock_doc.metadata = {"chunk_id": "chunk_10", "source": "contract_v1.pdf"}
    mock_vector_store.similarity_search.return_value = [mock_doc]

    query = "What is the termination notice period?"

    print(f"\n🔍 Querying QnA Agent with: '{query}'")
    
    try:
        agent = QnA_Agent()
        output = agent.get_answer(query)

        print("\n✅ QnA Agent Output (Pydantic Object):\n")
        print(output)

        print("\n✅ Output as JSON dict:\n")
        print(output.model_dump())
        
    except Exception as e:
        print(f"\n❌ Error running QnA Agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
