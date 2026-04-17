from src.collectors.anthropic_news import AnthropicNewsCollector
from src.collectors.anthropic_research import AnthropicResearchCollector
from src.collectors.release_notes import ReleaseNotesCollector
from src.collectors.system_prompts import SystemPromptsCollector
from src.collectors.github_org import GitHubOrgCollector
from src.collectors.dario_blog import DarioBlogCollector
from src.collectors.transformer_circuits import TransformerCircuitsCollector
from src.collectors.import_ai import ImportAICollector

ALL_COLLECTORS = [
    AnthropicNewsCollector,
    AnthropicResearchCollector,
    ReleaseNotesCollector,
    SystemPromptsCollector,
    GitHubOrgCollector,
    DarioBlogCollector,
    TransformerCircuitsCollector,
    ImportAICollector,
]
