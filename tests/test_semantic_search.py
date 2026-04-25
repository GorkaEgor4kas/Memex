# tests/test_vector_store.py
import pytest
import tempfile
import shutil
from pathlib import Path
from indexing.chunker import Chunk
from indexing.vector_store import ChromaStore


def create_test_chunks():
    """Создаёт тестовые чанки."""
    return [
        Chunk(
            content="Дедлайн проекта Альфа перенесли на май",
            source_file="Projects/Alpha.md",
            metadata={"h1": "Проект Альфа", "h2": "Сроки"},
            parent_text="## Сроки\nДедлайн перенесли на май."
        ),
        Chunk(
            content="Бюджет проекта Альфа составляет 100к рублей",
            source_file="Projects/Alpha.md",
            metadata={"h1": "Проект Альфа", "h2": "Бюджет"},
            parent_text="## Бюджет\n100к рублей."
        ),
        Chunk(
            content="Иван отвечает за разработку нового API",
            source_file="Team/Ivan.md",
            metadata={"h1": "Иван", "h2": "Обязанности"},
            parent_text="## Обязанности\nИван разрабатывает API."
        ),
    ]


def create_fake_embeddings(n: int, dim: int = 10) -> list:
    """Создаёт фейковые эмбеддинги заданной размерности."""
    return [[0.1 * (i + j) for j in range(dim)] for i in range(n)]


class TestChromaStore:

    @pytest.fixture
    def temp_store(self):
        """Создаёт временное хранилище ChromaDB."""
        temp_dir = Path(tempfile.mkdtemp())
        temp_path = temp_dir / "test_chroma"
        store = ChromaStore(vault_path=temp_path)
        yield store
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_add_and_count(self, temp_store):
        """Добавление чанков и подсчёт количества."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))

        temp_store.add(chunks, embeddings)
        assert temp_store.count() == 3

    def test_search_returns_results(self, temp_store):
        """Поиск возвращает результаты с правильной структурой."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        # Используем первый эмбеддинг как запрос
        results = temp_store.search(embeddings[0], k=2)

        assert len(results) == 2
        assert "id" in results[0]
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert "distance" in results[0]

    def test_search_returns_less_than_k(self, temp_store):
        """Если чанков меньше k, возвращает сколько есть."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        results = temp_store.search(embeddings[0], k=10)
        assert len(results) == 3  # всего 3 чанка

    def test_delete_by_file(self, temp_store):
        """Удаление всех чанков файла."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        assert temp_store.count() == 3

        # Удаляем все чанки из Projects/Alpha.md
        temp_store.delete_by_file("Projects/Alpha.md")

        # Должен остаться только Иван
        assert temp_store.count() == 1

        # Проверяем, что остался правильный чанк
        results = temp_store.search(embeddings[2], k=5)
        assert results[0]["metadata"]["h1"] == "Иван"

    def test_get_by_ids(self, temp_store):
        """Получение чанков по id."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        ids = [chunks[0].id, chunks[2].id]
        results = temp_store.get_by_ids(ids)

        assert len(results) == 2
        retrieved_ids = [r["id"] for r in results]
        assert chunks[0].id in retrieved_ids
        assert chunks[2].id in retrieved_ids

    def test_get_by_ids_empty_list(self, temp_store):
        """Пустой список id возвращает пустой результат."""
        results = temp_store.get_by_ids([])
        assert results == []

    def test_clean(self, temp_store):
        """Очистка коллекции."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        assert temp_store.count() == 3

        temp_store.clean()
        assert temp_store.count() == 0

    def test_add_does_not_duplicate(self, temp_store):
        """Повторное добавление тех же id не дублирует."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))

        temp_store.add(chunks, embeddings)
        assert temp_store.count() == 3

        # Повторное добавление с теми же id
        temp_store.add(chunks, embeddings)
        assert temp_store.count() == 3  # не изменилось

    def test_metadata_fields(self, temp_store):
        """Проверка сохранения метаданных."""
        chunks = create_test_chunks()
        embeddings = create_fake_embeddings(len(chunks))
        temp_store.add(chunks, embeddings)

        results = temp_store.search(embeddings[0], k=3)
        first = results[0]

        assert "source_file" in first["metadata"]
        assert "h1" in first["metadata"]
        assert "h2" in first["metadata"]
        assert "parent_id" in first["metadata"]
        assert "parent_text" in first["metadata"]