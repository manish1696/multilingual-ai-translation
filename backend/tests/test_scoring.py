from ai.scoring import entity_preservation_score, quality_score_v2


def test_entity_preservation():
    source = "Pay ₹500 before 2026-08-18."
    assert entity_preservation_score(source, "Pay ₹500 before 2026-08-18.") == 1.0
    assert entity_preservation_score(source, "Pay before tomorrow.") == 0.0


def test_quality_score_v2():
    score = quality_score_v2(0.9, 80.0, 0.8, 1.0, 1.0)
    assert score == 0.88
