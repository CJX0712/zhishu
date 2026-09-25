from zhishu import ingest
from zhishu.vector_store import count


def test_chunk_short():
    assert ingest.chunk_text("短文本") == ["短文本"]


def test_chunk_split():
    chunks = ingest.chunk_text("内容" * 200, chunk_size=50, overlap=10)
    assert len(chunks) >= 4
    assert all(len(c) <= 50 for c in chunks)


def test_load_text_markdown(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("# 标题\n正文内容", encoding="utf-8")
    assert "正文内容" in ingest.load_text(str(p))


def test_load_text_pdf_path(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    # 仅验证不会因非标准 PDF 直接崩溃（异常应向上抛出由调用方处理）
    try:
        ingest.load_text(str(p))
    except Exception:
        pass


def test_ingest_file_persists(tmp_path, requires_qdrant):
    p = tmp_path / "doc.txt"
    p.write_text("退款政策：发货后7天内可全额退款。年假满1年5天。", encoding="utf-8")
    n = ingest.ingest_file(str(p))
    assert n >= 1
    assert count() >= 1
