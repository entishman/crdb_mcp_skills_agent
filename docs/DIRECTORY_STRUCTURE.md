# Directory Structure - Cleanup (April 5, 2026)

## Summary

Reorganized project for better maintainability by separating code, documentation, and utilities.

**Latest Update:** All utility scripts and documentation files moved to their respective directories (April 5, 2026 - final cleanup)

---

## New Structure

```
aidemo2/
├── docs/                          # All documentation and presentations
│   ├── archive/                   # Archived documentation
│   │   └── README_old.md          # Original README
│   ├── *.md                       # Markdown documentation (22 files)
│   │   ├── README.md              # Main documentation
│   │   ├── ARCHITECTURE.md        # System architecture
│   │   ├── CHANGELOG.md           # Change history
│   │   ├── COCKROACHDB_SETUP.md   # OAuth/MCP setup
│   │   ├── REQUIREMENTS_WRITE_OPERATIONS.md  # Write ops docs
│   │   ├── SKILL_TEST_TASKS.md    # Testing tasks
│   │   └── ... (other docs)
│   ├── *.pptx                     # PowerPoint presentations
│   └── arch1.png                  # Architecture diagram
│
├── utilities/                     # Scripts for setup, testing, and generation
│   ├── create_*.py                # Presentation/diagram generators
│   ├── setup_ai_demo.py           # Database setup
│   ├── populate_skills_db.py      # Skill population
│   ├── index_skills.py            # Skill indexing
│   ├── create_query_table.py      # Table creation
│   ├── run_sample_tests.sh        # Sample test runner
│   ├── run_skill_tests.py         # Skill test runner
│   ├── test_skill_fetching.py     # Skill fetch tests
│   └── README.md                  # Utilities documentation
│
├── .cache/                        # Cached skill files
├── __pycache__/                   # Python bytecode
│
├── agent.py                       # Main agent (run this!)
├── mcp_client.py                  # MCP communication
├── mcp_tools.py                   # Tool definitions
├── ollama_embedding_manager.py    # Embeddings (768-dim)
├── query_store.py                 # Learning system
├── skill_fetcher.py               # Skill loading
├── embedding_manager.py           # Vertex AI embeddings (optional)
├── skills_vectorstore.py          # Vector search (optional)
│
├── config.json                    # Configuration (DO NOT COMMIT!)
├── config.template.json           # Configuration template
├── requirements.txt               # Python dependencies
└── .gitignore                     # Git ignore rules
```

---

## Root Directory - Core Files Only

### Required to Run Agent:

| File | Purpose | Required? |
|------|---------|-----------|
| `agent.py` | Main orchestrator | ✅ Yes |
| `mcp_client.py` | MCP server communication | ✅ Yes |
| `mcp_tools.py` | Tool definitions | ✅ Yes |
| `ollama_embedding_manager.py` | 768-dim embeddings | ✅ Yes |
| `query_store.py` | Learning/similarity search | ✅ Yes |
| `skill_fetcher.py` | Load SKILL.md files | ✅ Yes |
| `embedding_manager.py` | Vertex AI embeddings | ⚠️  Vector search mode only |
| `skills_vectorstore.py` | Vector skill search | ⚠️  Vector search mode only |

### Configuration:
| File | Purpose |
|------|---------|
| `config.json` | Database, API keys, settings |
| `requirements.txt` | Python dependencies |

---

## docs/ Directory - All Documentation

### README & Guides:
- `README.md` - Main project documentation
- `ARCHITECTURE.md` - System architecture (UPDATED)
- `RECENT_CHANGES.md` - Quick reference for recent updates

### Change Documentation:
- `CHANGELOG.md` - Detailed change history
- `ARCHITECTURE_UPDATES.md` - Architecture doc updates
- `PRESENTATION_UPDATES.md` - PowerPoint/diagram updates
- `DIRECTORY_STRUCTURE.md` - This file (NEW)

### Optimization Documentation:
- `OPTIMIZATIONS_2026-04-04.md` - Performance improvements
- `UI_IMPROVEMENTS_2026-04-05.md` - Color-coded output

### Legacy/Alternative Docs:
- `README_old.md` - Original README
- `SETUP_VECTOR_SEARCH.md` - Vector search setup
- `VECTOR_SEARCH_README.md` - Vector search details
- `COMMENTS_*.md` - Detailed code explanations
- `DOCUMENTATION_SUMMARY.md` - Summary of all docs

### Presentations:
- `demo_for_humanx.pptx` - Main demo presentation (UPDATED)
- `demo_for_humanx_backup.pptx` - Backup before updates
- `AIdemo2_Presentation.pptx` - Original presentation

### Diagrams:
- `arch1.png` - Architecture diagram (UPDATED with 768-dim)

---

## utilities/ Directory - Setup & Generation Scripts

### Diagram/Presentation Generators:
| File | Purpose |
|------|---------|
| `create_arch1_diagram.py` | Generate arch1.png (UPDATED) |
| `create_architecture_diagram.py` | Alternative diagram generator |
| `create_demo_presentation.py` | Generate demo PowerPoint |
| `create_presentation.py` | Alternative presentation generator |

### Database Setup:
| File | Purpose |
|------|---------|
| `setup_ai_demo.py` | Create ai_demo database schema |
| `create_query_table.py` | Create query_history table |
| `populate_skills_db.py` | Load skills to database |
| `index_skills.py` | Index skills for vector search |

### Documentation:
| File | Purpose |
|------|---------|
| `README.md` | Utilities documentation |

---

## Rationale for Organization

### Before Cleanup:
```
Root directory: 25+ files (.py, .md, .pptx all mixed)
Hard to find what you need
Unclear which Python files are needed to run vs for setup
```

### After Cleanup:
```
Root directory: 8 core Python files + config
docs/: All documentation in one place
utilities/: All setup/generation scripts separate
```

**Benefits:**
1. ✅ **Clearer** - Core files vs documentation vs utilities
2. ✅ **Faster** - Find what you need quickly
3. ✅ **Safer** - Less risk of editing wrong file
4. ✅ **Professional** - Better project organization

---

## Quick Reference

### To Run the Agent:
```bash
python agent.py "your question"
```

### To Read Documentation:
```bash
cd docs/
# Main docs:
cat README.md
cat ARCHITECTURE.md
cat RECENT_CHANGES.md
```

### To Regenerate Diagrams:
```bash
cd utilities/
python create_arch1_diagram.py
# Output: ../docs/arch1.png
```

### To Setup Database:
```bash
cd utilities/
python setup_ai_demo.py
python populate_skills_db.py
```

---

## Files Moved

### Initial Cleanup (Earlier):
From Root → docs/:
✅ Core documentation (13 MD files)
✅ PowerPoint presentations (3 files)  
✅ `arch1.png` diagram

From Root → utilities/:
✅ `create_arch1_diagram.py`  
✅ `create_architecture_diagram.py`  
✅ `create_demo_presentation.py`  
✅ `create_presentation.py`

### Final Cleanup (April 5, 2026):
From Root → utilities/:
✅ `run_sample_tests.sh` - Sample test runner script
✅ `run_skill_tests.py` - Skill test runner  
✅ `test_skill_fetching.py` - Skill fetching tests

From Root → docs/:
✅ `COCKROACHDB_SETUP.md` - OAuth/MCP configuration guide
✅ `MANUAL_SKILL_TEST_GUIDE.md` - Manual testing instructions
✅ `POWERPOINT_SLIDES_READY_TO_ADD.md` - Slide content
✅ `PRESENTATION_UPDATES.md` - Presentation update notes
✅ `REQUIREMENTS_WRITE_OPERATIONS.md` - Write operations docs
✅ `SKILL_TEST_TASKS.md` - 20 skill testing tasks

From docs/ → docs/archive/:
✅ `README_old.md` - Original README (archived)

### Stayed in Root (Core Runtime Files Only):
✅ All core agent files (8 Python files)  
✅ Configuration files (config.json, config.template.json)
✅ Dependencies file (requirements.txt)
✅ .gitignore

---

## Verification

### Agent Still Works: ✅
```bash
$ python agent.py "how many databases?"
[Task displays in dark blue]
[Skill report in dark red]
Answer: 3 databases...
```

### All Imports Work: ✅
- No broken imports after file moves
- All relative paths still correct

### Documentation Accessible: ✅
- All docs in one organized location
- Cross-references still valid

---

## Next Steps for Future Cleanup

Potential future improvements:
1. Move `__pycache__/` to build/ directory (if needed)
2. Add tests/ directory for unit tests
3. Add examples/ directory for sample configs
4. Consider scripts/ directory for one-off admin tasks

---

**Date:** April 5, 2026  
**Files Moved:** 20+ files  
**Status:** ✅ Complete and verified  
**Agent Status:** ✅ Working perfectly
