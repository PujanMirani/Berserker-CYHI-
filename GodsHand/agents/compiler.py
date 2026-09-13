import os
from GodsHand.utils.parser import load_rules

class SystemPromptCompiler:
    def __init__(self):
        self.rules = load_rules("ANTISLOP.md")
        self.liveliness_toolkit = "" # Left empty as requested

    def compile_prompt(self):
        prompt_parts = []
        
        # Inject the parsed 38 rules
        if self.rules:
            prompt_parts.append("## ANTI-SLOP Rules\n")
            prompt_parts.extend(self.rules)
        
        # Inject the Liveliness Toolkit
        if self.liveliness_toolkit:
            prompt_parts.append("\n## Liveliness Toolkit\n")
            prompt_parts.append(self.liveliness_toolkit)
            
        # Append DESIGN.md if exists
        design_path = "DESIGN.md"
        if os.path.exists(design_path):
            prompt_parts.append("\n## Project Design\n")
            with open(design_path, "r", encoding="utf-8") as f:
                prompt_parts.append(f.read())
        else:
            prompt_parts.append("\n**WARNING**: Draft without direction. (DESIGN.md not found)\n")
            
        return "\n".join(prompt_parts)
