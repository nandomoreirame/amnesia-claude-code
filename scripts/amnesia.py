#!/usr/bin/env python3
"""Amnesia CLI — deterministic memory operations for Claude Code."""
import argparse, json, sys
from pathlib import Path

# Ensure project root is in sys.path so `scripts.*` imports work when running as a script
_here = Path(__file__).resolve().parent.parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

def ok(data): print(json.dumps({"data": data, "error": None}, ensure_ascii=False))
def err(msg, file=""): print(json.dumps({"data": None, "error": msg, "file": file}, ensure_ascii=False)); sys.exit(1)

def root(args):
    from scripts.paths import get_project_root
    return get_project_root(getattr(args, "project_root", None))

def cmd_entity_load(args):
    from scripts.entity import load_entity
    try:
        data = load_entity(args.name, root(args))
        ok({"found": data is not None, "entity": args.name, **(data or {})})
    except ValueError as e: err(str(e), f".claude/amnesia/memory/{args.name}.json")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_list(args):
    from scripts.entity import list_entities
    try: ok(list_entities(root(args)))
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_diff(args):
    from scripts.entity import diff_entity
    try: ok(diff_entity(args.name, json.loads(args.updates_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid updates_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_save(args):
    from scripts.entity import save_entity
    try: ok(save_entity(args.name, json.loads(args.updates_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid updates_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_project_load(args):
    from scripts.project import load_project
    try: ok(load_project(args.name, root(args)))
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_project_save(args):
    from scripts.project import save_project
    try: ok(save_project(args.name, json.loads(args.entry_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid entry_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_sync(args):
    from scripts.native_memory import resolve_native_memory_dir, generate_sync_report
    r = root(args)
    native_dir = resolve_native_memory_dir(str(r))
    try:
        report = generate_sync_report(r, native_dir)
        ok(report)
    except Exception as e:
        err(f"sync_error: {e}")

def cmd_list(args):
    from scripts.entity import list_entities
    from scripts.paths import get_projects_dir
    r = root(args)
    pd = get_projects_dir(r)
    projects = [d.name for d in pd.iterdir() if d.is_dir()] if pd.exists() else []
    ok({"entities": list_entities(r), "projects": projects})

def _add_root_flag(parser):
    """Add --project-root to a parser without overriding already-parsed values."""
    parser.add_argument("--project-root", default=argparse.SUPPRESS)

def main():
    p = argparse.ArgumentParser(prog="amnesia")
    p.add_argument("--project-root", default=None)
    sub = p.add_subparsers(dest="command", required=True)

    ep = sub.add_parser("entity"); _add_root_flag(ep)
    es = ep.add_subparsers(dest="subcommand", required=True)
    for name, func, extra in [("load", cmd_entity_load, ["name"]), ("list", cmd_entity_list, []),
                               ("diff", cmd_entity_diff, ["name", "updates_json"]),
                               ("save", cmd_entity_save, ["name", "updates_json"])]:
        sp = es.add_parser(name); _add_root_flag(sp); sp.set_defaults(func=func)
        for a in extra: sp.add_argument(a)

    pp = sub.add_parser("project"); _add_root_flag(pp)
    ps = pp.add_subparsers(dest="subcommand", required=True)
    for name, func, extra in [("load", cmd_project_load, ["name"]), ("save", cmd_project_save, ["name", "entry_json"])]:
        sp = ps.add_parser(name); _add_root_flag(sp); sp.set_defaults(func=func)
        for a in extra: sp.add_argument(a)

    lp = sub.add_parser("list"); _add_root_flag(lp); lp.set_defaults(func=cmd_list)
    sp_sync = sub.add_parser("sync"); _add_root_flag(sp_sync); sp_sync.set_defaults(func=cmd_sync)

    args = p.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
