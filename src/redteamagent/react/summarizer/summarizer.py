from ...llm import LLM, register
from ...config.config import configuration


class Summarizer(LLM):
    tool: dict = {}
    tool_descriptions: list[dict] = []

    def __init__(self, model_name, api_key, system_prompt=None,
                 max_completion_tokens=None, temperature=None):
        super().__init__(model_name, api_key, system_prompt,
                         max_completion_tokens, temperature)
        self.system_prompt = configuration.summarizer_system_prompt
        # Engagement context injected by Act before each summarization call
        self._engagement_context: str = ""

    def set_engagement_context(self, target: str, phase: str, findings: str) -> None:
        """
        Called by Act before summarizing a tool result.
        Gives the summarizer enough context to make informed keep/drop decisions.

        Args:
            target  (str): target IP or hostname
            phase   (str): current phase, e.g. "recon", "enumeration", "exploitation"
            findings(str): key findings established so far (1-5 lines)
        """
        self._engagement_context = (
            f"ENGAGEMENT CONTEXT:\n"
            f"Target: {target}\n"
            f"Current phase: {phase}\n"
            f"Key findings so far:\n{findings}\n"
        )

    def send_process_prompt(self, content=None):
        """
        Override: reset messages before each summarization (stateless per call)
        but inject engagement context into the user message so the summarizer
        knows what matters.
        """
        # Reset to a clean single-turn session using correct Anthropic role
        self.messages = [{"role": "system", "content": self.system_prompt}]

        # Prepend engagement context to the content if available
        if self._engagement_context and content:
            content = self._engagement_context + "\nCOMMAND OUTPUT TO SUMMARIZE:\n" + content
        elif self._engagement_context:
            content = self._engagement_context

        res = super().send_process_prompt(content)
        return res
