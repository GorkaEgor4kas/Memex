import tempfile
from pathlib import Path
from indexing.chunker import MarkdownChunker

def test_process_small_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write("""# Проект Альфа

## Сроки
Дедлайн перенесли на май.

## Бюджет
Выделили 100к.
""")
        temp_path = Path(f.name)

        chunker = MarkdownChunker()
        chunks = chunker.process(temp_path)

        assert len(chunks) == 2

        assert "[File:" in chunks[0].content
        assert "[Проект Альфа]" in chunks[0].content
        assert "[Сроки]" in chunks[0].content
        assert "Дедлайн перенесли на май" in chunks[0].content
        
        assert chunks[0].metadata["h1"] == "Проект Альфа"
        assert chunks[0].metadata["h2"] == "Сроки"

        temp_path.unlink()

