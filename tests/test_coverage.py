from manual_handwrite.coverage import analyze_text


def test_analyze_text_preserves_character_and_python_operator_evidence():
    report = analyze_text("def f(x):\n    return x >= 2\n")
    assert report.characters["x"] == 2
    assert report.tokens["def"] == 1
    assert report.tokens["2"] == 1
    assert report.operators[">="] == 1
    assert ">=" not in report.missing_operators


def test_invalid_python_does_not_fabricate_token_coverage():
    report = analyze_text("if x = 5:")
    assert report.characters["="] == 1
    assert report.tokens["if"] == 1
    assert report.tokens["x"] == 1
    assert report.tokens["5"] == 1
