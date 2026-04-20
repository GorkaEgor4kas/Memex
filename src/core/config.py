from pathlib import Path
import tomllib
from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    def __init__(self):
        self.defaults = self._load_pyproject()
        self.user = self._load_user_config()
        self.env = dict(os.environ)
        self.mode = self._mode()
        self.path = self.PathConfig(self.defaults, self.user, self.env)
        self.indexing = self.IndexingConfig(self.defaults, self.user, self.env)
        self.retrieval = self.RetrievalConfig(self.defaults, self.user, self.env)
        self.online = self.OnlineConfig(self.defaults, self.user, self.env)
        self.thresholds = self.ThresholdsConfig(self.defaults, self.user, self.env)

    def _load_pyproject(self) -> dict:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data["tool"]["obsidian-rag"]

    def _load_user_config(self) -> dict:
        user_path = Path.home() / ".obsidian-rag" / "config.toml"
        if user_path.exists():
            with open(user_path, "rb") as f:
                return tomllib.load(f)
        return {}

    def _mode(self) -> str:
        if val := self.env.get("OBSIDIAN_RAG_MODE"):
            return val
        if val := self.user.get("mode"):
            return val
        return self.defaults["mode"]

    class PathConfig:
        def __init__(self, defaults, user, env):
            self._defaults = defaults
            self._user = user
            self._env = env

        @property
        def vault_path(self) -> Path:
            """priorities: .env > user > default"""
            if val := self._env.get("OBSIDIAN_RAG_VAULT_PATH"):
                return Path(val).expanduser()
            if val := self._user.get("vault_path"):
                return Path(val ).expanduser()
            return Path(self._defaults["vault_path"]).expanduser()

        @property
        def chroma_db_path(self) -> Path:
            if val := self._env.get("OBSIDIAN_RAG_CHROMA_DB_PATH"):
                return Path(val).expanduser()
            if system := self._user.get("system"):
                if val := system.get("chroma_db_path"):
                    return Path(val).expanduser()
            return Path(self._defaults["system"]["chroma_db_path"]).expanduser()

        @property
        def bm25_index_path(self) -> Path:
            if val := self._env.get("OBSIDIAN_RAG_BM25_INDEX_PATH"):
                return Path(val).expanduser()
            if system := self._user.get("system"):
                if val := system.get("bm25_index_path"):
                    return Path(val).expanduser()
            return Path(self._defaults["system"]["bm25_index_path"]).expanduser()

    class IndexingConfig:
        def __init__(self, defaults, user, env):
            self._defaults = defaults
            self._user = user
            self._env = env

        @property
        def chunk_size(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_CHUNK_SIZE"):
                return int(val)
            if indexing := self._user.get("indexing"):
                if val := indexing.get("chunk_size"):
                    return int(val)
            return self._defaults["indexing"]["chunk_size"]

        @property
        def chunk_overlap(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_CHUNK_OVERLAP"):
                return int(val)
            if indexing := self._user.get("indexing"):
                if val := indexing.get("chunk_overlap"):
                    return int(val)
            return self._defaults["indexing"]["chunk_overlap"]

        @property
        def use_parental(self) -> bool:
            if val := self._env.get("OBSIDIAN_RAG_USE_PARENTAL"):
                return val.lower() in ("true", "1", "yes")
            if indexing := self._user.get("indexing"):
                if val := indexing.get("use_parental"):
                    return bool(val)
            return self._defaults["indexing"]["use_parental"]

    class RetrievalConfig:
        def __init__(self, defaults, user, env):
            self._defaults = defaults
            self._user = user
            self._env = env

        @property
        def semantic_limit(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_SEMANTIC_LIMIT"):
                return int(val)
            if retrieval := self._user.get("retrieval"):
                if val := retrieval.get("semantic_limit"):
                    return int(val)
            return self._defaults["retrieval"]["semantic_limit"]

        @property
        def bm25_limit(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_BM25_LIMIT"):
                return int(val)
            if retrieval := self._user.get("retrieval"):
                if val := retrieval.get("bm25_limit"):
                    return int(val)
            return self._defaults["retrieval"]["bm25_limit"]

        @property
        def rrf_k(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_RRF_K"):
                return int(val)
            if retrieval := self._user.get("retrieval"):
                if val := retrieval.get("rrf_k"):
                    return int(val)
            return self._defaults["retrieval"]["rrf_k"]

        @property
        def final_limit(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_FINAL_LIMIT"):
                return int(val)
            if retrieval := self._user.get("retrieval"):
                if val := retrieval.get("final_limit"):
                    return int(val)
            return self._defaults["retrieval"]["final_limit"]

    class OnlineConfig:
        def __init__(self, defaults, user, env):
            self._defaults = defaults
            self._user = user
            self._env = env

        @property
        def provider(self) -> str:
            if val := self._env.get("OBSIDIAN_RAG_PROVIDER"):
                return val
            if online := self._user.get("online"):
                if val := online.get("provider"):
                    return val
            return self._defaults["online"]["provider"]

        @property
        def model(self) -> str:
            if val := self._env.get("OBSIDIAN_RAG_MODEL"):
                return val
            if online := self._user.get("online"):
                if val := online.get("model"):
                    return val
            return self._defaults["online"]["model"]

        @property
        def temperature(self) -> float:
            if val := self._env.get("OBSIDIAN_RAG_TEMPERATURE"):
                return float(val)
            if online := self._user.get("online"):
                if val := online.get("temperature"):
                    return float(val)
            return self._defaults["online"]["temperature"]

        @property
        def max_tokens(self) -> int:
            if val := self._env.get("OBSIDIAN_RAG_MAX_TOKENS"):
                return int(val)
            if online := self._user.get("online"):
                if val := online.get("max_tokens"):
                    return int(val)
            return self._defaults["online"]["max_tokens"]

        @property
        def prompt_template(self) -> str:
            if val := self._env.get("OBSIDIAN_RAG_PROMPT_TEMPLATE"):
                return val
            if online := self._user.get("online"):
                if val := online.get("prompt_template"):
                    return val
            return self._defaults["online"]["prompt_template"]

    class ThresholdsConfig:
        def __init__(self, defaults, user, env):
            self._defaults = defaults
            self._user = user
            self._env = env

        @property
        def bm25_min_score(self) -> float:
            if val := self._env.get("OBSIDIAN_RAG_BM25_MIN_SCORE"):
                return float(val)
            if thresholds := self._user.get("thresholds"):
                if val := thresholds.get("bm25_min_score"):
                    return float(val)
            return float(self._defaults["thresholds"]["bm25_min_score"])

        @property
        def vector_min_similarity(self) -> float:
            if val := self._env.get("OBSIDIAN_RAG_VECTOR_MIN_SIMILARITY"):
                return float(val)
            if thresholds := self._user.get("thresholds"):
                if val := thresholds.get("vector_min_similarity"):
                    return float(val)
            return float(self._defaults["thresholds"]["vector_min_similarity"])


# global variable for import 
config = Config()