from app.utils import extract_json_array, normalize_code, safe_float


def test_safe_float_handles_market_placeholders():
    assert safe_float("-") is None
    assert safe_float("1,234.5") == 1234.5
    assert safe_float("12.3%") == 12.3
    assert safe_float(None, 0) == 0


def test_normalize_code():
    assert normalize_code("sh600519") == "600519"
    assert normalize_code("1") == "000001"


def test_extract_json_array_from_markdown():
    text = "```json\n[{\"code\": \"600519\"}]\n```"
    assert extract_json_array(text)[0]["code"] == "600519"
