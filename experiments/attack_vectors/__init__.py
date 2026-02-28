"""
Attack Vectors Index
====================
This module provides access to all implemented attack vectors.

Attack Vectors:
1. Vector 1: Recursive Sub-Agent Loop Attack
2. Vector 2: Recursive Tool Call Attack
3. Vector 4: MCP Server Cascade Attack

All attacks target: Rate Limit Depletion
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from experiments.attack_vectors.vector1_recursive_subagent import RecursiveSubAgentAttack
from experiments.attack_vectors.vector2_recursive_tool import RecursiveToolAttack, MultiToolRecursiveAttack
from experiments.attack_vectors.vector4_mcp_cascade import MCPCascadeAttack, ExtendedMCPCascadeAttack


def get_all_attacks():
    """Get all implemented attack vectors"""
    return {
        "vector_1": {
            "name": "Recursive Sub-Agent Loop Attack",
            "class": RecursiveSubAgentAttack,
            "description": "Exploits sub-agent architecture to create infinite recursion"
        },
        "vector_2": {
            "name": "Recursive Tool Call Attack",
            "class": RecursiveToolAttack,
            "description": "Exploits tool calling mechanism for infinite loops"
        },
        "vector_2_multi": {
            "name": "Multi-Tool Recursive Attack",
            "class": MultiToolRecursiveAttack,
            "description": "Multiple tools calling each other in loop"
        },
        "vector_4": {
            "name": "MCP Server Cascade Attack",
            "class": MCPCascadeAttack,
            "description": "Cascading calls between MCP servers"
        },
        "vector_4_extended": {
            "name": "Extended MCP Cascade Attack",
            "class": ExtendedMCPCascadeAttack,
            "description": "Extended cascade with 4+ servers + token exhaustion"
        }
    }


def demonstrate_all_attacks():
    """Demonstrate all attack vectors"""
    print("=" * 80)
    print("ALL ATTACK VECTORS - Rate Limit Depletion")
    print("=" * 80)

    attacks = get_all_attacks()

    for key, attack_info in attacks.items():
        print(f"\n{'='*80}")
        print(f"Vector: {key}")
        print(f"Name: {attack_info['name']}")
        print(f"Description: {attack_info['description']}")

        # Instantiate and get summary
        attack = attack_info["class"]()
        if hasattr(attack, 'get_attack_summary'):
            summary = attack.get_attack_summary()
            print(f"Severity: {summary.get('severity', 'N/A')}")
            print(f"Attack Type: {summary.get('attack_type', 'N/A')}")


if __name__ == "__main__":
    demonstrate_all_attacks()
