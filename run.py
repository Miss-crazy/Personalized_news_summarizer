"""
run.py
CLI for Phase 1 + Phase 2 + Phase 3 + Phase 4.

Commands
--------
  python run.py --ingest              Run ingestion pipeline once
  python run.py --process             Run processing + sync to ChromaDB
  python run.py --sync-chroma         Push all SQLite clusters → ChromaDB
  python run.py --ask "query"         Ask a question via RAG
  python run.py --rag-repl            Interactive RAG session
  python run.py --pask USER "query"   Personalised RAG ask
  python run.py --feedback U CID SIG  Send feedback signal
  python run.py --profile USER        Show a user's preference weights
  python run.py --scheduler           Start continuous scheduler
  python run.py --stats               Print DB stats
  python run.py --show-clusters       Print all clusters with summaries
  python run.py --chroma-stats        Print ChromaDB collection stats
"""

import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from storage.database import init_db, article_count, cluster_count, fetch_all_clusters


# ── Command implementations ───────────────────────────────────────────────────

def cmd_ingest():
    from ingestion.pipeline import run_pipeline
    init_db()
    results = run_pipeline()
    db = results.get("db", {})
    print(f"\nIngestion complete.")
    print(f"  Total articles   : {db.get('total', '?')}")
    print(f"  Unprocessed      : {db.get('unprocessed', '?')}")


def cmd_process():
    from processing.pipeline import run_processing_pipeline
    from storage.vector_store import sync_from_db
    init_db()
    results = run_processing_pipeline(force=True)
    print(f"\nProcessing complete.")
    print(f"  Articles processed : {results.get('articles_processed', 0)}")
    print(f"  Clusters created   : {results.get('clusters_created', 0)}")
    print(f"  Total clusters     : {results.get('total_clusters', 0)}")
    print("\nSyncing clusters to ChromaDB...")
    synced = sync_from_db()
    print(f"  Synced {synced} cluster(s) to ChromaDB.")


def cmd_sync_chroma():
    from storage.vector_store import sync_from_db, collection_stats
    init_db()
    print("Syncing all clusters from SQLite → ChromaDB...")
    synced = sync_from_db()
    stats  = collection_stats()
    print(f"  Synced    : {synced} cluster(s)")
    print(f"  Chroma DB : {stats['doc_count']} total docs  ({stats['persist_dir']})")


def cmd_ask(query: str):
    from rag.chain import ask
    init_db()
    print(f"\nQ: {query}\n")
    result = ask(query)
    print(f"A: {result.answer}")
    if result.sources:
        print("\nSources used:")
        for s in result.sources:
            print(f"  • [{s['similarity']:.0%}] {s['label']}")
    else:
        print("\n(No relevant sources found in the database.)")


def cmd_rag_repl():
    from rag.chain import interactive_session
    init_db()
    interactive_session()


def cmd_personalised_ask(query: str, user_id: str):
    from rag.chain import personalised_ask
    init_db()
    print(f"\nQ: {query}  [user: {user_id}]\n")
    result = personalised_ask(query, user_id=user_id)
    print(f"A: {result.answer}")
    if result.sources:
        print("\nSources (personalised ranking):")
        for s in result.sources:
            score  = s.get("personalised_score", s["similarity"])
            weight = s.get("user_weight", 0.0)
            print(f"  • [{score:.0%}] {s['label']}  (pref weight: {weight:.3f})")
    else:
        print("\n(No relevant sources found in the database.)")


def cmd_feedback(user_id: str, cluster_id: int, signal: str, dwell: float = 0.0):
    from personalization.feedback_handler import process_feedback
    init_db()
    result = process_feedback(user_id, cluster_id, signal, dwell_seconds=dwell)
    print(f"\nFeedback processed:")
    print(f"  User          : {result['user_id']}")
    print(f"  Cluster       : {result['cluster_id']}")
    print(f"  Signal        : {result['signal']}")
    print(f"  Active weights: {result['weights_updated']}")


def cmd_profile(user_id: str):
    from storage.user_profiles import get_or_create_profile
    init_db()
    profile = get_or_create_profile(user_id)
    weights = profile["weights"]
    print(f"\n── Profile: {user_id} ────────────────────")
    if not weights:
        print("  No preferences recorded yet.")
    else:
        for cid, w in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
            bar  = "▓" * int(abs(w) * 20)
            sign = "+" if w >= 0 else "-"
            print(f"  Cluster {cid:4d}  {sign}{abs(w):.3f}  {bar}")
    print(f"\n  Updated: {profile['updated_at'][:19]}")


def cmd_chroma_stats():
    from storage.vector_store import collection_stats
    stats = collection_stats()
    print(f"\n── ChromaDB Stats ──────────────────────")
    print(f"  Collection  : {stats['collection']}")
    print(f"  Persist dir : {stats['persist_dir']}")
    print(f"  Doc count   : {stats['doc_count']}")


def cmd_stats():
    init_db()
    a = article_count()
    c = cluster_count()
    print(f"\n── DB Stats ─────────────────────────")
    print(f"  Articles total      : {a['total']}")
    print(f"  Articles unprocessed: {a['unprocessed']}")
    print(f"  Clusters total      : {c}")


def cmd_show_clusters():
    init_db()
    clusters = fetch_all_clusters()
    if not clusters:
        print("No clusters yet. Run: python run.py --process")
        return
    print(f"\n── {len(clusters)} Cluster(s) ──────────────────────")
    for cl in clusters:
        print(f"\n[{cl['id']}] {cl['label']}  ({cl['article_count']} articles)")
        summary = cl['summary']
        if summary:
            words = summary.split()
            line, lines = [], []
            for w in words:
                if sum(len(x) + 1 for x in line) + len(w) > 76:
                    lines.append(" ".join(line))
                    line = []
                line.append(w)
            if line:
                lines.append(" ".join(line))
            for ln in lines:
                print(f"    {ln}")
        print(f"    Created: {cl['created_at'][:19]}")


def cmd_scheduler():
    from scheduler.jobs import start_scheduler
    start_scheduler()


# ── main() ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Personalized News Summarizer")
    group = parser.add_mutually_exclusive_group(required=True)

    # Phase 1
    group.add_argument("--ingest",
                       action="store_true",
                       help="Run ingestion pipeline once")
    # Phase 2
    group.add_argument("--process",
                       action="store_true",
                       help="Run processing (embed + cluster + summarise) once")
    # Phase 3
    group.add_argument("--sync-chroma",
                       action="store_true",
                       help="Sync all SQLite clusters → ChromaDB")
    group.add_argument("--ask",
                       type=str,
                       metavar="QUERY",
                       help="Ask a plain RAG question, e.g. --ask 'AI news'")
    group.add_argument("--rag-repl",
                       action="store_true",
                       help="Start an interactive RAG session")
    group.add_argument("--chroma-stats",
                       action="store_true",
                       help="Show ChromaDB collection stats")
    # Phase 4
    group.add_argument("--pask",
                       nargs=2,
                       metavar=("USER_ID", "QUERY"),
                       help="Personalised ask, e.g. --pask alice 'AI regulation'")
    group.add_argument("--feedback",
                       nargs=3,
                       metavar=("USER_ID", "CLUSTER_ID", "SIGNAL"),
                       help="Send feedback, e.g. --feedback alice 7 thumbs_up")
    group.add_argument("--profile",
                       type=str,
                       metavar="USER_ID",
                       help="Show a user's preference weights, e.g. --profile alice")
    # Shared
    group.add_argument("--scheduler",
                       action="store_true",
                       help="Start continuous dual-loop scheduler")
    group.add_argument("--stats",
                       action="store_true",
                       help="Show DB stats (articles + clusters)")
    group.add_argument("--show-clusters",
                       action="store_true",
                       help="Print all clusters with summaries")

    args = parser.parse_args()

    # ── Route ──────────────────────────────────────────────────
    if args.ingest:
        cmd_ingest()
    elif args.process:
        cmd_process()
    elif args.sync_chroma:
        cmd_sync_chroma()
    elif args.ask:
        cmd_ask(args.ask)
    elif args.rag_repl:
        cmd_rag_repl()
    elif args.chroma_stats:
        cmd_chroma_stats()
    elif args.pask:
        user_id, query = args.pask
        cmd_personalised_ask(query, user_id=user_id)
    elif args.feedback:
        user_id, cluster_id, signal = args.feedback
        cmd_feedback(user_id, int(cluster_id), signal)
    elif args.profile:
        cmd_profile(args.profile)
    elif args.scheduler:
        cmd_scheduler()
    elif args.stats:
        cmd_stats()
    elif args.show_clusters:
        cmd_show_clusters()


if __name__ == "__main__":
    main()
