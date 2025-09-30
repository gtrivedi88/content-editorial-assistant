

📥 INCOMING REQUEST: GET /static/js/error-styling.js


📥 INCOMING REQUEST: GET /static/js/error-cards.js


📥 INCOMING REQUEST: GET /static/js/error-highlighting.js


📥 INCOMING REQUEST: GET /static/js/feedback-system.js


📥 INCOMING REQUEST: GET /static/js/error-display-core.js


📥 INCOMING REQUEST: GET /static/js/statistics-display.js


📥 INCOMING REQUEST: GET /static/js/socket-handler.js


📥 INCOMING REQUEST: GET /static/js/file-handler.js


📥 INCOMING REQUEST: GET /static/js/smart-filter-system.js


📥 INCOMING REQUEST: GET /static/js/smart-filter-chips.js


📥 INCOMING REQUEST: GET /static/js/display-main.js


📥 INCOMING REQUEST: GET /static/js/modular-compliance-display.js


📥 INCOMING REQUEST: GET /static/js/modular-compliance-scoring.js


📥 INCOMING REQUEST: GET /static/js/metadata-display.js


📥 INCOMING REQUEST: GET /static/js/metadata-editor.js


📥 INCOMING REQUEST: GET /static/js/metadata-export.js


📥 INCOMING REQUEST: GET /static/js/metadata-feedback.js


📥 INCOMING REQUEST: GET /static/js/block-assembly.js


📥 INCOMING REQUEST: GET /static/js/core.js


📥 INCOMING REQUEST: GET /static/js/navigation.js


📥 INCOMING REQUEST: GET /static/js/elements-minimal.js


📥 INCOMING REQUEST: GET /static/js/index-page.js


📥 INCOMING REQUEST: GET /api/feedback/session


📥 INCOMING REQUEST: GET /api/feedback/session

INFO:app_modules.websocket_handlers:Client connected with session ID: c6fca038-8166-44be-ae12-c9b958c0f81f

📥 INCOMING REQUEST: GET /favicon.ico


📥 INCOMING REQUEST: GET /analyze


📥 INCOMING REQUEST: GET /static/css/patternfly.css


📥 INCOMING REQUEST: GET /static/css/patternfly-addons.css


📥 INCOMING REQUEST: GET /static/css/writing-analytics.css


📥 INCOMING REQUEST: GET /static/css/home.css

📥 INCOMING REQUEST: GET /static/css/metadata-assistant.css

📥 INCOMING REQUEST: GET /static/css/base-html.css



INFO:app_modules.websocket_handlers:Client disconnected

📥 INCOMING REQUEST: GET /static/js/engagement-analyzer.js


📥 INCOMING REQUEST: GET /static/js/error-styling.js


📥 INCOMING REQUEST: GET /static/js/style-helpers.js


📥 INCOMING REQUEST: GET /static/js/confidence-system.js

📥 INCOMING REQUEST: GET /static/js/error-cards.js

📥 INCOMING REQUEST: GET /static/js/utility-functions.js




📥 INCOMING REQUEST: GET /static/js/error-highlighting.js

📥 INCOMING REQUEST: GET /static/js/feedback-system.js

📥 INCOMING REQUEST: GET /static/css/index-page.css




📥 INCOMING REQUEST: GET /static/js/error-display-core.js

📥 INCOMING REQUEST: GET /static/js/statistics-display.js

📥 INCOMING REQUEST: GET /static/js/socket-handler.js




📥 INCOMING REQUEST: GET /static/js/file-handler.js

📥 INCOMING REQUEST: GET /static/js/smart-filter-chips.js

📥 INCOMING REQUEST: GET /static/js/smart-filter-system.js




📥 INCOMING REQUEST: GET /static/js/display-main.js

📥 INCOMING REQUEST: GET /static/js/modular-compliance-scoring.js
📥 INCOMING REQUEST: GET /static/js/modular-compliance-display.js





📥 INCOMING REQUEST: GET /static/js/metadata-display.js

📥 INCOMING REQUEST: GET /static/js/metadata-editor.js


📥 INCOMING REQUEST: GET /static/js/metadata-export.js



📥 INCOMING REQUEST: GET /static/js/metadata-feedback.js

📥 INCOMING REQUEST: GET /static/js/block-assembly.js

📥 INCOMING REQUEST: GET /static/js/core.js




📥 INCOMING REQUEST: GET /static/js/navigation.js

📥 INCOMING REQUEST: GET /static/js/elements-minimal.js



📥 INCOMING REQUEST: GET /static/js/index-page.js


📥 INCOMING REQUEST: GET /api/feedback/session


📥 INCOMING REQUEST: GET /api/feedback/session

INFO:app_modules.websocket_handlers:Client connected with session ID: 18b631a9-947e-4e84-9e07-5b7ee428438a

📥 INCOMING REQUEST: POST /analyze
   📋 Content-Type: application/json
   📋 Content-Length: 981
   📋 JSON Data Keys: ['content', 'format_hint', 'content_type', 'session_id']

INFO:database.dao:Stored document: 1700c698-302a-489b-b7e1-a898003cf0cd
INFO:database.dao:Created analysis session: b026bcee-41c3-4370-9515-f5af865a5c5d
INFO:database.services:Processed document upload: doc=1700c698-302a-489b-b7e1-a898003cf0cd, analysis=b026bcee-41c3-4370-9515-f5af865a5c5d
INFO:app_modules.api_routes:📄 Created database document: 1700c698-302a-489b-b7e1-a898003cf0cd, analysis: b026bcee-41c3-4370-9515-f5af865a5c5d
INFO:app_modules.api_routes:Starting analysis for session 18c21bcc-2b36-45c3-87e1-35eb83daabe0 with content_type=concept and confidence_threshold=None
✓ Loaded language vocabulary: inclusive_language_terms.yaml
INFO:validation.confidence.rule_reliability:Loaded reliability overrides generated at 2025-08-26 12:50:30
INFO:validation.confidence.rule_reliability:Applied 2 reliability overrides from /home/gtrivedi/Documents/GitLab/content-editorial-assiatant/validation/confidence/../config/reliability_overrides.yaml
✓ Loaded language vocabulary: verbs_corrections.yaml
✓ Loaded language vocabulary: anthropomorphism_entities.yaml
✓ Loaded language vocabulary: articles_phonetics.yaml
✓ Loaded language vocabulary: plurals_corrections.yaml
INFO:rules.legal_information.services.entity_detector:Initialized ensemble detector with 3 detectors
🔍 Confidence filtering: Removed 3/13 low-confidence errors (threshold: 0.350)
INFO:style_analyzer.analysis_modes:Context-aware modular rules analysis found 10 issues
INFO:rules.legal_information.services.entity_detector:Initialized ensemble detector with 3 detectors
🔍 Confidence filtering: Removed 1/9 low-confidence errors (threshold: 0.350)
INFO:style_analyzer.analysis_modes:Context-aware modular rules analysis found 8 issues
✓ Loaded spaCy model: en_core_web_sm
INFO:rules.legal_information.services.entity_detector:Initialized ensemble detector with 3 detectors
🔍 Confidence filtering: Removed 1/8 low-confidence errors (threshold: 0.350)
INFO:style_analyzer.analysis_modes:Context-aware modular rules analysis found 7 issues
INFO:style_analyzer.base_analyzer:Advanced modular compliance analysis completed for concept: 1 issues found
INFO:metadata_assistant.config:Using default configuration
INFO:metadata_assistant.config:Loaded taxonomy configuration with 9 categories
INFO:metadata_assistant.core:✅ Advanced TTL caching initialized
INFO:metadata_assistant.core:📊 Performance monitoring initialized
INFO:metadata_assistant.taxonomy_classifier:Initializing sentence transformer: all-MiniLM-L6-v2
INFO:sentence_transformers.SentenceTransformer:Load pretrained SentenceTransformer: all-MiniLM-L6-v2
INFO:sentence_transformers.SentenceTransformer:Use pytorch device_name: cpu
INFO:metadata_assistant.taxonomy_classifier:Sentence transformer initialized successfully
INFO:metadata_assistant.core:All extractors initialized successfully
INFO:metadata_assistant.core:MetadataAssistant initialized successfully
INFO:models.token_config:Initialized global TokenConfig: TokenConfig(base_max_tokens=2048)
ERROR:models.providers.api_provider:Cannot extract text from response. Keys available: ['choices', 'created', 'id', 'model', 'object', 'usage']
WARNING:models.providers.api_provider:API returned empty response
WARNING:models.model_manager:Model returned empty result
ERROR:models.providers.api_provider:Cannot extract text from response. Keys available: ['choices', 'created', 'id', 'model', 'object', 'usage']
WARNING:models.providers.api_provider:API returned empty response
WARNING:models.model_manager:Model returned empty result
Batches: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 53.10it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 130.36it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 131.64it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 139.92it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 131.10it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 156.86it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 157.62it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 138.65it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 102.09it/s]
Batches: 100%|████████████████████████████████████████████████████████████████████████████████████████████████| 1/1 [00:00<00:00, 161.51it/s]
INFO:database.dao:Stored 25 violations for analysis b026bcee-41c3-4370-9515-f5af865a5c5d
INFO:database.services:Stored 25 violations for analysis b026bcee-41c3-4370-9515-f5af865a5c5d
INFO:app_modules.api_routes:📊 Stored 25 violations in database
INFO:app_modules.api_routes:Analysis completed in 15.23s for session 18c21bcc-2b36-45c3-87e1-35eb83daabe0

📥 INCOMING REQUEST: GET /static/css/assets/fonts/RedHatMono/RedHatMono-Regular.woff2

INFO:app_modules.websocket_handlers:Client joined session: session_l1fkeavmw_1759224843678

📥 INCOMING REQUEST: POST /rewrite-block
   📋 Content-Type: application/json
   📋 Content-Length: 304088
   📋 JSON Data Keys: ['block_content', 'block_errors', 'block_type', 'block_id', 'session_id']


🔍 DEBUG API ROUTE: /rewrite-block
   📋 Block ID: block-1
   📋 Session ID: session_l1fkeavmw_1759224843678
   📋 Block Type: paragraph
   📋 Content Length: 232
   📋 Errors Count: 8
   📋 Content Preview: 'This document will provide an overview of the new features and improvements that have been implement'
INFO:app_modules.api_routes:Starting block rewrite for session session_l1fkeavmw_1759224843678, block block-1, type: paragraph
   📡 Emitting initial progress update...
   ✅ Initial progress update emitted to session: session_l1fkeavmw_1759224843678
   🔍 DEBUG AI Rewriter Structure:
      ai_rewriter type: <class 'rewriter.document_rewriter.DocumentRewriter'>
      hasattr(ai_rewriter, 'ai_rewriter'): True
      ai_rewriter.ai_rewriter type: <class 'rewriter.core.AIRewriter'>
      hasattr(ai_rewriter.ai_rewriter, 'assembly_line'): True
      assembly_line type: <class 'rewriter.assembly_line_rewriter.AssemblyLineRewriter'>
      assembly_line progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
      hasattr(ai_rewriter, 'assembly_line'): False
   🏭 Using DocumentRewriter -> AIRewriter -> AssemblyLine path

🔍 DEBUG ASSEMBLY LINE REWRITER:
   📋 Method called with:
      - block_content length: 232
      - block_errors count: 8
      - block_type: paragraph
      - session_id: session_l1fkeavmw_1759224843678
      - block_id: block-1
      - progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
      - progress_callback type: <class 'function'>
   🏭 Starting world-class assembly line processing
INFO:rewriter.assembly_line_rewriter:🏭 World-class assembly line processing: This document will provide an overview of the new ... with 8 errors

🔍 DEBUG PROGRESS TRACKER INIT:
   📋 session_id: session_l1fkeavmw_1759224843678
   📋 block_id: block-1
   📋 progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
   📋 progress_callback type: <class 'function'>
   📡 Attempting to import WebSocket handlers...
   ✅ WebSocket handlers imported successfully
   ✅ WorldClassProgressTracker initialized successfully
INFO:rewriter.progress_tracker:🎯 World-class progress tracker initialized for block-1
INFO:rewriter.progress_tracker:🏭 Initialized 1-pass processing with 3 stations (3 total work units)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Initializing assembly line processing... - Setting up multi-pass pipeline
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🏭 Multi-pass assembly line: 3 stations for 8 errors
INFO:rewriter.progress_tracker:🚀 Starting Pass 1/1: World-Class AI Processing

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Pass 1: World-Class AI Processing - Starting world-class ai processing processing...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔧 Pass 1/3 - Structural Pass: 4 errors
INFO:rewriter.progress_tracker:🏗️ Station Structural Pass: Processing 4 errors (Station 1/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Pass 1: Structural Pass - Processing 4 high issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 4 contextual

📥 INCOMING REQUEST: GET /static/css/patternfly.css

📥 INCOMING REQUEST: GET /static/css/home.css


📥 INCOMING REQUEST: GET /static/css/writing-analytics.css

📥 INCOMING REQUEST: GET /static/css/metadata-assistant.css


📥 INCOMING REQUEST: GET /static/css/patternfly-addons.css




📥 INCOMING REQUEST: GET /static/css/base-html.css


📥 INCOMING REQUEST: GET /static/css/index-page.css

INFO:rewriter.processors:🔧 Processing AI response: 255 chars vs original: 232 chars
INFO:rewriter.processors:✅ Clean processing complete: 'This document provides an overview of the new features and improvements that we have implemented. It...'
INFO:rewriter.assembly_line_rewriter:🧠 Contextual AI: 4 errors fixed
INFO:rewriter.progress_tracker:✅ Station Structural Pass completed: 4 errors fixed in 12.55s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 66% - Pass 1: Structural Pass - Completed - 4 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:✅ Structural Pass: 4 errors fixed, confidence: 0.75
INFO:rewriter.assembly_line_rewriter:🔧 Pass 2/3 - Grammar Pass: 2 errors
INFO:rewriter.progress_tracker:🏗️ Station Grammar Pass: Processing 2 errors (Station 2/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 33% - Pass 1: Grammar Pass - Processing 2 medium issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 2 contextual
INFO:rewriter.processors:🔧 Processing AI response: 238 chars vs original: 221 chars
INFO:rewriter.processors:✅ Clean processing complete: 'This document provides an overview of the new features and improvements we have implemented. It is i...'
INFO:rewriter.assembly_line_rewriter:🧠 Contextual AI: 2 errors fixed
INFO:rewriter.progress_tracker:✅ Station Grammar Pass completed: 2 errors fixed in 23.26s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1: Grammar Pass - Completed - 2 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:✅ Grammar Pass: 2 errors fixed, confidence: 0.90
INFO:rewriter.assembly_line_rewriter:🔧 Pass 3/3 - Style Pass: 2 errors
INFO:rewriter.progress_tracker:🏗️ Station Style Pass: Processing 2 errors (Station 3/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 66% - Pass 1: Style Pass - Processing 2 low issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 2 contextual
ERROR:models.providers.api_provider:Cannot extract text from response. Keys available: ['choices', 'created', 'id', 'model', 'object', 'usage']
WARNING:models.providers.api_provider:API returned empty response
WARNING:models.model_manager:Model returned empty result
WARNING:rewriter.assembly_line_rewriter:No changes made for 2 errors (surgical: 0, contextual: 2)
INFO:rewriter.progress_tracker:✅ Station Style Pass completed: 0 errors fixed in 22.82s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1: Style Pass - Completed - 0 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

WARNING:rewriter.assembly_line_rewriter:⚠️ Style Pass: No changes made
INFO:rewriter.progress_tracker:🎉 Pass 1 (World-Class AI Processing) completed: 3 stations in 58.64s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1 Complete - World-Class AI Processing completed - 3 stations processed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.progress_tracker:🏆 Processing complete: 6 errors fixed across 3 stations in 58.64s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Processing Complete - World-class AI rewriting complete - 6 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🏆 World-class assembly line processing complete: 6/8 errors fixed in 58640ms
   ✅ Assembly line processing completed
INFO:app_modules.api_routes:Block rewrite completed in 58.64s - 6 errors fixed

📥 INCOMING REQUEST: POST /rewrite-block
   📋 Content-Type: application/json
   📋 Content-Length: 304088
   📋 JSON Data Keys: ['block_content', 'block_errors', 'block_type', 'block_id', 'session_id']


🔍 DEBUG API ROUTE: /rewrite-block
   📋 Block ID: block-1
   📋 Session ID: session_l1fkeavmw_1759224843678
   📋 Block Type: paragraph
   📋 Content Length: 232
   📋 Errors Count: 8
   📋 Content Preview: 'This document will provide an overview of the new features and improvements that have been implement'
INFO:app_modules.api_routes:Starting block rewrite for session session_l1fkeavmw_1759224843678, block block-1, type: paragraph
   📡 Emitting initial progress update...
   ✅ Initial progress update emitted to session: session_l1fkeavmw_1759224843678
   🔍 DEBUG AI Rewriter Structure:
      ai_rewriter type: <class 'rewriter.document_rewriter.DocumentRewriter'>
      hasattr(ai_rewriter, 'ai_rewriter'): True
      ai_rewriter.ai_rewriter type: <class 'rewriter.core.AIRewriter'>
      hasattr(ai_rewriter.ai_rewriter, 'assembly_line'): True
      assembly_line type: <class 'rewriter.assembly_line_rewriter.AssemblyLineRewriter'>
      assembly_line progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
      hasattr(ai_rewriter, 'assembly_line'): False
   🏭 Using DocumentRewriter -> AIRewriter -> AssemblyLine path

🔍 DEBUG ASSEMBLY LINE REWRITER:
   📋 Method called with:
      - block_content length: 232
      - block_errors count: 8
      - block_type: paragraph
      - session_id: session_l1fkeavmw_1759224843678
      - block_id: block-1
      - progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
      - progress_callback type: <class 'function'>
   🏭 Starting world-class assembly line processing
INFO:rewriter.assembly_line_rewriter:🏭 World-class assembly line processing: This document will provide an overview of the new ... with 8 errors

🔍 DEBUG PROGRESS TRACKER INIT:
   📋 session_id: session_l1fkeavmw_1759224843678
   📋 block_id: block-1
   📋 progress_callback: <function initialize_services.<locals>.progress_callback at 0x7fcac9b21a80>
   📋 progress_callback type: <class 'function'>
   📡 Attempting to import WebSocket handlers...
   ✅ WebSocket handlers imported successfully
   ✅ WorldClassProgressTracker initialized successfully
INFO:rewriter.progress_tracker:🎯 World-class progress tracker initialized for block-1
INFO:rewriter.progress_tracker:🏭 Initialized 1-pass processing with 3 stations (3 total work units)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Initializing assembly line processing... - Setting up multi-pass pipeline
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🏭 Multi-pass assembly line: 3 stations for 8 errors
INFO:rewriter.progress_tracker:🚀 Starting Pass 1/1: World-Class AI Processing

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Pass 1: World-Class AI Processing - Starting world-class ai processing processing...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔧 Pass 1/3 - Structural Pass: 4 errors
INFO:rewriter.progress_tracker:🏗️ Station Structural Pass: Processing 4 errors (Station 1/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 0% - Pass 1: Structural Pass - Processing 4 high issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 4 contextual
INFO:rewriter.processors:🔧 Processing AI response: 255 chars vs original: 232 chars
INFO:rewriter.processors:✅ Clean processing complete: 'This document provides an overview of the new features and improvements that we have implemented. It...'
INFO:rewriter.assembly_line_rewriter:🧠 Contextual AI: 4 errors fixed
INFO:rewriter.progress_tracker:✅ Station Structural Pass completed: 4 errors fixed in 13.58s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 66% - Pass 1: Structural Pass - Completed - 4 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:✅ Structural Pass: 4 errors fixed, confidence: 0.75
INFO:rewriter.assembly_line_rewriter:🔧 Pass 2/3 - Grammar Pass: 2 errors
INFO:rewriter.progress_tracker:🏗️ Station Grammar Pass: Processing 2 errors (Station 2/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 33% - Pass 1: Grammar Pass - Processing 2 medium issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 2 contextual
ERROR:models.providers.api_provider:Cannot extract text from response. Keys available: ['choices', 'created', 'id', 'model', 'object', 'usage']
WARNING:models.providers.api_provider:API returned empty response
WARNING:models.model_manager:Model returned empty result
WARNING:rewriter.assembly_line_rewriter:No changes made for 2 errors (surgical: 0, contextual: 2)
INFO:rewriter.progress_tracker:✅ Station Grammar Pass completed: 0 errors fixed in 22.56s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1: Grammar Pass - Completed - 0 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

WARNING:rewriter.assembly_line_rewriter:⚠️ Grammar Pass: No changes made
INFO:rewriter.assembly_line_rewriter:🔧 Pass 3/3 - Style Pass: 2 errors
INFO:rewriter.progress_tracker:🏗️ Station Style Pass: Processing 2 errors (Station 3/3)

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 66% - Pass 1: Style Pass - Processing 2 low issue(s)...
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🔬 Error routing: 0 surgical, 2 contextual
ERROR:models.providers.api_provider:Cannot extract text from response. Keys available: ['choices', 'created', 'id', 'model', 'object', 'usage']
WARNING:models.providers.api_provider:API returned empty response
WARNING:models.model_manager:Model returned empty result
WARNING:rewriter.assembly_line_rewriter:No changes made for 2 errors (surgical: 0, contextual: 2)
INFO:rewriter.progress_tracker:✅ Station Style Pass completed: 0 errors fixed in 24.20s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1: Style Pass - Completed - 0 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

WARNING:rewriter.assembly_line_rewriter:⚠️ Style Pass: No changes made
INFO:rewriter.progress_tracker:🎉 Pass 1 (World-Class AI Processing) completed: 3 stations in 60.33s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Pass 1 Complete - World-Class AI Processing completed - 3 stations processed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.progress_tracker:🏆 Processing complete: 4 errors fixed across 3 stations in 60.33s

🔍 DEBUG PROGRESS EMIT:
   📊 Emitting progress: 100% - Processing Complete - World-class AI rewriting complete - 4 errors fixed
   📋 session_id: session_l1fkeavmw_1759224843678 
   📋 progress_callback available: True
   📋 websocket_available: True
   📞 Calling progress_callback...
🔍 DEBUG PROGRESS CALLBACK: Emitted to session_l1fkeavmw_1759224843678
   ✅ Progress callback executed successfully
   📡 Calling emit_progress WebSocket...
   ✅ WebSocket progress emitted successfully to session_l1fkeavmw_1759224843678
   ✅ Progress emit complete

INFO:rewriter.assembly_line_rewriter:🏆 World-class assembly line processing complete: 4/8 errors fixed in 60334ms
   ✅ Assembly line processing completed
INFO:app_modules.api_routes:Block rewrite completed in 60.34s - 4 errors fixed