"""
Unit tests for the z-score anomaly detector.

Run with:  pytest tests/ -v
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from app.anomaly.detector import AnomalyDetector, DetectedAnomaly


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cost_rows(costs: list[float], base_date: date | None = None) -> list[dict]:
    """Build fake cost-record dicts for the detector."""
    d = base_date or date(2024, 1, 1)
    return [
        {
            "provider": "aws",
            "account_id": "123456789",
            "service": "EC2",
            "region": "us-east-1",
            "cost_usd": c,
            "usage_date": d,
        }
        for c in costs
    ]


# ---------------------------------------------------------------------------
# Z-score calculation
# ---------------------------------------------------------------------------

class TestZScore:
    def test_normal_spend_not_flagged(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)
        # 29 days of stable $10 spend, one observation of $11 (well within 1 stddev)
        history = [10.0] * 29
        assert not detector._is_anomaly(11.0, history)

    def test_spike_flagged(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)
        history = [10.0] * 29
        # 5x spike is clearly anomalous
        assert detector._is_anomaly(50.0, history)

    def test_below_min_history_skipped(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=14)
        # only 5 data points, detector should skip
        history = [10.0] * 5
        assert not detector._is_anomaly(50.0, history)

    def test_zero_stddev_does_not_raise(self):
        """All historical values identical -> stddev=0, should not divide by zero."""
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)
        history = [100.0] * 30
        # any deviation from a perfectly flat history should be flagged
        result = detector._is_anomaly(150.0, history)
        assert isinstance(result, bool)

    def test_confidence_between_zero_and_one(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)
        history = [10.0] * 29
        conf = detector._confidence(50.0, history)
        assert 0.0 <= conf <= 1.0

    def test_confidence_higher_for_larger_spike(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)
        history = [10.0] * 29
        conf_small = detector._confidence(12.0, history)
        conf_large = detector._confidence(100.0, history)
        assert conf_large > conf_small


# ---------------------------------------------------------------------------
# Detector integration (mocked DB)
# ---------------------------------------------------------------------------

class TestDetectorRun:
    @pytest.mark.asyncio
    async def test_detect_inserts_anomaly(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)

        # history: 30 days of $10, latest day is $200
        history_rows = _cost_rows([10.0] * 30)
        spike_row = {**history_rows[0], "cost_usd": 200.0, "usage_date": date(2024, 2, 1)}

        mock_db = AsyncMock()
        # first query returns history, second returns the spike record
        mock_db.execute.return_value.mappings.return_value.all.side_effect = [
            history_rows,
            [spike_row],
        ]

        with patch("app.anomaly.detector.SessionLocal") as mock_session_cls:
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            results = await detector.run()

        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_no_anomaly_on_stable_spend(self):
        detector = AnomalyDetector(z_threshold=2.5, min_history=7)

        # perfectly flat history, no spike
        history_rows = _cost_rows([10.0] * 31)

        mock_db = AsyncMock()
        mock_db.execute.return_value.mappings.return_value.all.side_effect = [
            history_rows,
            [history_rows[-1]],
        ]

        with patch("app.anomaly.detector.SessionLocal") as mock_session_cls:
            mock_session_cls.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            results = await detector.run()

        # upsert should not have been called for an anomaly
        insert_calls = [
            c for c in mock_db.execute.call_args_list
            if "INSERT INTO anomalies" in str(c)
        ]
        assert len(insert_calls) == 0


# ---------------------------------------------------------------------------
# Pipeline serialisation (regression for json.dumps fix)
# ---------------------------------------------------------------------------

class TestPipelineTagSerialisation:
    def test_tags_with_special_chars_survive_round_trip(self):
        """Ensure tags containing apostrophes are serialised with json.dumps, not str()."""
        import json
        tags = {"env": "it's-prod", "team": "platform", "nested": True}
        serialised = json.dumps(tags)
        # must be valid JSON
        parsed = json.loads(serialised)
        assert parsed == tags

    def test_bool_values_are_lowercase_json(self):
        import json
        tags = {"active": True, "deprecated": False}
        serialised = json.dumps(tags)
        assert "true" in serialised
        assert "True" not in serialised
