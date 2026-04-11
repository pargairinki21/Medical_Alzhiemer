from google.adk.agents import SequentialAgent
# Relative import from your specialists file
from .specialists import librarian, researcher

# The Coordinator manages the flow of information between the PDF and the Web
# NOTE: SequentialAgent orchestrates the sub_agents in order.
# It does not require its own 'instructions' field.
coordinator = SequentialAgent(
    name="AlzheimerResearchCoordinator",
    sub_agents=[librarian, researcher]
)