-- ===================== EXTENSIONS ==========================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ===================== VIDEO CACHING =====================
CREATE TABLE "Video" (
  "videoID" serial PRIMARY KEY,
  "url" VARCHAR(500) UNIQUE NOT NULL,
  "title" VARCHAR(200),
  "transcription" TEXT,
  "claims" JSONB NOT NULL DEFAULT '[]',  -- [] or ["claim1", "claim2", "claim3"]
  "processed_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast URL lookups (main caching use case)
CREATE UNIQUE INDEX idx_video_url ON "Video" ("url");

-- Index for filtering diabetes vs non-diabetes videos  
CREATE INDEX idx_video_has_claims ON "Video" 
USING GIN ((jsonb_array_length("claims")));