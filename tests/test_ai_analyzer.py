from app.ai_analyzer import analyze_with_ai


def test_fallback_keeps_candidates_when_no_key(monkeypatch):
    monkeypatch.setattr("app.ai_analyzer.settings.openai_api_key", "")
    candidates = [
        {
            "code": "600519",
            "name": "贵州茅台",
            "strategy": "测试策略",
            "score": 80,
            "buy_timing": "回踩买入",
            "stop_loss": "跌破止损",
            "take_profit": "分批止盈",
            "holding_period": "5-20日",
            "position": "10%",
            "risk_notes": ["测试风险"],
        }
    ]
    result = analyze_with_ai(candidates, [], {"regime": "strong"}, top_n=1)
    assert result[0]["code"] == "600519"
    assert "ai_score" in result[0]


def test_empty_candidates_returns_empty():
    assert analyze_with_ai([], [], {"regime": "strong"}) == []
