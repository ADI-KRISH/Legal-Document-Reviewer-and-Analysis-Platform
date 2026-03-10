# system/test/test_graph.py
import sys
import os

# Add the project root to path so imports resolve correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from system.state import build_graph

def test_graph_compiles():
    """Test that the graph builds and compiles without errors."""
    graph = build_graph()
    assert graph is not None
    print("✅ Graph compiled successfully!")

def test_graph_structure():
    """Test that the graph has the expected nodes."""
    graph = build_graph()
    nodes = list(graph.nodes)
    print("Graph nodes:", nodes)

    expected_nodes = ["Orchestrator", "QnA_Agent", "clause_extraction_agent", "risk_analyser", "report_generator"]
    for node in expected_nodes:
        assert node in nodes, f"Missing node: {node}"
    print("✅ All expected nodes present!")

if __name__ == "__main__":
    test_graph_compiles()
    test_graph_structure()
