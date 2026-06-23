#!/usr/bin/env python3
"""
Create comprehensive architecture diagram (arch1.png)
Shows all system components and their interactions

UPDATE HISTORY:
- 2026-04-05: Updated to reflect 768-dim embeddings (all-mpnet-base-v2)
- 2026-04-05: Updated query_history table to show 768-dim vectors
- Original: Created with 384-dim all-MiniLM-L6-v2 model
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.lines as mlines

# Create figure
fig, ax = plt.subplots(figsize=(18, 14))
ax.set_xlim(0, 18)
ax.set_ylim(0, 14)
ax.axis('off')

# Define colors
color_user = '#E8F4F8'
color_agent = '#FFE6CC'
color_llm = '#E6CCE6'
color_db = '#CCE6CC'
color_external = '#F0F0F0'
color_embedding = '#FFE6E6'

# Helper functions
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

def draw_arrow(ax, x1, y1, x2, y2, label='', style='->', color='black', lw=2, dashed=False):
    linestyle = '--' if dashed else '-'
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle=style,
                           color=color,
                           linewidth=lw,
                           linestyle=linestyle,
                           mutation_scale=25)
    ax.add_patch(arrow)
    if label:
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mid_x, mid_y, label,
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray'),
                ha='center', va='center')

# Title
ax.text(9, 13.3, 'AIdemo2 Complete Architecture',
        ha='center', va='top', fontsize=22, weight='bold')
ax.text(9, 12.8, 'Self-Learning CockroachDB Agent with Query-Based Learning',
        ha='center', va='top', fontsize=14, style='italic')

# ===== Layer 1: User =====
draw_box(ax, 7.5, 11.5, 3, 0.8, 'User\nNatural Language Query', color_user, 12, True)

# ===== Layer 2: Agent Core =====
draw_box(ax, 6, 9.5, 6, 1.3, 'Agent (agent.py)\nOrchestrator & Learning Engine',
         color_agent, 13, True)

# ===== Layer 3: Agent Components =====
# Query Store
draw_box(ax, 0.5, 7, 2.5, 1.2, 'Query Store\n(query_store.py)\nSimilarity Search\n& Learning',
         color_agent, 10)

# Skill Fetcher
draw_box(ax, 3.5, 7, 2.5, 1.2, 'Skill Fetcher\n(skill_fetcher.py)\nSKILL.md Loader',
         color_embedding, 10)

# Embedding Manager (Updated 2026-04-04: 768-dim model)
draw_box(ax, 6.5, 7, 2.5, 1.2, 'Embedding Manager\nsentence-transformers\nall-mpnet-base-v2\n(768-dim)',
         color_embedding, 10)

# MCP Client
draw_box(ax, 9.5, 7, 2.5, 1.2, 'MCP Client\n(mcp_client.py)\nTool Executor',
         color_agent, 10)

# MCP Tools
draw_box(ax, 12.5, 7, 2.5, 1.2, 'MCP Tools\nAgent Tools:\nfetch_skill\ncomplete_task',
         color_agent, 9)

# Skill Cache
draw_box(ax, 15.5, 7, 2, 1.2, 'Local Cache\n.cache/\n(fallback)',
         color_external, 9)

# ===== Layer 4: LLMs & External Services =====
# Claude (Vertex AI)
draw_box(ax, 0.5, 4.5, 3.5, 1.3, 'Claude API\n(Vertex AI)\nSonnet 4.6\nRegion: global',
         color_llm, 11, True)

# Ollama (placeholder for future)
draw_box(ax, 4.5, 4.5, 3, 1.3, 'Ollama LLM\n(Future)\nLocal embeddings\nnomic-embed-text',
         color_llm, 10)

# MCP Server
draw_box(ax, 8, 4.5, 4, 1.3, 'CockroachDB MCP Server\ncockroachlabs.cloud/mcp\nJSON-RPC + SSE',
         color_external, 11, True)

# GitHub
draw_box(ax, 12.5, 4.5, 3, 1.3, 'GitHub\ncockroachdb-skills\n25 SKILL.md files',
         color_external, 10)

# ===== Layer 5: CockroachDB Cluster =====
# Main cluster box
draw_box(ax, 2, 0.5, 14, 3.3, '', color_db, 10)
ax.text(9, 3.4, 'CockroachDB Cluster (trs-demo)',
        ha='center', fontsize=13, weight='bold')

# Database: ai_demo
draw_box(ax, 2.5, 1.8, 4, 1.3, 'Database: ai_demo\n(Learning Storage)',
         '#B3E5B3', 10, True)

# Table: query_history (Updated 2026-04-04: 768-dim)
draw_box(ax, 2.7, 0.9, 1.8, 0.7, 'query_history\n768-dim vectors\nHNSW index',
         '#99D699', 8)

# Table: skills
draw_box(ax, 4.7, 0.9, 1.8, 0.7, 'skills\nSKILL.md content\n25 files',
         '#99D699', 8)

# Database: testdb
draw_box(ax, 7, 1.8, 4, 1.3, 'Database: testdb\n(User Data)',
         '#B3E5B3', 10, True)

# User tables
draw_box(ax, 7.2, 0.9, 1.8, 0.7, 'User Tables\nt1, t2, etc.',
         '#99D699', 8)

# Cluster metadata
draw_box(ax, 9.2, 0.9, 1.8, 0.7, 'Cluster Metadata\nRanges, Nodes',
         '#99D699', 8)

# Other databases
draw_box(ax, 11.5, 1.8, 4, 1.3, 'Database: defaultdb\n(System DB)',
         '#B3E5B3', 10, True)

# System tables
draw_box(ax, 11.7, 0.9, 3.6, 0.7, 'System Tables\ncrdb_internal, pg_catalog',
         '#99D699', 8)

# ===== Data Flow Arrows =====

# User to Agent
draw_arrow(ax, 9, 11.5, 9, 10.8, '1. Query', color='#0066CC', lw=2.5)

# Agent to Embedding Manager
draw_arrow(ax, 7.75, 9.5, 7.75, 8.2, '2. Generate\nembedding', color='#CC6600')

# Agent to Query Store
draw_arrow(ax, 6, 10, 1.75, 8.2, '3. Find similar\nqueries', color='#CC6600')

# Query Store to query_history
draw_arrow(ax, 1.75, 7, 3.6, 3.8, '4. Vector\nsimilarity\nsearch', color='#009900')

# Agent to Skill Fetcher
draw_arrow(ax, 8, 9.5, 4.75, 8.2, '5. Load\nskills', color='#CC6600')

# Skill Fetcher to skills table
draw_arrow(ax, 4.75, 7, 5.6, 3.8, '6a. DB', color='#009900')

# Skill Fetcher to cache (fallback)
draw_arrow(ax, 6, 7.6, 15.5, 7.6, '6b. Cache\n(fallback)', color='#999999', dashed=True)

# Skill Fetcher to GitHub (fallback)
draw_arrow(ax, 5, 7, 13.5, 5.8, '6c. GitHub\n(fallback)', color='#999999', dashed=True)

# Agent to Claude
draw_arrow(ax, 6, 10, 2.25, 5.8, '7. Prompt +\nSkills + Tools', color='#9900CC', lw=2.5)

# Claude to MCP Client (tool calls)
draw_arrow(ax, 4, 5.5, 10, 8.2, '8. Tool calls', color='#9900CC', style='<->')

# MCP Client to MCP Server
draw_arrow(ax, 10, 7, 10, 5.8, '9. Execute\nMCP tools', color='#0066CC')

# MCP Server to testdb
draw_arrow(ax, 10, 4.5, 9, 3.8, '10. SQL queries\n(READ-ONLY)', color='#0066CC', lw=2.5)

# Results back through chain
draw_arrow(ax, 11, 5.5, 11, 8.2, '11. Results', color='#0066CC', style='<-')

# Store learning
draw_arrow(ax, 12, 10, 3.6, 2.5, '12. Store:\nquery + skills', color='#009900', lw=2.5)

# Answer to user
draw_arrow(ax, 10.5, 10.8, 10.5, 11.5, '13. Answer +\nSkill Report', color='#0066CC', lw=2.5, style='<-')

# ===== Legend =====
legend_elements = [
    mpatches.Patch(color=color_user, label='User Interface', edgecolor='black'),
    mpatches.Patch(color=color_agent, label='Agent Components', edgecolor='black'),
    mpatches.Patch(color=color_llm, label='LLM Services', edgecolor='black'),
    mpatches.Patch(color=color_embedding, label='Embeddings & Skills', edgecolor='black'),
    mpatches.Patch(color=color_external, label='External Services', edgecolor='black'),
    mpatches.Patch(color=color_db, label='CockroachDB Storage', edgecolor='black'),
]
ax.legend(handles=legend_elements, loc='lower center', ncol=6,
          frameon=True, fontsize=10, bbox_to_anchor=(0.5, -0.08))

# Add key features box
features_text = """Key Features:
• Query-based learning with semantic embeddings
• 95% token savings vs loading all skills
• HNSW index for fast similarity search (O(log n))
• Skills stored in CockroachDB (persistent, shared)
• Read-only enforcement (safe by design)
• Progressive learning (gets smarter over time)"""

ax.text(16.5, 11, features_text,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFFACD',
                  edgecolor='black', linewidth=1.5))

plt.tight_layout()
plt.savefig('arch1.png', dpi=300, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print("✓ Architecture diagram created: arch1.png")
