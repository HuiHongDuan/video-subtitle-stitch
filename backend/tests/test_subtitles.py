from app.domain.subtitles import wrap_zh, segments_to_srt, Segment


def test_wrap_zh_limits_line_count_and_length():
    text = '这是一个很长的中文句子，用来验证字幕换行逻辑是否能够优先按标点断行，而不是无脑截断。'
    wrapped = wrap_zh(text, max_chars_per_line=12, max_lines=2)
    lines = wrapped.splitlines()
    assert len(lines) <= 2
    assert all(len(line) <= 12 for line in lines)


def test_segments_to_srt_outputs_valid_blocks():
    srt = segments_to_srt([Segment(0.0, 1.2, '你好世界')])
    assert '00:00:00,000 --> 00:00:01,200' in srt
    assert '你好世界' in srt
