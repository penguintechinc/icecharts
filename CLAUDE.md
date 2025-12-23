## File Size Limits
- **Maximum file size**: 25,000 characters for ALL code and markdown files
- **Split large files**: Decompose into modules, libraries, or separate documents
- **CLAUDE.md exception**: Maximum 39,000 characters (only exception to 25K rule)
- **High-level approach**: CLAUDE.md contains high-level context and references detailed docs
- **Documentation strategy**: Create detailed documentation in `docs/` folder and link to them from CLAUDE.md
- **Keep focused**: Critical context, architectural decisions, and workflow instructions only
- **User approval required**: ALWAYS ask user permission before splitting CLAUDE.md files
- **Use Task Agents**: Utilize task agents (subagents) to be more expedient and efficient when making changes to large files, updating or reviewing multiple files, or performing complex multi-step operations
- **Avoid sed/cat**: Use sed and cat commands only when necessary; prefer dedicated Read/Edit/Write tools for file operations

## Task Agent Usage Guidelines

**Model Selection:**
- **Haiku model**: Use for the majority of task agent work (file searches, simple edits, routine operations)
- **Sonnet model**: Use for more complex jobs requiring deeper reasoning (architectural decisions, complex refactoring, multi-file coordination)
- Default to haiku unless the task explicitly requires complex analysis

**Response Size Requirements:**
- **CRITICAL**: Task agents MUST return minimal responses to avoid context overload of the orchestration model
- Agents should return only essential information: file paths, line numbers, brief summaries
- Avoid returning full file contents or verbose explanations in agent responses
- Use bullet points and concise formatting in agent outputs

**Concurrency Limits:**
- **Maximum 10 task agents** running concurrently at any time
- Even with minimal responses, running more than 10 agents risks context overload
- Queue additional tasks if the limit would be exceeded
- Monitor active agent count before spawning new agents

**Best Practices:**
- Provide clear, specific prompts to agents to get focused responses
- Request only the information needed, not comprehensive analysis
- Use agents for parallelizable work (searching multiple directories, checking multiple files)
- Combine related small tasks into single agent calls when possible

## Pre-Commit Screenshots

**Before Every Commit - Screenshots**:
- **Run screenshot tool to update UI screenshots in documentation**
  - Run `cd services/webui && npm run screenshots` to capture current UI state
  - This automatically removes old screenshots and captures fresh ones
  - Commit updated screenshots with relevant feature/documentation changes

## API Versioning Standards

**API Versioning**:
- ALL REST APIs MUST use versioning: `/api/v{major}/endpoint` format
- Semantic versioning for major versions only in URL
- Support current and previous versions (N-1) minimum
- Add deprecation headers to old versions
- Document migration paths for version changes

## Local State Management

**Local State Management (Crash Recovery)**:
- **ALWAYS maintain local .PLAN and .TODO files** for crash recovery
- **Keep .PLAN file updated** with current implementation plans and progress
- **Keep .TODO file updated** with task lists and completion status
- **Update these files in real-time** as work progresses
- **Add to .gitignore**: Both .PLAN and .TODO files must be in .gitignore
- **File format**: Use simple text format for easy recovery
- **Automatic recovery**: Upon restart, check for existing files to resume work
