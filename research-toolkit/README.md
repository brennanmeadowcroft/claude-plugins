# Research Toolkit

The research toolkit plugin provides a research assistant that does research according to an objective and provides a report.  It works best with research projects within a project that has similar research objectives because the vectordb is maintained at a project level.  If working on multiple projects, add the plugin to multiple projects.

Claude's own research flag works very well and provides a comprehensive report.  However, while those sources are cited, they are not saved and follow-up questions frequently require additional research. The research toolkit creates markdown reports that could be used by Claude Code during planning sessions.  It also saves quality content to a local vector store to answer follow-up questions.  

Research memory is saved across all research projects *within a project* so follow-up questions can expand beyond a single set of research.

**This plugin requires `yt-dlp` to be installed for YouTube transcription**

## Permissions Setup

The research agents require `WebSearch` and `WebFetch` tool permissions. Without these, research will not proceed (agents will refuse to fall back to trained knowledge).

To auto-grant these permissions at the project level, add the following to your project's `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch"
    ]
  }
}
```

This prevents repeated permission prompts during research sessions. These settings are project-scoped — they only apply when working in the project where `.claude/settings.json` is configured.

## Installation
1. Add the marketplace to Claude using the instructions in the project README
2. Add the plugin to claude code with `/plugin install research-toolkit@brennanmeadowcroft/claude-plugins`

It's also possible to install this within a codebase or repo so it's always available.  Within `.claude/settings.json`, add the following:
```
{
  "extraKnownMarketplaces": {
    "research-toolkit": {
      "source": { "source: "github", "repo": "brennanmeadowcroft/claude-plugins", "ref": "v1.0.0" }
    }
  },
  "enabledPlugins": {
    "research-toolkit@brennanmeadowcroft/claude-plugins": true
  }
}
```

## Bootstrapping
After installing, run `/init-research-toolkit` to set up permissions and the vector database within the project. This configures WebSearch/WebFetch permissions in `.claude/settings.json` and creates a `.research-memory/` folder for the local vector database.

## Usage
### Research
```
/deep-research what are emerging trends in the use of agents and skills in claude code
```
The skill with ask for any clarification needed and confirm the research objective before proceeding. All searched resources are saved in the folder under `search-results.json` or `youtube-results.json` including the URL, a quality rating, summary and key takeaways.


```
/ask-research what are the biggest obstacles to setting up agents?
```
The skill queries the vector store and returns a result with citations


## Skills
| Skill                   | Description                                                                                                                 |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `/deep-research`        | Researches according to an objective and returns a markdown report                                                          |
| `/ask-research`         | Queries the local vector store for additional questions                                                                     |
| `/init-research-toolkit` | Configures permissions, installs ChromaDB, and sets up the vector store                                                    |
| `/save-research-result` | Used by the research analyst agents, it saves each result to the research memory. **Not intended to be called by the user** |
| `/transcribe-youtube`   | Transcribes YouTube videos using yt-dlp — no API keys needed.                                                               |

## Agents
| Agent                    | Description                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| Web Research Analyst     | Conducts multiple searches and evaluates the results. Will follow additional links.            |
| Youtube Research Analyst | Conducts multiple searches on Youtube, transcribes the videos and processes the transcriptions |

