import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { record, bucket } = await req.json()
    
    console.log(`Processing file: ${record.name} from bucket: ${bucket}`)
    
    // Initialize Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    // Process based on bucket type
    if (bucket === 'financial_docs') {
      await processFinancialDocument(supabase, record)
    } else if (bucket === 'audio_recordings') {
      await processAudioDocument(supabase, record)
    } else if (bucket === 'temp_uploads') {
      await processTempUpload(supabase, record)
    }

    return new Response(
      JSON.stringify({ message: 'Document processed successfully' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    console.error('Processing error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    )
  }
})

async function processFinancialDocument(supabase: any, record: any) {
  const { name, id } = record
  
  // Extract company info from path
  const pathParts = name.split('/')
  const [ticker, fiscalYear, period, docType] = pathParts
  
  console.log(`Processing financial document: ${ticker} ${fiscalYear} ${period} ${docType}`)
  
  // Download file content
  const { data: fileData, error: downloadError } = await supabase.storage
    .from('financial_docs')
    .download(name)
  
  if (downloadError) throw downloadError
  
  // Extract text from PDF (simplified - in production use PDF parser)
  const content = await extractPDFText(fileData)
  
  // Parse financial data (simplified - in production use financial parser)
  const financialData = parseFinancialData(content, ticker, fiscalYear, period, docType)
  
  // Store in database
  const { error: insertError } = await supabase
    .from('financial_filings')
    .insert({
      symbol: ticker,
      company_name: getCompanyName(ticker),
      company_ticker: ticker,
      filing_type: docType.toUpperCase(),
      period: `${fiscalYear}_${period}`,
      doc_type: docType.toLowerCase(),
      revenue: financialData.revenue,
      net_income: financialData.netIncome,
      total_assets: financialData.totalAssets,
      total_liabilities: financialData.totalLiabilities,
      content_chunk: content.substring(0, 1000), // First 1000 chars
      metadata: JSON.stringify(financialData),
      filing_date: new Date().toISOString(),
      source_file_key: name
    })
  
  if (insertError) throw insertError
  
  console.log(`✅ Financial document processed: ${name}`)
}

async function processAudioDocument(supabase: any, record: any) {
  const { name, id } = record
  
  // Extract info from path
  const pathParts = name.split('/')
  const [ticker, fiscalYear, period, callInfo] = pathParts
  const [callType, date] = callInfo.split('_')
  
  console.log(`Processing audio document: ${ticker} ${callType} ${date}`)
  
  // In production: transcribe audio using speech-to-text
  const transcription = await transcribeAudio(record)
  
  // Store in database
  const { error: insertError } = await supabase
    .from('audio_transcripts')
    .insert({
      title: `${ticker} ${callType} Call - ${date}`,
      content: transcription,
      speaker: 'Unknown', // Would be detected in production
      company: getCompanyName(ticker),
      date: new Date(date).toISOString(),
      duration_seconds: 1800, // Would be extracted from audio
      sentiment_score: 0.5, // Would be analyzed
      source_file_key: name
    })
  
  if (insertError) throw insertError
  
  console.log(`✅ Audio document processed: ${name}`)
}

async function processTempUpload(supabase: any, record: any) {
  const { name, id } = record
  
  console.log(`Processing temp upload: ${name}`)
  
  // Move to appropriate bucket based on file type
  const fileExtension = name.split('.').pop()?.toLowerCase()
  
  let targetBucket = 'financial_docs'
  let targetPath = name
  
  if (['mp3', 'wav', 'm4a'].includes(fileExtension)) {
    targetBucket = 'audio_recordings'
  } else if (fileExtension === 'pdf') {
    targetBucket = 'financial_docs'
  }
  
  // Copy file to target bucket
  const { error: copyError } = await supabase.storage
    .from(targetBucket)
    .copy(name, targetPath)
  
  if (copyError) throw copyError
  
  // Delete from temp
  await supabase.storage
    .from('temp_uploads')
    .remove([name])
  
  console.log(`✅ Temp file moved to ${targetBucket}: ${name}`)
}

// Helper functions (simplified implementations)
async function extractPDFText(buffer: ArrayBuffer): Promise<string> {
  // In production: use pdf-parse or similar library
  return "Sample PDF content extracted from financial document"
}

function parseFinancialData(content: string, ticker: string, fiscalYear: string, period: string) {
  // In production: use financial data parsing library
  return {
    revenue: 1000000000,
    netIncome: 100000000,
    totalAssets: 2000000000,
    totalLiabilities: 500000000
  }
}

async function transcribeAudio(record: any): Promise<string> {
  // In production: use speech-to-text service
  return "Sample audio transcription content"
}

function getCompanyName(ticker: string): string {
  const companies: Record<string, string> = {
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'TSLA': 'Tesla, Inc.'
  }
  return companies[ticker] || `${ticker} Corporation`
}
