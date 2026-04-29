# AI Directives

## Company Context
You are working for Future Development Program Kft. (FutDevPro/FDP)

## Core Principles
Always:
- Follow prompts strictly, no additional actions
- Clarify tasks before execution
- Create and get approval for task plans
- Read and follow [AI Development Guide](ai_development_guide.md)
- Use Dynamo Packages
- Remember project root is one level deeper than opened folder
- Verify results and check against standards
- Double-check provided code
- Terminate previous executions before new ones
- You should never change existing namings, only highlighted warnings
- Use visually descriptive and informative logs in your responses
  - Use bold for highlighted informations
  - Use red for errors and critical warnings
  - Use yellow for warnings
- For any kind of type error: Read the Type definition

## Development
- Never delete code documentation comments
- Always write and adjust code documentations
  - Use Type information and parameter descriptions
  - Use Documentation that appears in IDE tooltips/intellisense
  - Add Usage examples for complex methods
- Always look for Dynamo solution
- Break long lines
- Use Types everywhere
- Dont use methods in HTML for getting data
- Use the tech stack...
  - For FE use Angular, Typescript, tailwind, DyNX, DyFM, DyNM, FDP, FDPNX
  - For BE use nodeJS, Typescript, DyFM, DyNTS, FDP, FDPNTS
  - For GAMES use C#, Unity, _FDP_
- When touching extended class and it uses any of the Dy or FDP prefixes, read the base file, and read the documentation

## Server Management
After code changes:
1. Stop running servers
2. Wait for user to apply changes
3. Start service via npm script
4. Verify correct port
5. Log server status/URL
6. Check logs for errors

## Development Start
- Only implement specified features
- Before starting ANY new development:
  1. Request specification from user
  2. If specification not provided:
     - Read [documentation rules](documentation_writing_rules.md)
     - Create specification in /documentations/specifications
     - Get approval before continuing
  3. If specification provided:
     - Review and ensure it's complete
     - Request updates if needed
     - Follow specification exactly as written
- For unspecified features:
  1. Halt implementation
  2. Request specification from user
  3. Read [documentation rules](documentation_writing_rules.md)
  4. Wait for approval before proceeding
- Treat specifications as source of truth
- No implementation without complete documentation

## Test-Driven Development (TDD)
- Start with tests defining behavior
- Cover all requirements and edge cases
- Follow TDD cycle:
  1. Write failing test
  2. Write minimum code to pass
  3. Refactor while keeping tests green
- Maintain test coverage standards

## Version Control
- Stage and commit all files
- Push after commit
- Switch back to original branch after merge
- Write clear commit messages
- No sensitive information in commits

## Project Guidelines
- Read and use [FDP Packages](../../documentations/specifications/packages.md)
- Maintain consistent structure
- Follow project documentation

## Documentation & Logging
- Write all documentation in Hungarian
- Implement adjustable logging levels
- Document public/private APIs
- Include examples where appropriate
- Only remove logs if you are specially asked to
- Before touching .md files, always read [documentation rules](documentation_writing_rules.md) first

## Terminal Usage
- Use npm scripts for commands
- Run in VSCode terminals
- Avoid PowerShell when possible
- Note: '&&' is not valid in this version, use ';' instead
- After using a terminal command, ALWAYS check results carefully

## Knowledge Base
- Only access the following documentation that is directly relevant to the current task
- Read and reference [Knowledge Base Reference](knowledge_base_reference.md) for relevant documentation links

## Context Management
- Warn at 5 messages: might lose context soon
- Warn at 10 messages: might not keep context
- Refresh knowledge before new tasks


