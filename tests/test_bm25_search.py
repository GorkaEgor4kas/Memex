import pytest
import tempfile
import shutil
from pathlib import Path
from memex.indexing.chunker import Chunk
from memex.indexing.bm25_store import BM25Store


def create_test_chunks():
    return [
        Chunk(
            content="Дедлайн проекта Альфа перенесли на май",
            source_file="Projects/Alpha.md",
            metadata={"h1": "Проект Альфа", "h2": "Сроки"},
        ),
        Chunk(
            content="Бюджет проекта Альфа составляет 100к рублей",
            source_file="Projects/Alpha.md",
            metadata={"h1": "Проект Альфа", "h2": "Бюджет"},
        ),
        Chunk(
            content="Иван отвечает за разработку нового API",
            source_file="Team/Ivan.md",
            metadata={"h1": "Иван", "h2": "Обязанности"},
        ),
    ]


class TestBM25Store:

    @pytest.fixture
    def temp_store(self):
        """Создаёт временное хранилище BM25."""
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / "test_bm25"
        store = BM25Store(vault_path=temp_path)
        yield store
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_and_search(self, temp_store):
        """Базовая индексация и поиск."""
        chunks = create_test_chunks()
        temp_store.build_index(chunks)

        results = temp_store.search("дедлайн", k=3)
        assert len(results) > 0
        assert chunks[0].id in [r[0] for r in results]

    def test_search_before_build(self, temp_store):
        """Поиск до индексации возвращает пустой список."""
        results = temp_store.search("что-то", k=3)
        assert results == []

    def test_search_returns_scores_descending(self, temp_store):
        """Результаты отсортированы по убыванию score."""
        chunks = create_test_chunks()
        temp_store.build_index(chunks)

        results = temp_store.search("проект Альфа", k=3)
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_save_and_load(self, temp_store):
        """Сохранение и загрузка индекса."""
        chunks = create_test_chunks()
        temp_store.build_index(chunks)
        temp_store.save()

        # Загружаем в новый store
        store2 = BM25Store(vault_path=temp_store.vault_path)
        store2.load()

        results = store2.search("дедлайн", k=3)
        assert len(results) > 0
        assert len(store2.chunk_ids) == len(chunks)

    def test_no_duplicates(self, temp_store):
        """Нет дубликатов в выдаче."""
        chunks = create_test_chunks()
        temp_store.build_index(chunks)

        results = temp_store.search("проект", k=3)
        ids = [r[0] for r in results]
        assert len(ids) == len(set(ids))