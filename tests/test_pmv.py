import pytest

from pygreenbuild.transform.pmv import pmv_ashrae, pmv_iso


def test_pmv_iso_scalar_matches_reference():
    result = pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5)

    assert isinstance(result, dict)
    assert result == {
        "pmv": 0.08,
        "ppd": 5.1,
        "tsv": "Neutral",
        "standard": "ISO 7730:2025",
    }


def test_pmv_iso_vectorized_input_returns_list_of_dicts():
    result = pmv_iso(
        [22.0, 25.0],
        [22.0, 25.0],
        0.1,
        50.0,
        1.2,
        0.5,
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(item["standard"] == "ISO 7730:2025" for item in result)
    assert result[0]["pmv"] < result[1]["pmv"]


def test_pmv_ashrae_with_elevated_air_speed_matches_reference():
    result = pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5)

    assert result["standard"] == "ASHRAE 55-2023"
    assert result["pmv"] == -0.69
    assert result["ppd"] == 15.1
    assert result["tsv"] == "Slightly Cool"
    assert result["cooling_effect"] == 2.62
    assert result["compliance"] is False


def test_pmv_ashrae_still_air_has_zero_cooling_effect():
    result = pmv_ashrae(25.0, 25.0, 0.1, 50.0, 1.2, 0.5)

    assert result["cooling_effect"] == 0.0
    assert result["pmv"] == pytest.approx(0.08)


def test_pmv_ashrae_moderate_airspeed_compliance():
    result = pmv_ashrae(25.0, 25.0, 0.3, 50.0, 1.2, 0.5)

    assert result["cooling_effect"] == 1.68
    assert result["pmv"] == -0.41
    assert result["compliance"] is True


def test_pmv_iso_rejects_invalid_humidity():
    with pytest.raises(ValueError, match="rh"):
        pmv_iso(25.0, 25.0, 0.1, 120.0, 1.2, 0.5)


def test_pmv_iso_rejects_mismatched_vector_lengths():
    with pytest.raises(ValueError, match="長度"):
        pmv_iso([25.0, 26.0], [25.0, 26.0, 27.0], 0.1, 50.0, 1.2, 0.5)


def test_round_output_false_returns_unrounded_pmv():
    result = pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, round_output=False)

    assert result["pmv"] == pytest.approx(0.084137, abs=1e-6)
    assert isinstance(result["ppd"], float)


def test_pmv_iso_output_pmv_returns_scalar_value():
    assert pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="pmv") == 0.08
    assert pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="ppd") == 5.1
    assert pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="tsv") == "Neutral"


def test_pmv_iso_output_pmv_vectorized_returns_list():
    result = pmv_iso(
        [22.0, 25.0],
        [22.0, 25.0],
        0.1,
        50.0,
        1.2,
        0.5,
        output="pmv",
    )

    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(value, float) for value in result)
    assert result[0] < result[1]


def test_pmv_ashrae_output_cooling_effect():
    assert pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5, output="cooling_effect") == 2.62
    assert pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5, output="compliance") is False


def test_pmv_iso_rejects_invalid_output():
    with pytest.raises(ValueError, match="output"):
        pmv_iso(25.0, 25.0, 0.1, 50.0, 1.2, 0.5, output="set")


def test_pmv_ashrae_output_all_includes_cooling_effect():
    result = pmv_ashrae(25.0, 25.0, 0.5, 50.0, 1.2, 0.5, output="all")

    assert isinstance(result, dict)
    assert "cooling_effect" in result
    assert "compliance" in result
