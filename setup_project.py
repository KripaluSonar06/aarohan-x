from pathlib import Path

PROJECT_NAME = "aarohan-x"

files = [
    "README.md",
    "requirements.txt",
    ".env.example",
    ".gitignore",

    # config
    "config/__init__.py",
    "config/settings.py",
    "config/policy.py",
    "config/channel_costs.py",
    "config/logger.py",

    # core
    "core/__init__.py",
    "core/state.py",
    "core/graph.py",
    "core/orchestrator.py",
    "core/decision_engine.py",

    # agents
    "agents/__init__.py",
    "agents/ingestion_agent.py",
    "agents/diagnosis_agent.py",
    "agents/risk_gate_agent.py",
    "agents/ranking_agent.py",
    "agents/policy_agent.py",

    # execution agents
    "agents/execution/__init__.py",
    "agents/execution/silent_retry_agent.py",
    "agents/execution/link_generation_agent.py",
    "agents/execution/text_nudge_agent.py",
    "agents/execution/voice_call_agent.py",
    "agents/execution/checkout_retarget_agent.py",
    "agents/execution/scheduler_agent.py",

    # other agents
    "agents/settlement_agent.py",
    "agents/learning_agent.py",

    # models
    "models/__init__.py",
    "models/ranker_model.py",
    "models/checkout_ranker.py",
    "models/bandit_model.py",

    # services
    "services/__init__.py",
    "services/razorpay_client.py",
    "services/voice_service.py",
    "services/llm_service.py",
    "services/scheduler.py",

    # data
    "data/__init__.py",
    "data/synthetic_generator.py",
    "data/ground_truth.py",
    "data/customer_profiles.py",
    "data/batch_150.csv",
    "data/evaluation_results.json",

    # dashboard
    "dashboard/__init__.py",
    "dashboard/app.py",

    # dashboard components
    "dashboard/components/__init__.py",
    "dashboard/components/metrics.py",
    "dashboard/components/strategy_simulator.py",
    "dashboard/components/intervention_ladder.py",
    "dashboard/components/timeline.py",
    "dashboard/components/policy_center.py",
    "dashboard/components/exceptions.py",

    "dashboard/state_loader.py",
    "dashboard/style.css",

    # utils
    "utils/__init__.py",
    "utils/idempotency.py",
    "utils/audit.py",
    "utils/time_utils.py",
    "utils/db.py",
    "utils/validators.py",

    # scripts
    "scripts/generate_batch.py",
    "scripts/train_ranker.py",
    "scripts/run_batch.py",
    "scripts/evaluate.py",
    "scripts/demo_failure.py",

    # tests
    "tests/__init__.py",
    "tests/test_decision_engine.py",
    "tests/test_diagnosis.py",
    "tests/test_policy_gates.py",
    "tests/test_ptp_tracker.py",
    "tests/test_idempotency.py",
    "tests/test_checkout.py",
    "tests/test_learning_agent.py",

    # docs
    "docs/ARCHITECTURE.md",
    "docs/DECISIONS.md",
    "docs/FAILURE_MODES.md",
    "docs/METRICS.md",

    # logs
    "logs/.gitkeep",
]

def create_project():
    root = Path(PROJECT_NAME)
    root.mkdir(exist_ok=True)

    for relative_path in files:
        file_path = root / relative_path

        # Create parent directories
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if it doesn't already exist
        if not file_path.exists():
            file_path.touch()

    print(f"\n✅ Project structure created successfully at:")
    print(root.resolve())

    print(f"\n📁 Created {len(files)} files/folders.")

if __name__ == "__main__":
    create_project()