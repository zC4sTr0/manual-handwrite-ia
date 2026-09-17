from manual_handwrite.coverage.optimizer import optimize_coverage


def test_greedy_selection_prefers_new_coverage_per_character():
    result = optimize_coverage(
        [
            "print(1)",
            "for i in range(3):\n    print(i)",
            "if x != 0:\n    return x",
        ],
        max_snippets=2,
    )

    assert result.selected_snippets == (
        "print(1)",
        "if x != 0:\n    return x",
    )
    assert "for" in result.missing_tokens
    assert "!=" not in result.missing_operators
    assert "return" not in result.missing_tokens


def test_coverage_is_taken_only_from_analyzer_output():
    result = optimize_coverage(["if x = 5:"], max_snippets=1)

    assert result.selected_snippets == ("if x = 5:",)
    assert "if" not in result.missing_tokens
    assert "x" not in result.missing_tokens
    assert "5" not in result.missing_tokens
    assert "==" in result.missing_operators
    assert "=" not in result.missing_operators


def test_existing_text_and_cost_bound_leave_a_reportable_remainder():
    result = optimize_coverage(
        ["def f():\n    return None", "while x >= 1:\n    x -= 1"],
        existing_text="print('already')",
        max_snippets=1,
        max_cost=24,
    )

    assert result.selected_snippets == ("def f():\n    return None",)
    assert "def" not in result.missing_tokens
    assert "return" not in result.missing_tokens
    assert "while" in result.missing_tokens
    assert ">=" in result.missing_operators


def test_duplicate_and_zero_gain_candidates_are_not_selected():
    result = optimize_coverage(
        ["print(1)", "print(1)", "x = 1"],
        max_snippets=3,
    )

    assert result.selected_snippets == ("print(1)", "x = 1")
    assert result.selected_count == 2
