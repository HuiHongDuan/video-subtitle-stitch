from app.domain.eval import evaluate_srt, parse_srt, text_similarity


def test_parse_srt_reads_blocks():
    text = '1\n00:00:00,000 --> 00:00:01,000\n你好\n\n'
    items = parse_srt(text)
    assert len(items) == 1
    assert items[0].text == '你好'


def test_text_similarity_is_high_for_near_match():
    assert text_similarity('你好，世界', '你好世界') > 0.9


def test_evaluate_srt_returns_metrics():
    pred = '1\n00:00:00,000 --> 00:00:01,000\n你好世界\n\n'
    gold = '1\n00:00:00,100 --> 00:00:01,000\n你好世界\n\n'
    metrics = evaluate_srt(pred, gold)
    assert metrics['coverage'] == 1.0
    assert metrics['avg_similarity'] > 0.9
