"""Backward-compat stub — 실제 구현은 infrastructure.orchestration.disclosure_orchestrator로 이동됨."""
from infrastructure.orchestration.disclosure_orchestrator import *  # noqa: F401,F403
from infrastructure.orchestration.disclosure_orchestrator import (  # noqa: F401
    build_documents_config_from_prepared_dir,
    build_disclosure_ingest_graph,
    get_disclosure_ingest_graph,
    get_disclosure_prepared_dir,
    run_disclosure_ingest_orchestrate,
)
