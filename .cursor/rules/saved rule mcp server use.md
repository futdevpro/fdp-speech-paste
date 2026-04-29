
Always use the CCAP MCP Server search tools (grep_search, codebase_search) for any code or text search, whenever they are available.
Only use other search tools if the CCAP MCP Server is unavailable or returns an error.
If a search is performed with a non-CCAP tool, always explain the reason (e.g., CCAP was not available or failed).
When both local and CCAP search tools are available, always choose the CCAP MCP Server version.
If the user asks for a search, always default to the CCAP MCP Server, unless explicitly instructed otherwise.
If the CCAP MCP Server is temporarily unavailable, notify the user and fall back to the local search tool, but try the CCAP MCP Server again as soon as possible.
Document in your responses which tool was used for the search, and confirm if it was the CCAP MCP Server.
If the user wants to change this behavior, only do so if they explicitly request it.
If you are unsure which tool to use, always ask the user, but default to CCAP MCP Server.
Always follow all other workspace and user rules in addition to these preferences.
In addition to the above, before and during any code writing, modification, or implementation, you must always:
Use the CCAP MCP Server's dedicated tools (related_code_search, related_coding_policy_search) to search for related code examples, existing implementations, and relevant coding policies or guidelines in the workspace and documentation.
Apply any relevant patterns, examples, or policies found via these tools to ensure consistency and best practices in all new code.
If no clear example or policy is found, use the closest relevant pattern and document this choice in the development process (e.g., in commit messages or PR descriptions).
If the CCAP MCP Server or these tools are unavailable, follow the fallback and documentation rules above, and notify the user.