#!/usr/bin/env python3
"""
Create architecture diagram for aidemo2
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.lines as mlines

# Create figure
fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 16)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
color_user = '#E8F4F8'
color_agent = '#FFE6CC'
color_llm = '#E6CCE6'
color_storage = '#CCE6CC'
color_external = '#F0F0F0'
color_skill = '#FFE6E6'

# Helper function to draw boxes
def draw_box(ax, x, y, width, height, label, color, fontsize=11, bold=False):
    box = FancyBboxPatch((x, y), width, height,
                          boxstyle="round,pad=0.1",
                          edgecolor='black',
                          facecolor=color,
                          linewidth=2)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + width/2, y + height/2, label,
            ha='center', va='center',
            fontsize=fontsize, weight=weight,
            wrap=True)

# Helper function to draw arrows
def draw_arrow(ax, x1, y1, x2, y2, label='', style='->'):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle=style,
                           color='black',
                           linewidth=2,
                           mutation_scale=20)
    ax.add_patch(arrow)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y, label,
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray'),
                ha='center', va='center')

# Title
ax.text(8, 11.5, 'AIdemo2 Architecture - Intelligent CockroachDB Agent',
        ha='center', va='top', fontsize=18, weight='bold')

# === Layer 1: User ===
draw_box(ax, 6.5, 10, 3, 0.8, 'User', color_user, fontsize=12, bold=True)

# === Layer 2: Agent ===
draw_box(ax, 5.5, 8, 5, 1.2, 'Agent (agent.py)\nMain Orchestrator',
         color_agent, fontsize=12, bold=True)

# === Layer 3: Agent Components ===
# Query Store
draw_box(ax, 0.5, 6, 2.5, 1, 'Query Store\n(query_store.py)\nLearning & Similarity',
         color_agent, fontsize=10)

# Skill Fetcher
draw_box(ax, 3.5, 6, 2.5, 1, 'Skill Fetcher\n(skill_fetcher.py)\nGitHub SKILL.md',
         color_skill, fontsize=10)

# MCP Client
draw_box(ax, 6.5, 6, 2.5, 1, 'MCP Client\n(mcp_client.py)\nTool Executor',
         color_agent, fontsize=10)

# Ollama Embeddings
draw_box(ax, 9.5, 6, 2.5, 1, 'Ollama Embedding\nHash-based\n384-dim vectors',
         color_agent, fontsize=10)

# MCP Tools
draw_box(ax, 12.5, 6, 2.5, 1, 'MCP Tools\n+ Agent Tools\n(fetch_skill, complete_task)',
         color_agent, fontsize=10)

# === Layer 4: External Services ===
# Claude API (Vertex AI)
draw_box(ax, 1, 3.5, 3.5, 1.2, 'Claude API\n(Vertex AI)\nSonnet 4.6',
         color_llm, fontsize=11, bold=True)

# MCP Server
draw_box(ax, 5.5, 3.5, 3.5, 1.2, 'MCP Server\ncockroachlabs.cloud/mcp\nJSON-RPC + SSE',
         color_external, fontsize=11, bold=True)

# GitHub
draw_box(ax, 10, 3.5, 3.5, 1.2, 'GitHub\ncockroachdb-skills\n25 SKILL.md files',
         color_external, fontsize=11, bold=True)

# === Layer 5: Storage ===
# CockroachDB
draw_box(ax, 3.5, 1, 8, 1.5, 'CockroachDB Cluster (trs-demo)\n' +
         'ai_demo.query_history (embeddings, skills_used)\n' +
         'User databases (defaultdb, testdb, etc.)',
         color_storage, fontsize=11, bold=True)

# === Arrows - Request Flow ===
# User to Agent
draw_arrow(ax, 8, 10, 8, 9.2, '1. Natural language\nquery')

# Agent to Ollama
draw_arrow(ax, 10.5, 8, 10.5, 7, '2. Generate\nembedding')

# Agent to Query Store
draw_arrow(ax, 5.5, 8, 1.75, 7, '3. Find similar\nqueries')

# Query Store to CockroachDB
draw_arrow(ax, 1.75, 6, 5, 2.5, '4. Vector\nsimilarity\nsearch')

# Agent to Skill Fetcher (if needed)
draw_arrow(ax, 7.5, 8, 4.75, 7, '5. Load learned\nskills')

# Skill Fetcher to GitHub
draw_arrow(ax, 4.75, 6, 11.5, 4.7, '6. Fetch SKILL.md\n(if not cached)')

# Agent to Claude
draw_arrow(ax, 6, 8, 2.75, 4.7, '7. Prompt + Skills\n+ Tools')

# Claude calls MCP tools
draw_arrow(ax, 4.5, 3.5, 6.5, 7, '8. Tool calls\n(list_databases,\nfetch_skill, etc.)',
           style='<->')

# MCP Client to MCP Server
draw_arrow(ax, 7.5, 6, 7, 4.7, '9. Execute\nMCP tools')

# MCP Server to CockroachDB
draw_arrow(ax, 7, 3.5, 7, 2.5, '10. SQL\noperations')

# Results back to Agent
draw_arrow(ax, 4.5, 4.7, 6, 8, '11. Results +\nFinal answer', style='<-')

# Agent stores learning
draw_arrow(ax, 8.5, 8, 9, 2.5, '12. Store query\n+ useful skills')

# Results to User
draw_arrow(ax, 8, 9.2, 8, 10.8, '13. Answer +\nSkill Usage Report', style='<-')

# === Legend ===
legend_y = 0.3
legend_elements = [
    mpatches.Patch(color=color_user, label='User Interface'),
    mpatches.Patch(color=color_agent, label='Agent Components'),
    mpatches.Patch(color=color_llm, label='LLM Service'),
    mpatches.Patch(color=color_external, label='External Services'),
    mpatches.Patch(color=color_storage, label='Database Storage'),
    mpatches.Patch(color=color_skill, label='Skill Management')
]
ax.legend(handles=legend_elements, loc='lower center', ncol=6,
          frameon=True, fontsize=10, bbox_to_anchor=(0.5, -0.05))

# Add workflow description
workflow_text = """Key Features:
• Query Learning: Stores successful queries with embeddings, reuses skills for similar questions
• Dynamic Skill Loading: Fetches only needed SKILL.md files via fetch_skill tool
• Skill Usage Tracking: Reports which skills helped vs. which were loaded but unused
• Local Embeddings: Hash-based 384-dim vectors (no external API needed for similarity search)
• Progressive Learning: Gets smarter over time as query database grows"""

ax.text(8, -0.5, workflow_text, ha='center', va='top',
        fontsize=9, style='italic',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFFACD', alpha=0.8))

plt.tight_layout()
plt.savefig('architecture_diagram.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print("✓ Architecture diagram saved to: architecture_diagram.png")
