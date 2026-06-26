#!/usr/bin/env python3
"""
CockroachDB Intelligent Agent Extraordinaire (CRDB-AIE) - Query Learning + Vector Search

This agent uses Claude API to intelligently handle CockroachDB tasks with
query-based learning to get smarter over time.

Architecture:
    1. User provides a natural language task
    2. Agent searches for similar past queries (using 768-dim semantic embeddings)
    3. If similar query found: pre-load skills that helped before
    4. If no match: start with 0 pre-loaded skills (fetch on-demand if needed)
    5. Claude API receives the task, optional skills context, and MCP tool definitions
    6. Claude creates a plan and calls appropriate MCP tools
    7. Agent executes MCP tools via the MCP server
    8. Results are sent back to Claude for interpretation
    9. Claude provides the final response to the user
    10. Store query + skills that helped for future learning

Key Optimizations:
    - Query Learning: Learns from every interaction, pre-loads proven skills
    - Zero Default Skills: Simple queries use 0 pre-loaded skills (saves ~8KB tokens)
    - On-Demand Fetching: Claude uses fetch_skill tool only when needed
    - 768-dim Embeddings: High-quality semantic matching (all-mpnet-base-v2)
    - Color-Coded Output: Task (blue), Skills (red) for clear demo presentation

Recent Updates:
    - 2026-04-05: Enabled write operations (create_database, create_table, insert_rows) with user confirmation
    - 2026-04-05: Added color-coded UI (task in dark blue, skills in dark red)
    - 2026-04-05: Fixed stdout buffering for consistent output order
    - 2026-04-04: Upgraded to 768-dim embeddings (all-mpnet-base-v2)
    - 2026-04-04: Eliminated default skill pre-loading (zero-skill optimization)

This creates an intelligent agent that can:
    - List databases and tables
    - Execute SELECT queries
    - Analyze schema
    - Run diagnostics
    - Create databases and tables (with user confirmation)
    - Insert rows (with user confirmation)
    - Follow CockroachDB best practices from SKILL.md files
    - Get smarter over time by learning which skills help each type of query
"""

# Suppress warnings from Google Cloud libraries
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='google.auth')
warnings.filterwarnings('ignore', category=FutureWarning, module='google.oauth2')
warnings.filterwarnings('ignore', category=UserWarning, module='google.auth._default')

import json
import sys
from pathlib import Path
from anthropic import Anthropic, AnthropicVertex
from skill_fetcher import SkillFetcher
from mcp_client import MCPClient
from mcp_tools import get_agent_tools  # Only agent tools - MCP tools discovered dynamically!
from query_store import QueryStore
from ollama_embedding_manager import OllamaEmbeddingManager
import time

# Conditional imports for vector search mode
try:
    from embedding_manager import EmbeddingManager
    from skills_vectorstore import SkillsVectorStore
except ImportError:
    EmbeddingManager = None
    SkillsVectorStore = None

# ANSI color codes for terminal output
# Added 2026-04-05: Color-coded output for better visual distinction
class Colors:
    """ANSI escape codes for colored terminal output"""
    HEADER = '\033[95m'      # Bright magenta
    OKBLUE = '\033[94m'      # Blue
    OKCYAN = '\033[96m'      # Cyan
    OKGREEN = '\033[92m'     # Green
    WARNING = '\033[93m'     # Yellow
    DARK_ORANGE = '\033[38;5;208m'  # Dark orange (for write operation warnings)
    FAIL = '\033[91m'        # Red
    ENDC = '\033[0m'         # Reset
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline
    BG_BLUE = '\033[44m'     # Blue background
    BG_CYAN = '\033[46m'     # Cyan background
    BG_WHITE = '\033[47m'    # White background
    BLACK = '\033[30m'       # Black text (for use with light backgrounds)


def print_task_header(task_text):
    """
    Print the task with highlighted formatting to make it stand out.

    Added 2026-04-05: Visual enhancement for demo clarity
    - Uses ANSI escape codes for dark blue color
    - Bold text with double-line separators
    - Makes task easily distinguishable from output

    Args:
        task_text: The user's task/question to highlight
    """
    # ANSI colors - dark blue
    # \033[1m = bold, \033[34m = dark blue, \033[0m = reset
    width = 80

    print()
    print("\033[1m\033[34m" + "=" * width + "\033[0m")
    print("\033[1m\033[34m" + "=" * width + "\033[0m")
    print(f"\033[1m\033[34m>>> TASK: {task_text}\033[0m")
    print("\033[1m\033[34m" + "=" * width + "\033[0m")
    print("\033[1m\033[34m" + "=" * width + "\033[0m")
    print()


class CockroachDBAgent:
    """
    Intelligent agent for CockroachDB operations using Claude API.
    """

    def __init__(self, config_path="config.json"):
        """
        Initialize the agent.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)

        # Set verbose mode (default: False for cleaner output)
        self.verbose = self.config.get("verbose", False)

        # Initialize Claude API client (Vertex AI or standard Anthropic)
        if self.config.get("use_vertex_ai", False):
            if self.verbose:
                print(f"Using Claude via Vertex AI")
                print(f"  Project: {self.config['vertex_ai_project']}")
                print(f"  Region: {self.config['vertex_ai_region']}\n")
            self.claude = AnthropicVertex(
                project_id=self.config["vertex_ai_project"],
                region=self.config["vertex_ai_region"]
            )
        else:
            if self.verbose:
                print("Using Claude via standard Anthropic API\n")
            self.claude = Anthropic(api_key=self.config["anthropic_api_key"])

        # Initialize MCP client
        self.mcp_client = MCPClient(
            mcp_server_url=self.config["mcp_server_url"],
            cluster_id=self.config["cluster_id"],
            api_key=self.config["api_key"]
        )

        # Discover available tools from MCP server (dynamic discovery!)
        print("🔍 Discovering tools from MCP server...")
        self.mcp_tools = self.mcp_client.list_tools()
        if self.mcp_tools:
            print(f"✅ Discovered {len(self.mcp_tools)} MCP tools")
            for tool in self.mcp_tools[:3]:  # Show first 3
                print(f"   • {tool.get('name', 'unknown')}")
            if len(self.mcp_tools) > 3:
                print(f"   ... and {len(self.mcp_tools) - 3} more")
        else:
            print("⚠️  Warning: No tools discovered from MCP server")
            print("   Using agent tools only (fetch_skill, complete_task)")
        print()

        # Track write operation approval state
        # Can be controlled via config.json with "skip_write_confirmations": true
        self.auto_approve_writes = self.config.get("skip_write_confirmations", False)

        # Check if query-based learning is enabled (preferred over vector search)
        self.use_query_learning = self.config.get("use_query_learning", True)  # Enable by default

        # Check if vector search is enabled (legacy skill embedding approach)
        self.use_vector_search = self.config.get("use_vector_search", False)

        if self.use_query_learning:
            # Initialize query-based learning components
            if self.verbose:
                print("Query-based learning: ENABLED")
                print("  (Agent will learn from successful queries)")

            # Get database connection
            connection_string = self.config.get("database_connection_string")
            if connection_string:
                import os
                connection_string = connection_string.replace('$HOME', os.path.expanduser('~'))
                connection_string = connection_string.replace('/defaultdb?', '/ai_demo?')

                self.query_store = QueryStore(connection_string)

                if self.verbose:
                    stats = self.query_store.get_query_stats()
                    print(f"✓ Query store connected ({stats['total_queries']} queries learned)\n")
            else:
                print("WARNING: No database_connection_string - query learning disabled")
                self.use_query_learning = False
                self.query_store = None

            # Load skills for when we need defaults
            connection_string = self.config.get("database_connection_string")
            self.skill_fetcher = SkillFetcher(verbose=self.verbose, connection_string=connection_string)

            # Try database → local cache → GitHub
            if not self.skill_fetcher.load_from_database():
                if not self.skill_fetcher.load_from_cache():
                    self.skill_fetcher.fetch_all_skills()

            if self.verbose:
                print(f"✓ Loaded {len(self.skill_fetcher.skills)} skills as fallback\n")

        elif self.use_vector_search:
            # Initialize vector search components
            if self.verbose:
                print("Vector search: ENABLED")

            # Get embedding region (can't be "global")
            embedding_region = self.config.get("vertex_ai_region", "us-central1")
            if embedding_region == "global":
                embedding_region = "us-central1"

            self.embedding_manager = EmbeddingManager(
                project_id=self.config["vertex_ai_project"],
                region=embedding_region
            )

            # Initialize vector store
            connection_string = self.config.get("database_connection_string")
            if not connection_string:
                print("ERROR: Vector search enabled but no database_connection_string in config")
                print("Please add database_connection_string to config.json")
                print("Or run: python3 utilities/index_skills.py")
                sys.exit(1)

            self.vector_store = SkillsVectorStore(connection_string)

            if self.verbose:
                skill_count = self.vector_store.get_skill_count()
                print(f"✓ Vector store connected ({skill_count} skills indexed)\n")

            # Don't need to load all skills into memory
            self.skill_fetcher = None
            self.skills_context = None

        else:
            # Legacy mode: load all skills into memory
            if self.verbose:
                print("Vector search: DISABLED (using legacy mode)")

            connection_string = self.config.get("database_connection_string")
            self.skill_fetcher = SkillFetcher(verbose=self.verbose, connection_string=connection_string)

            # Load skills (try database → cache → GitHub)
            if self.verbose:
                print("Loading CockroachDB skills documentation...")
            if not self.skill_fetcher.load_from_database():
                if not self.skill_fetcher.load_from_cache():
                    self.skill_fetcher.fetch_all_skills()

            self.skills_context = self.skill_fetcher.get_skills_context()
            if self.verbose:
                print(f"✓ Loaded {len(self.skill_fetcher.skills)} skills\n")

            # No vector search in legacy mode
            self.embedding_manager = None
            self.vector_store = None

    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"ERROR: Config file not found: {config_path}")
            print("Please copy config.template.json to config.json and add your credentials.")
            sys.exit(1)

        with open(config_file, 'r') as f:
            config = json.load(f)

        # Validate required fields based on configuration
        required_fields = ["mcp_server_url", "cluster_id", "api_key"]

        # Add Anthropic API key requirement if not using Vertex AI
        if not config.get("use_vertex_ai", False):
            required_fields.append("anthropic_api_key")
        else:
            # Vertex AI requires project and region
            required_fields.extend(["vertex_ai_project", "vertex_ai_region"])

        missing_fields = [field for field in required_fields if not config.get(field) or config[field] == f"your-{field.replace('_', '-')}-here"]

        if missing_fields:
            print(f"ERROR: Missing or incomplete configuration fields: {', '.join(missing_fields)}")
            print("Please update config.json with your actual credentials.")
            sys.exit(1)

        return config

    def _build_system_prompt(self, user_task=None):
        """
        Build the system prompt for Claude.

        In vector mode, this searches for relevant skills based on the user's task.
        In legacy mode, this includes all skills.

        Args:
            user_task: The user's current task (used for vector search)

        Returns:
            str: System prompt with skills context
        """
        base_prompt = """You are an expert CockroachDB database administrator assistant.

You have access to MCP (Model Context Protocol) tools that let you interact with a CockroachDB cluster.
Use these tools to fulfill user requests about databases, tables, queries, and cluster operations.

AVAILABLE CAPABILITIES:
- List clusters, databases, and tables
- Get table schemas and structure
- Execute SELECT queries (read-only)
- Show running queries
- Explain query execution plans
- Cluster health checks

WRITE OPERATIONS:
- You have access to the following write operations via MCP tools:
  * create_database - Create new databases
  * create_table - Create new tables with SQL CREATE TABLE statements
  * insert_rows - Insert rows into existing tables

- IMPORTANT: The user will be prompted to confirm before ANY write operation executes
- When the user requests a write operation:
  1. Use the appropriate MCP tool (create_database, create_table, insert_rows)
  2. The system will ask the user: "Execute this operation? (yes/no)"
  3. The operation only executes if the user confirms with "yes"

- LIMITATIONS - You CANNOT:
  * UPDATE or DELETE existing data
  * DROP or ALTER databases, tables, or schemas
  * GRANT or REVOKE permissions
  * Modify cluster configuration
  * Execute raw DDL/DML beyond the available tools

GUIDELINES:
- Execute user requests directly when the intent is clear
- Maintain context across the conversation
- Format results clearly and concisely
- For write operations (create_database, create_table, insert_rows), use the appropriate tool - the user will confirm before execution
- For operations not supported by the available tools, explain the limitation and provide SQL they can run directly

SKILL LEARNING SYSTEM:
- You start with NO pre-loaded skills (saves tokens for simple queries)
- Try to answer the question using just the MCP tools first
- If you need additional information, use the 'fetch_skill' tool to load specific skill guides
- Only fetch skills you actually need - don't fetch speculatively
- When you have successfully completed the user's task, call 'complete_task' with:
  1. skills_that_helped: ONLY the skills whose content you actually referenced in your answer (array of skill names)
  2. answer: The FULL, COMPLETE answer text you want to show the user (NOT a summary - the actual detailed response)
- IMPORTANT: The 'answer' field in complete_task is what gets displayed to the user, so include ALL the details, formatting, code examples, etc.
- This learning helps future similar queries load the right skills immediately
"""

        # Add skills context based on mode
        if self.use_query_learning and user_task:
            # Query learning mode: Get skills from similar past queries
            skills_context = self._get_skills_from_query_learning(user_task)
        elif self.use_vector_search and user_task:
            # Vector mode: search for relevant skills
            skills_context = self._get_relevant_skills(user_task)
        elif self.use_vector_search or self.use_query_learning:
            # Vector/query mode but no user task yet
            skills_context = "\nCockroachDB skills available."
        else:
            # Legacy mode: use skills summary
            skills_context = f"\nCockroachDB Best Practices (summary):\n{self._get_skills_summary()}"

        return base_prompt + skills_context

    def _get_skills_from_query_learning(self, user_task, top_k=3):
        """
        Use query-based learning to find relevant skills.

        Searches for similar past queries and uses the skills that helped answer them.

        Args:
            user_task: The user's question/task
            top_k: Number of skills to retrieve (default: 3)

        Returns:
            str: Formatted relevant skills or defaults
        """
        if not self.use_query_learning or not self.query_store:
            return ""

        try:
            # Get skill recommendation based on similar queries
            recommendation = self.query_store.get_skills_for_query(
                user_task,
                default_skills=self._get_default_skills()
            )

            if recommendation['source'] == 'learned':
                # Found similar query - use those skills
                skill_names = recommendation['skills']

                if self.verbose:
                    print(f"[Query Learning] Found similar query (similarity: {recommendation['similarity']:.2f})")
                    print(f"[Query Learning] Matched: '{recommendation['matched_query']}'")
                    print(f"[Query Learning] Using skills: {', '.join(skill_names)}")
                    print()

                # Get full skill content
                skills_content = []
                for skill_name in skill_names:
                    if self.skill_fetcher and skill_name in self.skill_fetcher.skills:
                        skills_content.append(f"\n--- Skill: {skill_name} ---\n")
                        skills_content.append(self.skill_fetcher.skills[skill_name]['content'])

                if skills_content:
                    return "\n\nRELEVANT COCKROACHDB SKILLS (from similar queries):\n" + "\n".join(skills_content)
                else:
                    return "\nUsing learned skill recommendations."

            else:
                # No similar query found - start with no pre-loaded skills
                if self.verbose:
                    print(f"[Query Learning] No similar query found, starting with no pre-loaded skills")
                    print(f"[Query Learning] Claude can fetch skills if needed using fetch_skill tool")
                    print()

                # Return empty string (no pre-loaded skills)
                return ""

        except Exception as e:
            if self.verbose:
                print(f"Warning: Query learning failed: {e}")
            return ""

    def _get_default_skills(self):
        """
        Get default skills to use when no learned match is found.

        Returns:
            list: Default skill names (empty list - let Claude fetch what it needs)

        OPTIMIZATION CHANGE (2026-04-04):
        Previously returned 3 default skills for EVERY query, which wasted tokens on simple
        queries like "how many databases?". Now returns empty array [].

        Strategy:
        - Simple queries (e.g., "list databases") → 0 skills needed, use MCP tools only
        - Complex queries (e.g., "optimize slow query") → Claude fetches specific skills on-demand
        - Learned queries → Pre-load proven-helpful skills from similar past queries

        Result: ~30-40% token savings on typical query mix, no loss in capability.
        """
        return []

    def _get_default_skill_content(self, skill_names):
        """
        Get formatted content for default skills.

        Args:
            skill_names: List of skill names

        Returns:
            str: Formatted skill content
        """
        if not self.skill_fetcher:
            return "\nDefault CockroachDB best practices will be applied."

        skills_content = []
        for skill_name in skill_names:
            if skill_name in self.skill_fetcher.skills:
                skills_content.append(f"\n--- Skill: {skill_name} ---\n")
                skills_content.append(self.skill_fetcher.skills[skill_name]['content'])

        if skills_content:
            return "\n\nCOCKROACHDB BEST PRACTICES:\n" + "\n".join(skills_content)
        else:
            return ""

    def _get_relevant_skills(self, user_task, top_k=3):
        """
        Use vector search to find relevant skills for the user's task.

        Args:
            user_task: The user's question/task
            top_k: Number of skills to retrieve (default: 3)

        Returns:
            str: Formatted relevant skills
        """
        if not self.use_vector_search:
            return ""

        try:
            # Generate embedding for the user's task
            query_embedding = self.embedding_manager.generate_embedding(user_task)

            # Search for similar skills
            results = self.vector_store.search_similar_skills(query_embedding, limit=top_k)

            if not results:
                return "\nNo relevant skills found."

            # Format results
            context_parts = ["\n\nRELEVANT COCKROACHDB SKILLS FOR THIS TASK:"]

            for i, result in enumerate(results, 1):
                context_parts.append(f"\n--- Skill {i}: {result['skill_name']} (relevance: {result['similarity']:.2f}) ---")
                context_parts.append(result['content'])
                context_parts.append("")

            return "\n".join(context_parts)

        except Exception as e:
            if self.verbose:
                print(f"Warning: Vector search failed: {e}")
            return "\nVector search unavailable."

    def _get_skills_summary(self):
        """
        Get a condensed summary of skills instead of full content to save tokens.

        Returns:
            str: Brief summary of available skills
        """
        if not self.skill_fetcher or not self.skill_fetcher.skills:
            return "No skills loaded."

        summary_parts = ["Available CockroachDB skills for reference:"]

        # Group skills by category
        categories = {}
        for skill_name in sorted(self.skill_fetcher.skills.keys()):
            category = skill_name.split('/')[0]
            if category not in categories:
                categories[category] = []
            skill_short_name = skill_name.split('/')[-1]
            categories[category].append(skill_short_name)

        # Build compact summary
        for category, skills in sorted(categories.items()):
            summary_parts.append(f"\n{category}: {', '.join(skills)}")

        summary_parts.append("\n\nNote: Follow CockroachDB best practices for query design, indexing, and schema design.")

        return "\n".join(summary_parts)

    def _handle_fetch_skill(self, tool_input):
        """
        Handle the fetch_skill tool - load a specific skill guide.

        Args:
            tool_input: dict with 'skill_name' key

        Returns:
            str: Skill content or error message
        """
        skill_name = tool_input.get("skill_name", "")

        if not self.skill_fetcher:
            return json.dumps({"error": "Skill fetcher not available"})

        if skill_name not in self.skill_fetcher.skills:
            available = list(self.skill_fetcher.skills.keys())
            return json.dumps({
                "error": f"Skill '{skill_name}' not found",
                "available_skills": available[:10]  # Show first 10 as examples
            })

        # Track that this skill was loaded
        if hasattr(self, '_loaded_skills'):
            self._loaded_skills.add(skill_name)

        # Return the skill content
        content = self.skill_fetcher.skills[skill_name]['content']

        if self.verbose:
            print(f"[Fetch Skill] Loaded skill: {skill_name}")
            print(f"[Fetch Skill] Content length: {len(content)} characters")
            print()

        return json.dumps({
            "skill_name": skill_name,
            "content": content
        })

    def _handle_complete_task(self, tool_input, user_task, start_time):
        """
        Handle the complete_task tool - store learning and return answer.

        Args:
            tool_input: dict with 'skills_that_helped' and 'answer' keys
            user_task: The original user task
            start_time: When the task started (for execution time)

        Returns:
            str: Confirmation message
        """
        skills_that_helped = tool_input.get("skills_that_helped", [])
        answer = tool_input.get("answer", "")

        # Get loaded vs. used skills
        loaded_skills = getattr(self, '_loaded_skills', set())
        used_skills = set(skills_that_helped)
        unused_skills = loaded_skills - used_skills

        # Display skill usage report
        # Color-coded in dark red for visual distinction (added 2026-04-05)
        # Shows which skills were actually helpful vs loaded but unused
        print()
        print("\033[31m" + "=" * 80 + "\033[0m")
        print("\033[31mSKILL USAGE REPORT\033[0m")
        print("\033[31m" + "=" * 80 + "\033[0m")

        if used_skills:
            print("\033[31m✓ Skills that helped complete this task:\033[0m")
            for skill in sorted(used_skills):
                print(f"\033[31m  • {skill}\033[0m")
        else:
            print("\033[31m✓ No specific skills were needed (answered from general knowledge)\033[0m")

        # Show unused skills to track Claude's skill selection accuracy
        # With zero-skill-preloading, this section rarely appears (skills are fetched on-demand)
        if unused_skills:
            print()
            print("\033[31m✗ Skills that were loaded but not used:\033[0m")
            for skill in sorted(unused_skills):
                print(f"\033[31m  • {skill}\033[0m")

        print("\033[31m" + "=" * 80 + "\033[0m")
        print()

        # Flush stdout to ensure report is displayed before answer
        # Fix added 2026-04-05: Prevents buffering issues where report appears after answer
        import sys
        sys.stdout.flush()

        # Store the query with only the skills that actually helped
        if self.use_query_learning and self.query_store:
            execution_time_ms = int((time.time() - start_time) * 1000)

            try:
                self.query_store.store_query(
                    query_text=user_task,
                    skills_used=skills_that_helped,
                    was_successful=True,
                    execution_time_ms=execution_time_ms
                )
                if self.verbose:
                    print(f"[Query Learning] Stored query with {len(skills_that_helped)} useful skills")
            except Exception as e:
                if self.verbose:
                    print(f"[Query Learning] Could not store query: {e}")

        return json.dumps({
            "status": "success",
            "skills_stored": skills_that_helped,
            "message": "Task completed and learning stored"
        })

    def run_task(self, user_task):
        """
        Execute a user task using Claude API with tool use.

        Args:
            user_task: Natural language description of the task

        Returns:
            str: Final response from Claude
        """
        # Track execution for learning
        start_time = time.time()
        skills_used = []

        # Track ALL skills loaded during this task
        self._loaded_skills = set()

        # Get skills recommendation if using query learning
        if self.use_query_learning and self.query_store:
            recommendation = self.query_store.get_skills_for_query(user_task)
            if recommendation['source'] == 'learned':
                skills_used = recommendation['skills']
                # Track these pre-loaded skills
                self._loaded_skills.update(skills_used)
            else:
                # Track default skills
                self._loaded_skills.update(self._get_default_skills())

        if self.verbose:
            print("=" * 80)
            print("Processing Task")
            print("=" * 80)
            print(f"Task: {user_task}\n")

        # Build initial messages
        messages = [
            {
                "role": "user",
                "content": user_task
            }
        ]

        # Tool use loop
        # Claude may call multiple tools in sequence to complete the task
        while True:
            # Call Claude API
            # Vertex AI uses different model names than standard Anthropic API
            # See: https://platform.claude.com/docs/en/build-with-claude/claude-on-vertex-ai
            if self.config.get("use_vertex_ai"):
                # For Vertex AI: claude-sonnet-4-6, claude-opus-4-6, etc.
                model_name = "claude-sonnet-4-6"
            else:
                # For standard Anthropic API: claude-sonnet-4-20250514, etc.
                model_name = "claude-sonnet-4-20250514"

            # Use discovered MCP tools + agent tools (fetch_skill, complete_task)
            # Build system prompt with relevant skills (vector search if enabled)
            response = self.claude.messages.create(
                model=model_name,
                max_tokens=4096,
                system=self._build_system_prompt(user_task=user_task),
                tools=self.mcp_tools + get_agent_tools(),  # Discovered MCP tools + agent tools
                messages=messages
            )

            # Check stop reason
            if response.stop_reason == "end_turn":
                # Claude is done, extract final response
                final_text = ""
                for block in response.content:
                    if block.type == "text":
                        final_text += block.text

                # Store successful query for learning
                if self.use_query_learning and self.query_store:
                    execution_time_ms = int((time.time() - start_time) * 1000)

                    # If no skills were used, store empty list (not defaults)
                    # This is correct - we learned that this query doesn't need skills!
                    if not skills_used:
                        skills_used = []

                    try:
                        self.query_store.store_query(
                            query_text=user_task,
                            skills_used=skills_used,
                            was_successful=True,
                            execution_time_ms=execution_time_ms
                        )
                        if self.verbose:
                            print(f"[Query Learning] Stored query for future learning")
                    except Exception as e:
                        if self.verbose:
                            print(f"[Query Learning] Could not store query: {e}")

                return final_text

            elif response.stop_reason == "tool_use":
                # Claude wants to use tools
                # Add assistant's response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute each tool call
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id

                        if self.verbose:
                            print(f"→ Claude is calling tool: {tool_name}")
                            print(f"  Input: {json.dumps(tool_input, indent=2)}")

                        # Handle agent-specific tools locally
                        if tool_name == "fetch_skill":
                            result = self._handle_fetch_skill(tool_input)
                        elif tool_name == "complete_task":
                            result = self._handle_complete_task(tool_input, user_task, start_time)
                            # Add result to tool_results and break out of loop
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result
                            })
                            # Task is complete - return the answer
                            messages.append({
                                "role": "user",
                                "content": tool_results
                            })
                            return tool_input.get("answer", "Task completed.")
                        else:
                            # Check if this is a write operation that needs confirmation
                            write_tools = {"create_database", "create_table", "insert_rows"}
                            if tool_name in write_tools and not self.auto_approve_writes:
                                # Ask for user confirmation before executing write operations
                                print(f"\n{Colors.DARK_ORANGE}⚠️  WRITE OPERATION REQUESTED{Colors.ENDC}")
                                print(f"{Colors.BOLD}Tool:{Colors.ENDC} {tool_name}")
                                print(f"{Colors.BOLD}Input:{Colors.ENDC} {json.dumps(tool_input, indent=2)}")

                                confirm = input(f"\n{Colors.BOLD}Execute this operation? (yes/no/all): {Colors.ENDC}").strip().lower()

                                if confirm in ['all', 'a']:
                                    # Auto-approve all future write operations in this session
                                    self.auto_approve_writes = True
                                    print(f"{Colors.WARNING}⚡ Auto-approving all future write operations this session{Colors.ENDC}")
                                    result = self.mcp_client.execute_tool_call(tool_name, tool_input)
                                    print(f"{Colors.OKGREEN}✓ Write operation completed{Colors.ENDC}\n")
                                elif confirm not in ['yes', 'y']:
                                    result = json.dumps({
                                        "error": "Operation cancelled by user",
                                        "message": "User declined to execute write operation"
                                    })
                                    print(f"{Colors.FAIL}✗ Operation cancelled{Colors.ENDC}\n")
                                else:
                                    # Execute MCP tool via MCP server
                                    result = self.mcp_client.execute_tool_call(tool_name, tool_input)
                                    print(f"{Colors.OKGREEN}✓ Write operation completed{Colors.ENDC}\n")
                            elif tool_name in write_tools and self.auto_approve_writes:
                                # Auto-approved - execute without prompting
                                print(f"{Colors.OKGREEN}⚡ Auto-approved: {tool_name}{Colors.ENDC}")
                                result = self.mcp_client.execute_tool_call(tool_name, tool_input)
                                print(f"{Colors.OKGREEN}✓ Write operation completed{Colors.ENDC}\n")
                            else:
                                # Execute read-only MCP tool via MCP server
                                result = self.mcp_client.execute_tool_call(tool_name, tool_input)

                        if self.verbose:
                            print(f"✓ Tool result received")
                            print()

                        # Add tool result to list
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue the loop - Claude will process the results

            else:
                # Unexpected stop reason
                print(f"Unexpected stop reason: {response.stop_reason}")
                return "Error: Unexpected response from Claude API"

    def interactive_mode(self):
        """
        Run the agent in interactive mode where the user can enter multiple tasks.
        """
        print("\n" + "=" * 80)
        print("CockroachDB Intelligent Agent")
        print("=" * 80)
        print()
        print("This agent can help you with CockroachDB tasks using natural language.")
        print("Examples:")
        print("  - Show me all databases")
        print("  - List tables in the defaultdb database")
        print("  - Run a query to check the CockroachDB version")
        print("  - What tables exist in my cluster?")
        print()
        print("Type 'quit' or 'exit' to stop.")
        print("=" * 80)
        print()

        while True:
            try:
                # Get user input
                user_input = input("Task: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break

                # Display the task with highlighting
                print_task_header(user_input)

                # Execute the task
                response = self.run_task(user_input)

                # Display the response
                print()
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break

            except Exception as e:
                print(f"\nERROR: {e}\n")

    def close(self):
        """Clean up resources."""
        self.mcp_client.close()


def main():
    """
    Main entry point for the agent.

    Usage:
        # Interactive mode
        python3 agent.py

        # Single task mode
        python3 agent.py "show me all databases"
    """
    # Create agent
    agent = CockroachDBAgent()

    try:
        if len(sys.argv) > 1:
            # Single task mode - task provided as command line argument
            task = " ".join(sys.argv[1:])

            # Display the task with highlighting
            print_task_header(task)

            response = agent.run_task(task)

            # Just print the response directly (clean output)
            print(response)
        else:
            # Interactive mode
            agent.interactive_mode()
    finally:
        agent.close()


if __name__ == "__main__":
    main()
