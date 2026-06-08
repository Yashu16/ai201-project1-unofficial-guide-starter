from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent
DOCUMENTS_PATH = PROJECT_ROOT / "documents"
ARTIFACTS_PATH = PROJECT_ROOT / "artifacts"
RAW_DOCUMENTS_PATH = ARTIFACTS_PATH / "raw_documents.jsonl"
CHUNKS_PATH = ARTIFACTS_PATH / "chunks.jsonl"

# --- Ingestion ---
REQUEST_TIMEOUT_SECONDS = 20
MAX_WEB_TEXT_CHARS = 120_000
MAX_REDDIT_THREADS_PER_SEARCH = 10

# --- Chunking (source-aware) ---
NARRATIVE_CHUNK_TOKENS = 360
NARRATIVE_OVERLAP_TOKENS = 50
SHORT_REVIEW_MAX_TOKENS = 65
MIN_CHUNK_TOKENS = 20

# --- Embedding & Retrieval ---
CHROMA_PATH = ARTIFACTS_PATH / "chroma_db"
CHROMA_COLLECTION = "umd_cs_chunks"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5
TOP_K_SHORT = 3
SHORT_CHUNK_TOKEN_THRESHOLD = 100  # chunks at or below this use TOP_K_SHORT
RETRIEVAL_SCORE_CUTOFF = 1.2       # Chroma uses L2 distance; lower = more similar

# You can edit this list as your source list changes.
# source_kind drives chunking behavior.
SOURCES = [
    {
        "id": "planetterp_cmsc_reviews",
        "name": "PlanetTerp CMSC Reviews",
        "url": "https://planetterp.com/api/v1/courses?department=CMSC&reviews=true&limit=100",
        "source_kind": "review",
    },
    {
        "id": "planetterp_cmsc_reviews_p2",
        "name": "PlanetTerp CMSC Reviews (page 2)",
        "url": "https://planetterp.com/api/v1/courses?department=CMSC&reviews=true&limit=100&offset=100",
        "source_kind": "review",
    },
    {
        "id": "umd_cs_current_students",
        "name": "UMD CS Current Students",
        "url": "https://undergrad.cs.umd.edu/current",
        "source_kind": "local",
    },
    {
        "id": "umd_cs_faq",
        "name": "UMD CS Undergraduate FAQ",
        "url": "https://undergrad.cs.umd.edu/faq",
        "source_kind": "local",
    },
    {
        "id": "ratemyprofessors_umd",
        "name": "RateMyProfessors UMD",
        "url": "https://www.ratemyprofessors.com/school/1270",
        "source_kind": "review",
    },
    {
        "id": "reddit_umd_cs_opportunities",
        "name": "r/UMD CS Opportunities",
        "url": "https://www.reddit.com/r/UMD/search/?q=CMSC+internship+research+opportunity&restrict_sr=1",
        "source_kind": "discussion",
    },
    {
        "id": "reddit_umd_professors",
        "name": "r/UMD Professors",
        "url": "https://www.reddit.com/r/UMD/search/?q=professor+review+class+CMSC&restrict_sr=1",
        "source_kind": "discussion",
    },
    {
        "id": "reddit_umd_cmsc",
        "name": "Reddit UMD CMSC",
        "url": "https://www.reddit.com/r/UMD/search/?q=CMSC+course+review&restrict_sr=1",
        "source_kind": "discussion",
    },
    {
        "id": "reddit_umd_exams",
        "name": "Reddit UMD Exams",
        "url": "https://www.reddit.com/r/UMD/search/?q=CMSC+exam+midterm+final&restrict_sr=1",
        "source_kind": "discussion",
    },
    {
        "id": "reddit_umd_cs_grades",
        "name": "r/UMD CS Grades",
        "url": "https://www.reddit.com/r/UMD/search/?q=CMSC+grade+GPA&restrict_sr=1",
        "source_kind": "discussion",
    },
    {
        "id": "reddit_umd_wiki",
        "name": "r/UMD Maryland Pro Tips",
        "url": "https://www.reddit.com/r/UMD/wiki/marylandprotips/",
        "source_kind": "discussion",
    },
]
