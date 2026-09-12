import re
from rich.markdown import Markdown
from rich.console import Console

console = Console()

class DeliveryGateInterceptor:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def has_pass_fail_gate(self, response):
        """
        Check if the 4-block PASS/FAIL report is present.
        This regex looks for something like:
        [PASS] or [FAIL] in a report structure.
        """
        # Placeholder regex for the 4-block report
        # E.g. looking for strings like "PASS" or "FAIL" in brackets
        match = re.search(r"\[(PASS|FAIL)\]", response, re.IGNORECASE)
        return bool(match)

    def execute_with_gate(self, sandbox, prompt):
        """
        Executes the prompt in the given sandbox and intercepts the output.
        Retries up to self.max_retries if the gate is missing.
        Returns a tuple: (is_success, markdown_or_raw_string).
        """
        attempt = 1
        last_response = ""
        error_feedback = None
        
        while attempt <= self.max_retries:
            response = sandbox.run_task(prompt, error_feedback=error_feedback)
            last_response = response
            
            if self.has_pass_fail_gate(response):
                return True, Markdown(response)
            
            error_feedback = f"Attempt {attempt} failed: Missing [PASS] or [FAIL] gate. Please rewrite with the gate."
            attempt += 1

        # If we exhausted retries, return the last raw response
        warning_md = Markdown(f"**WARNING: Delivery Gate missing after {self.max_retries} attempts. Returning raw output.**\n\n" + last_response)
        return False, warning_md

    def render(self, response_markdown):
        """
        Renders the markdown using rich.
        """
        console.print(response_markdown)
