"""Agent execution time benchmarks.

Measures performance of AI agents: trust scoring, moderation, health scoring,
reputation system, escalation workflow, and queue optimization.

Note: Some agents require optional dependencies (langchain_core, structlog).
Tests for those agents are skipped if dependencies are missing.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import time
from pathlib import Path

import pytest

from .conftest import run_benchmark, run_async_benchmark


def _load_standalone_module(module_name: str, file_path: str):
    """Load a standalone .py file as a module, bypassing package __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        del sys.modules[module_name]
        return None


# Try to load standalone agent modules
_AGENTS_DIR = Path(__file__).parent.parent.parent / "src" / "gated_communities" / "agents"

_health_scorer = _load_standalone_module(
    "health_scorer_standalone",
    str(_AGENTS_DIR / "community_health_scorer.py"),
)

_reputation_system = _load_standalone_module(
    "reputation_system_standalone",
    str(_AGENTS_DIR / "reputation_system.py"),
)

_escalation_workflow = _load_standalone_module(
    "escalation_workflow_standalone",
    str(_AGENTS_DIR / "escalation_workflow.py"),
)

# Try to import trust scorer (requires member_verification package)
try:
    from gated_communities.agents.member_verification.trust_scorer import TrustScorerAgent
    _trust_scorer_available = True
except (ImportError, ModuleNotFoundError):
    TrustScorerAgent = None
    _trust_scorer_available = False

# Try to import auto moderator (requires langchain_core)
try:
    from gated_communities.agents.moderation_queue.auto_moderator import AutoModeratorAgent
    _auto_moderator_available = True
except (ImportError, ModuleNotFoundError):
    AutoModeratorAgent = None
    _auto_moderator_available = False


class TestTrustScorerAgent:
    """Benchmark trust scorer agent performance."""

    @pytest.fixture
    def trust_scorer(self):
        if not _trust_scorer_available:
            pytest.skip("TrustScorerAgent not available (missing dependencies)")
        return TrustScorerAgent()

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    def test_trust_score_calculation(self, trust_scorer):
        """Benchmark trust score calculation."""
        input_data = {
            "member_id": "user_123",
            "include_history": True,
            "factors": None,
        }
        result = run_async_benchmark(
            lambda: trust_scorer.run(input_data), iterations=50
        )
        assert result["avg_ms"] < 100, f"Trust scoring too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    def test_trust_score_without_history(self, trust_scorer):
        """Benchmark trust score calculation without history."""
        input_data = {
            "member_id": "user_456",
            "include_history": False,
            "factors": None,
        }
        result = run_async_benchmark(
            lambda: trust_scorer.run(input_data), iterations=50
        )
        assert result["avg_ms"] < 100, f"Trust scoring (no history) too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    def test_trust_score_with_specific_factors(self, trust_scorer):
        """Benchmark trust score calculation with specific factors."""
        input_data = {
            "member_id": "user_789",
            "include_history": True,
            "factors": ["account_age", "verification_status"],
        }
        result = run_async_benchmark(
            lambda: trust_scorer.run(input_data), iterations=50
        )
        assert result["avg_ms"] < 100, f"Trust scoring (specific factors) too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    def test_trust_score_health_check(self, trust_scorer):
        """Benchmark trust scorer health check."""
        result = run_async_benchmark(
            lambda: trust_scorer.health_check(), iterations=100
        )
        assert result["avg_ms"] < 10, f"Health check too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    def test_trust_score_capabilities(self, trust_scorer):
        """Benchmark getting agent capabilities."""
        result = run_benchmark(
            lambda: trust_scorer.get_capabilities(), iterations=100
        )
        assert result["avg_ms"] < 10, f"Get capabilities too slow: {result['avg_ms']}ms"


class TestCommunityHealthScorer:
    """Benchmark community health scorer performance."""

    @pytest.fixture(autouse=True)
    def check_available(self):
        if _health_scorer is None:
            pytest.skip("community_health_scorer not available")

    def test_health_score_calculation(self):
        """Benchmark community health score calculation."""
        result = run_benchmark(
            lambda: _health_scorer.calculate_health_score("comm_alpha"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Health score calc too slow: {result['avg_ms']}ms"

    def test_health_score_unknown_community(self):
        """Benchmark health score for unknown community (generates data)."""
        result = run_benchmark(
            lambda: _health_scorer.calculate_health_score("unknown_comm"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Health score (unknown) too slow: {result['avg_ms']}ms"

    def test_identify_risks(self):
        """Benchmark risk identification."""
        result = run_benchmark(
            lambda: _health_scorer.identify_risks("comm_beta"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Risk identification too slow: {result['avg_ms']}ms"

    def test_get_health_metrics(self):
        """Benchmark getting health metrics."""
        result = run_benchmark(
            lambda: _health_scorer.get_health_metrics("comm_gamma"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Get health metrics too slow: {result['avg_ms']}ms"

    def test_score_community_health(self):
        """Benchmark scoring community health."""
        result = run_benchmark(
            lambda: _health_scorer.score_community_health("comm_delta"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Score community health too slow: {result['avg_ms']}ms"

    def test_flag_unhealthy_community(self):
        """Benchmark flagging unhealthy community."""
        result = run_benchmark(
            lambda: _health_scorer.flag_unhealthy_community("comm_alpha"), iterations=100
        )
        assert result["avg_ms"] < 50, f"Flag unhealthy too slow: {result['avg_ms']}ms"

    def test_multiple_communities_health_check(self):
        """Benchmark health checks for multiple communities."""
        community_ids = ["comm_alpha", "comm_beta", "comm_gamma", "comm_delta"]

        def check_all():
            for cid in community_ids:
                _health_scorer.calculate_health_score(cid)

        result = run_benchmark(check_all, iterations=50)
        assert result["avg_ms"] < 200, f"Multi-community health check too slow: {result['avg_ms']}ms"


class TestReputationSystem:
    """Benchmark reputation system performance."""

    @pytest.fixture(autouse=True)
    def check_available(self):
        if _reputation_system is None:
            pytest.skip("reputation_system not available")

    def test_calculate_reputation(self):
        """Benchmark reputation calculation."""
        result = run_benchmark(
            lambda: _reputation_system.calculate_reputation("user_123"), iterations=100
        )
        assert result["avg_ms"] < 20, f"Reputation calc too slow: {result['avg_ms']}ms"

    def test_get_reputation_score(self):
        """Benchmark getting reputation score."""
        result = run_benchmark(
            lambda: _reputation_system.get_reputation_score("user_123"), iterations=100
        )
        assert result["avg_ms"] < 20, f"Get reputation too slow: {result['avg_ms']}ms"

    def test_update_reputation(self):
        """Benchmark updating reputation."""
        result = run_benchmark(
            lambda: _reputation_system.update_reputation("user_bench", "upvote"), iterations=100
        )
        assert result["avg_ms"] < 20, f"Update reputation too slow: {result['avg_ms']}ms"

    def test_reputation_tier_classification(self):
        """Benchmark reputation tier classification."""
        # Set up users with different reputation levels
        _reputation_system._reputation_store["user_gold"] = 150.0
        _reputation_system._reputation_store["user_silver"] = 75.0
        _reputation_system._reputation_store["user_bronze"] = 25.0
        _reputation_system._reputation_store["user_new"] = 5.0

        def classify_all():
            for uid in ["user_gold", "user_silver", "user_bronze", "user_new"]:
                _reputation_system.calculate_reputation(uid)

        result = run_benchmark(classify_all, iterations=50)
        assert result["avg_ms"] < 50, f"Tier classification too slow: {result['avg_ms']}ms"

    def test_reputation_breakdown(self):
        """Benchmark reputation breakdown generation."""
        result = run_benchmark(
            lambda: _reputation_system.calculate_reputation("user_breakdown"), iterations=100
        )
        assert result["avg_ms"] < 20, f"Reputation breakdown too slow: {result['avg_ms']}ms"


class TestEscalationWorkflow:
    """Benchmark escalation workflow performance."""

    @pytest.fixture(autouse=True)
    def check_available(self):
        if _escalation_workflow is None:
            pytest.skip("escalation_workflow not available")

    def test_create_escalation(self):
        """Benchmark creating an escalation."""
        counter = [0]

        def create():
            counter[0] += 1
            return _escalation_workflow.create_escalation(f"issue_{counter[0]}", "high")

        result = run_benchmark(create, iterations=50)
        assert result["avg_ms"] < 20, f"Create escalation too slow: {result['avg_ms']}ms"

    def test_get_escalation_status(self):
        """Benchmark getting escalation status."""
        esc = _escalation_workflow.create_escalation("issue_status", "medium")
        esc_id = esc["escalation_id"]

        result = run_benchmark(
            lambda: _escalation_workflow.get_escalation_status(esc_id), iterations=100
        )
        assert result["avg_ms"] < 20, f"Get escalation status too slow: {result['avg_ms']}ms"

    def test_resolve_escalation(self):
        """Benchmark resolving an escalation."""
        counter = [0]

        def resolve():
            counter[0] += 1
            esc = _escalation_workflow.create_escalation(f"issue_resolve_{counter[0]}", "low")
            return _escalation_workflow.resolve_escalation(esc["escalation_id"])

        result = run_benchmark(resolve, iterations=50)
        assert result["avg_ms"] < 30, f"Resolve escalation too slow: {result['avg_ms']}ms"

    def test_escalation_lifecycle(self):
        """Benchmark full escalation lifecycle."""
        counter = [0]

        def lifecycle():
            counter[0] += 1
            esc = _escalation_workflow.create_escalation(f"issue_lifecycle_{counter[0]}", "medium")
            _escalation_workflow.get_escalation_status(esc["escalation_id"])
            _escalation_workflow.resolve_escalation(esc["escalation_id"])

        result = run_benchmark(lifecycle, iterations=30)
        assert result["avg_ms"] < 50, f"Escalation lifecycle too slow: {result['avg_ms']}ms"


class TestModerationQueueAgents:
    """Benchmark moderation queue agent performance."""

    @pytest.fixture(autouse=True)
    def check_available(self):
        if not _auto_moderator_available:
            pytest.skip("AutoModeratorAgent not available (missing langchain_core)")

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    def test_auto_moderator_heuristic_approve(self):
        """Benchmark auto-moderator heuristic approval."""
        agent = AutoModeratorAgent()
        context = {
            "content": "This is a perfectly normal post about gardening.",
            "content_type": "text",
            "metadata": {},
        }
        result = run_async_benchmark(
            lambda: agent.process(context), iterations=100
        )
        assert result["avg_ms"] < 50, f"Auto-moderator approve too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    def test_auto_moderator_heuristic_reject(self):
        """Benchmark auto-moderator heuristic rejection."""
        agent = AutoModeratorAgent()
        context = {
            "content": "This contains hate speech and slurs.",
            "content_type": "text",
            "metadata": {},
        }
        result = run_async_benchmark(
            lambda: agent.process(context), iterations=100
        )
        assert result["avg_ms"] < 50, f"Auto-moderator reject too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    def test_auto_moderator_heuristic_escalate(self):
        """Benchmark auto-moderator heuristic escalation."""
        agent = AutoModeratorAgent()
        context = {
            "content": "This is a political opinion about protest.",
            "content_type": "text",
            "metadata": {},
        }
        result = run_async_benchmark(
            lambda: agent.process(context), iterations=100
        )
        assert result["avg_ms"] < 50, f"Auto-moderator escalate too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    def test_auto_moderator_empty_content(self):
        """Benchmark auto-moderator with empty content."""
        agent = AutoModeratorAgent()
        context = {
            "content": "",
            "content_type": "text",
            "metadata": {},
        }
        result = run_async_benchmark(
            lambda: agent.process(context), iterations=100
        )
        assert result["avg_ms"] < 20, f"Auto-moderator empty too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    def test_auto_moderator_long_content(self):
        """Benchmark auto-moderator with long content."""
        agent = AutoModeratorAgent()
        context = {
            "content": "Normal content. " * 1000,
            "content_type": "text",
            "metadata": {},
        }
        result = run_async_benchmark(
            lambda: agent.process(context), iterations=50
        )
        assert result["avg_ms"] < 100, f"Auto-moderator long content too slow: {result['avg_ms']}ms"


class TestAgentConcurrentExecution:
    """Benchmark concurrent agent execution."""

    @pytest.mark.skipif(not _trust_scorer_available, reason="TrustScorerAgent not available")
    @pytest.mark.asyncio
    async def test_concurrent_trust_scoring(self):
        """Benchmark concurrent trust score calculations."""
        agent = TrustScorerAgent()

        async def score_all():
            tasks = [
                agent.run(
                    {
                        "member_id": f"user_{i}",
                        "include_history": True,
                        "factors": None,
                    }
                )
                for i in range(20)
            ]
            await asyncio.gather(*tasks)

        result = run_async_benchmark(score_all, iterations=10)
        assert result["avg_ms"] < 500, f"Concurrent trust scoring too slow: {result['avg_ms']}ms"

    @pytest.fixture(autouse=True)
    def check_health_scorer_available(self):
        if _health_scorer is None:
            pytest.skip("community_health_scorer not available")

    @pytest.mark.asyncio
    async def test_concurrent_health_scoring(self):
        """Benchmark concurrent health score calculations."""
        community_ids = [f"comm_{i}" for i in range(20)]

        async def score_all():
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(None, _health_scorer.calculate_health_score, cid)
                for cid in community_ids
            ]
            await asyncio.gather(*tasks)

        result = run_async_benchmark(score_all, iterations=10)
        assert result["avg_ms"] < 500, f"Concurrent health scoring too slow: {result['avg_ms']}ms"

    @pytest.fixture(autouse=True)
    def check_reputation_available(self):
        if _reputation_system is None:
            pytest.skip("reputation_system not available")

    @pytest.mark.asyncio
    async def test_concurrent_reputation_updates(self):
        """Benchmark concurrent reputation updates."""
        async def update_all():
            tasks = [
                asyncio.to_thread(_reputation_system.update_reputation, f"user_{i}", "upvote")
                for i in range(50)
            ]
            await asyncio.gather(*tasks)

        result = run_async_benchmark(update_all, iterations=10)
        assert result["avg_ms"] < 500, f"Concurrent reputation updates too slow: {result['avg_ms']}ms"

    @pytest.mark.skipif(not _auto_moderator_available, reason="AutoModeratorAgent not available")
    @pytest.mark.asyncio
    async def test_concurrent_moderation(self):
        """Benchmark concurrent moderation processing."""
        agent = AutoModeratorAgent()
        contexts = [
            {"content": f"Content {i} for moderation", "content_type": "text", "metadata": {}}
            for i in range(30)
        ]

        async def moderate_all():
            tasks = [agent.process(ctx) for ctx in contexts]
            await asyncio.gather(*tasks)

        result = run_async_benchmark(moderate_all, iterations=10)
        assert result["avg_ms"] < 500, f"Concurrent moderation too slow: {result['avg_ms']}ms"

    @pytest.fixture(autouse=True)
    def check_escalation_available(self):
        if _escalation_workflow is None:
            pytest.skip("escalation_workflow not available")

    @pytest.mark.asyncio
    async def test_concurrent_escalation_creation(self):
        """Benchmark concurrent escalation creation."""
        async def create_all():
            tasks = [
                asyncio.to_thread(_escalation_workflow.create_escalation, f"issue_{i}", "high")
                for i in range(30)
            ]
            await asyncio.gather(*tasks)

        result = run_async_benchmark(create_all, iterations=10)
        assert result["avg_ms"] < 500, f"Concurrent escalation creation too slow: {result['avg_ms']}ms"
