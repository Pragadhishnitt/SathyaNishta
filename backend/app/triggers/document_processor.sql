-- ==========================================
-- DOCUMENT PROCESSING TRIGGERS
-- ==========================================
-- These triggers automatically process documents
-- when they're added to storage buckets

-- ==========================================
-- FINANCIAL DOCUMENTS PROCESSING
-- ==========================================

-- Function to process financial documents
CREATE OR REPLACE FUNCTION process_financial_document()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the document processing
    INSERT INTO audit_trails (
        investigation_id,
        step_type,
        agent_type,
        input_payload,
        output_payload,
        model_metadata
    ) VALUES (
        gen_random_uuid(), -- Generate a UUID for this processing task
        'document_processing',
        'financial_processor',
        json_build_object(
            'file_key', NEW.source_file_key,
            'company', NEW.company_name,
            'doc_type', NEW.doc_type,
            'action', 'financial_document_processed'
        ),
        json_build_object(
            'status', 'processed',
            'revenue', NEW.revenue,
            'net_income', NEW.net_income,
            'processed_at', NOW()
        ),
        json_build_object(
            'processor', 'supabase_trigger',
            'timestamp', NOW()
        )
    );
    
    -- Update any pending investigations that might need this data
    UPDATE investigations 
    SET updated_at = NOW()
    WHERE status = 'queued' 
    AND context->>'company_ticker' = NEW.company_ticker;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically process new financial filings
CREATE TRIGGER trigger_process_financial_document
AFTER INSERT ON financial_filings
FOR EACH ROW
EXECUTE FUNCTION process_financial_document();

-- ==========================================
-- AUDIO DOCUMENTS PROCESSING
-- ==========================================

-- Function to process audio documents
CREATE OR REPLACE FUNCTION process_audio_document()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the audio document processing
    INSERT INTO audit_trails (
        investigation_id,
        step_type,
        agent_type,
        input_payload,
        output_payload,
        model_metadata
    ) VALUES (
        gen_random_uuid(),
        'document_processing',
        'audio_processor',
        json_build_object(
            'file_key', NEW.source_file_key,
            'company', NEW.company,
            'title', NEW.title,
            'action', 'audio_document_processed'
        ),
        json_build_object(
            'status', 'processed',
            'duration', NEW.duration_seconds,
            'transcription_length', length(NEW.content),
            'processed_at', NOW()
        ),
        json_build_object(
            'processor', 'supabase_trigger',
            'timestamp', NOW()
        )
    );
    
    -- Update any pending investigations
    UPDATE investigations 
    SET updated_at = NOW()
    WHERE status = 'queued' 
    AND context->>'company' = NEW.company;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically process new audio transcripts
CREATE TRIGGER trigger_process_audio_document
AFTER INSERT ON audio_transcripts
FOR EACH ROW
EXECUTE FUNCTION process_audio_document();

-- ==========================================
-- NEWS ARTICLES PROCESSING
-- ==========================================

-- Function to process news articles
CREATE OR REPLACE FUNCTION process_news_article()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the news article processing
    INSERT INTO audit_trails (
        investigation_id,
        step_type,
        agent_type,
        input_payload,
        output_payload,
        model_metadata
    ) VALUES (
        gen_random_uuid(),
        'document_processing',
        'news_processor',
        json_build_object(
            'source', NEW.source,
            'title', NEW.title,
            'url', NEW.url,
            'action', 'news_article_processed'
        ),
        json_build_object(
            'status', 'processed',
            'sentiment', NEW.sentiment_score,
            'relevance', NEW.relevance_score,
            'processed_at', NOW()
        ),
        json_build_object(
            'processor', 'supabase_trigger',
            'timestamp', NOW()
        )
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically process new news articles
CREATE TRIGGER trigger_process_news_article
AFTER INSERT ON news_articles
FOR EACH ROW
EXECUTE FUNCTION process_news_article();

-- ==========================================
-- COMPLIANCE RECORDS PROCESSING
-- ==========================================

-- Function to process compliance records
CREATE OR REPLACE FUNCTION process_compliance_record()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the compliance record processing
    INSERT INTO audit_trails (
        investigation_id,
        step_type,
        agent_type,
        input_payload,
        output_payload,
        model_metadata
    ) VALUES (
        gen_random_uuid(),
        'document_processing',
        'compliance_processor',
        json_build_object(
            'entity', NEW.entity,
            'violation_type', NEW.violation_type,
            'severity', NEW.severity,
            'action', 'compliance_record_processed'
        ),
        json_build_object(
            'status', 'processed',
            'fine_amount', NEW.fine_amount,
            'status', NEW.status,
            'processed_at', NOW()
        ),
        json_build_object(
            'processor', 'supabase_trigger',
            'timestamp', NOW()
        )
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically process new compliance records
CREATE TRIGGER trigger_process_compliance_record
AFTER INSERT ON compliance_records
FOR EACH ROW
EXECUTE FUNCTION process_compliance_record();

-- ==========================================
-- INVESTIGATION AUTO-START TRIGGER
-- ==========================================

-- Function to automatically start investigations when relevant data is available
CREATE OR REPLACE FUNCTION auto_start_investigation()
RETURNS TRIGGER AS $$
DECLARE
    company_name TEXT;
    pending_investigations INTEGER;
BEGIN
    -- Extract company name based on table
    IF TG_TABLE_NAME = 'financial_filings' THEN
        company_name := NEW.company_name;
    ELSIF TG_TABLE_NAME = 'news_articles' THEN
        company_name := NEW.title; -- Extract from title in production
    ELSIF TG_TABLE_NAME = 'compliance_records' THEN
        company_name := NEW.entity;
    ELSIF TG_TABLE_NAME = 'audio_transcripts' THEN
        company_name := NEW.company;
    END IF;
    
    -- Check if there are pending investigations for this company
    SELECT COUNT(*) INTO pending_investigations
    FROM investigations 
    WHERE status = 'queued' 
    AND (
        LOWER(query) LIKE LOWER('%' || company_name || '%') OR
        context->>'company' = company_name OR
        context->>'company_name' = company_name
    );
    
    -- If pending investigations exist, notify the investigation system
    IF pending_investigations > 0 THEN
        -- In production, this would trigger a background job
        -- For now, we just log it
        INSERT INTO audit_trails (
            investigation_id,
            step_type,
            agent_type,
            input_payload,
            output_payload,
            model_metadata
        ) VALUES (
            gen_random_uuid(),
            'auto_trigger',
            'investigation_starter',
            json_build_object(
                'company', company_name,
                'trigger_table', TG_TABLE_NAME,
                'pending_investigations', pending_investigations,
                'action', 'investigation_data_available'
            ),
            json_build_object(
                'status', 'triggered',
                'message', 'Data available for pending investigations',
                'triggered_at', NOW()
            ),
            json_build_object(
                'trigger_type', 'database_trigger',
                'timestamp', NOW()
            )
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create auto-start triggers for all data tables
CREATE TRIGGER trigger_auto_start_financial
AFTER INSERT ON financial_filings
FOR EACH ROW
EXECUTE FUNCTION auto_start_investigation();

CREATE TRIGGER trigger_auto_start_news
AFTER INSERT ON news_articles
FOR EACH ROW
EXECUTE FUNCTION auto_start_investigation();

CREATE TRIGGER trigger_auto_start_compliance
AFTER INSERT ON compliance_records
FOR EACH ROW
EXECUTE FUNCTION auto_start_investigation();

CREATE TRIGGER trigger_auto_start_audio
AFTER INSERT ON audio_transcripts
FOR EACH ROW
EXECUTE FUNCTION auto_start_investigation();
