# Interactive wrapper scripts

These scripts are the easiest way to operate the project if you do not want to remember CLI commands.

## Commands

After installation, each helper is available as a CLI command directly on PATH:

| CLI command | Root script equivalent | What it does |
|---|---|---|
| `data-pipeline-flow-setup` | `python setup_project.py` | First-run setup and saved defaults |
| `data-pipeline-flow-make` | `python make_pipeline.py` | Render a PNG, SVG, PDF, or DOT using saved defaults |
| `data-pipeline-flow-inspect` | `python inspect_pipeline.py` | Run summary, validate, or both |
| `data-pipeline-flow-edit-exclusions` | `python edit_exclusions.py` | Manage ignored paths, names, and glob patterns |
| `data-pipeline-flow-manage-clusters` | `python manage_clusters.py` | Manage manual clusters |

Both forms work. The CLI commands work from any directory; the root scripts require you to be in the repo root.

## What gets remembered

Saved settings live in `pipeline_user_settings.yaml`.

By default, the main editable config lives in `user_configs/project_config.yaml`.

## Cluster entry style

When adding a cluster, enter one script path or folder path at a time.
Type `F` when you are finished.

This is meant to make multi-member clusters easy without forcing YAML edits for every small change.


## Path input rules

- You can enter repo-relative paths or absolute paths in the wrapper scripts.
- For the config location, you may give either a YAML file path or a folder path.
- If you give a folder, the wrapper creates `project_config.yaml` inside that folder automatically.
