import re
from pathlib import Path

def load_rules(rule_file="ANTISLOP.md"):
    """
    Reads a markdown file containing rules and extracts rule blocks.
    
    Args:
        rule_file (str): The name of the rule file to load.
        
    Returns:
        list: A list of extracted rule strings.
    """
    rule_path = Path(__file__).parent.parent / "rules" / rule_file
    
    if not rule_path.exists():
        return []

    with open(rule_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract rule blocks: R-XX — Rule Name or similar patterns
    rules = re.findall(r"(R-[A-Z0-9\-]+.*?)(?=R-[A-Z0-9\-]+|$)", content, re.DOTALL)
    
    # Clean up whitespace
    return [rule.strip() for rule in rules if rule.strip()]
