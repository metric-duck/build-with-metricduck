-- Lab 10: Enterprise Screener Database Schema
-- For PostgreSQL (works with Supabase, Neon, or any Postgres)

-- ============================================
-- CORE TABLES
-- ============================================

-- Company master data (synced from MetricDuck)
CREATE TABLE IF NOT EXISTS companies (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sic VARCHAR(10),  -- SEC SIC industry code
    cik VARCHAR(20),  -- SEC CIK identifier
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Metric values (single latest value per metric)
CREATE TABLE IF NOT EXISTS metrics_latest (
    ticker VARCHAR(10) REFERENCES companies(ticker) ON DELETE CASCADE,
    metric_id VARCHAR(50) NOT NULL,
    value DECIMAL(20, 6),  -- Latest value (TTM for flows, snapshot for balance sheet)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (ticker, metric_id)
);

-- User-defined screener configurations
CREATE TABLE IF NOT EXISTS screeners (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    filters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sync history (for delta sync tracking)
CREATE TABLE IF NOT EXISTS sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_id VARCHAR(50),
    credits_used INTEGER,
    companies_count INTEGER,
    metrics_count INTEGER,
    is_delta BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Fast metric filtering
CREATE INDEX IF NOT EXISTS idx_metrics_latest_metric_value
ON metrics_latest(metric_id, value);

-- Company lookup by SIC
CREATE INDEX IF NOT EXISTS idx_companies_sic
ON companies(sic);

-- User screeners
CREATE INDEX IF NOT EXISTS idx_screeners_user
ON screeners(user_id);

-- Delta sync timestamp lookup
CREATE INDEX IF NOT EXISTS idx_sync_log_synced_at
ON sync_log(synced_at DESC) WHERE status = 'success';

-- ============================================
-- SCREENER FUNCTION
-- ============================================

CREATE OR REPLACE FUNCTION run_screener(filters JSONB)
RETURNS TABLE(
    ticker VARCHAR,
    company_name VARCHAR,
    sic VARCHAR,
    matched_metrics JSONB
)
LANGUAGE plpgsql AS $$
DECLARE
    metric_key TEXT;
    metric_filter JSONB;
    sql_query TEXT;
BEGIN
    sql_query := '
        SELECT DISTINCT
            c.ticker,
            c.company_name,
            c.sic,
            (
                SELECT jsonb_object_agg(m.metric_id, m.value)
                FROM metrics_latest m
                WHERE m.ticker = c.ticker
            ) as matched_metrics
        FROM companies c
        WHERE 1=1
    ';

    FOR metric_key, metric_filter IN SELECT * FROM jsonb_each(filters)
    LOOP
        IF metric_filter ? 'lt' THEN
            sql_query := sql_query || format('
                AND EXISTS (
                    SELECT 1 FROM metrics_latest m
                    WHERE m.ticker = c.ticker
                    AND m.metric_id = %L
                    AND m.value < %s
                )', metric_key, (metric_filter->>'lt')::DECIMAL);
        END IF;

        IF metric_filter ? 'gt' THEN
            sql_query := sql_query || format('
                AND EXISTS (
                    SELECT 1 FROM metrics_latest m
                    WHERE m.ticker = c.ticker
                    AND m.metric_id = %L
                    AND m.value > %s
                )', metric_key, (metric_filter->>'gt')::DECIMAL);
        END IF;

        IF metric_filter ? 'eq' THEN
            sql_query := sql_query || format('
                AND EXISTS (
                    SELECT 1 FROM metrics_latest m
                    WHERE m.ticker = c.ticker
                    AND m.metric_id = %L
                    AND m.value = %s
                )', metric_key, (metric_filter->>'eq')::DECIMAL);
        END IF;

        IF metric_filter ? 'between' THEN
            sql_query := sql_query || format('
                AND EXISTS (
                    SELECT 1 FROM metrics_latest m
                    WHERE m.ticker = c.ticker
                    AND m.metric_id = %L
                    AND m.value BETWEEN %s AND %s
                )', metric_key,
                (metric_filter->'between'->>0)::DECIMAL,
                (metric_filter->'between'->>1)::DECIMAL);
        END IF;
    END LOOP;

    sql_query := sql_query || ' ORDER BY c.ticker';

    RETURN QUERY EXECUTE sql_query;
END;
$$;

COMMENT ON TABLE companies IS 'Company master data synced from MetricDuck';
COMMENT ON TABLE metrics_latest IS 'Latest metric values (single value per metric)';
COMMENT ON TABLE screeners IS 'User-defined stock screener configurations';
COMMENT ON FUNCTION run_screener IS 'Execute a screener with JSONB filter conditions';
