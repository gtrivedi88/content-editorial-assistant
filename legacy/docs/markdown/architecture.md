# Content Editorial Assistant - System architecture

## [](<#_overview>)1\. Overview

Content Editorial Assistant is a comprehensive technical writing assistant that combines AI-powered rewriting with sophisticated style analysis. This document provides an exhaustive breakdown of every component, file, and their interconnections.

**Key Features:**

  * **AI-Powered rewriting** : Two-pass iterative improvement using local Ollama models

  * **Comprehensive style analysis** : Multi-mode analysis with IBM Style Guide rules

  * **Structural document parsing** : Format-aware processing for AsciiDoc and Markdown

  * **Ambiguity detection** : Specialized system for identifying unclear content

  * **Real-time progress tracking** : WebSocket-based progress updates

  * **Multi-format support** : PDF, DOCX, MD, ADOC, DITA, TXT

## [](<#_complete_project_structure>)2\. Complete project structure
[code] 
    content-editorial-assistant/
    ├── main.py                         # Main application entry point (production)
    ├── config.py                       # Application configuration
    ├── requirements.txt                # Python dependencies
    ├── README.md                       # Project documentation
    ├── CLAUDE.md                       # AI assistant documentation
    ├──
    ├── app_modules/                    # Modular Flask application components
    │   ├── __init__.py                 # Package initialization
    │   ├── app_factory.py              # Flask factory pattern implementation
    │   ├── api_routes.py               # HTTP API route handlers
    │   ├── error_handlers.py           # Global error handling
    │   ├── websocket_handlers.py       # WebSocket event handlers
    │   ├── fallback_services.py        # Fallback service implementations
    │   ├── feedback_storage.py         # User feedback management
    │   └── pdf_report_generator.py     # PDF report generation
    ├──
    ├── ui/                             # User interface components
    │   ├── templates/                  # HTML templates
    │   │   ├── base.html               # Base template
    │   │   ├── index.html              # Main application page
    │   │   └── error.html              # Error page template
    │   └── static/                     # Static web assets
    │       ├── css/
    │       │   └── styles.css          # Application styles
    │       └── js/
    │           ├── core.js             # Core JavaScript functionality
    │           ├── file-handler.js     # File upload handling
    │           ├── socket-handler.js   # WebSocket communication
    │           ├── analysis-display.js # Analysis results display
    │           └── utility-functions.js # Utility functions
    ├──
    ├── style_analyzer/                 # Style analysis engine
    │   ├── __init__.py                 # Package initialization
    │   ├── base_analyzer.py            # Main StyleAnalyzer class
    │   ├── base_types.py               # Type definitions
    │   ├── analysis_modes.py           # Analysis mode implementations
    │   ├── core_analyzer.py            # Core analysis logic
    │   ├── block_processors.py         # Block-level processing
    │   ├── sentence_analyzer.py        # Sentence-level analysis
    │   ├── readability_analyzer.py     # Readability calculations
    │   ├── statistics_calculator.py    # Statistics computation
    │   ├── structural_analyzer.py      # Structural analysis
    │   ├── suggestion_generator.py     # Improvement suggestions
    │   └── error_converters.py         # Error format conversion
    ├──
    ├── rules/                          # Style guide rules system
    │   ├── __init__.py                 # Rules registry and discovery
    │   ├── base_rule.py                # Base rule class
    │   ├── rule_mappings.yaml          # Rule configuration mapping
    │   ├── ambiguity_rule.py           # Ambiguity detection integration
    │   ├── second_person_rule.py       # Second person detection
    │   ├── sentence_length_rule.py     # Sentence length validation
    │   ├──
    │   ├── language_and_grammar/       # Language and grammar rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_language_rule.py   # Base language rule
    │   │   ├── abbreviations_rule.py   # Abbreviations checking
    │   │   ├── adverbs_only_rule.py    # Adverb usage rules
    │   │   ├── anthropomorphism_rule.py # Anthropomorphism detection
    │   │   ├── articles_rule.py        # Article usage rules
    │   │   ├── capitalization_rule.py  # Capitalization rules
    │   │   ├── conjunctions_rule.py    # Conjunction rules
    │   │   ├── contractions_rule.py    # Contraction rules
    │   │   ├── inclusive_language_rule.py # Inclusive language
    │   │   ├── plurals_rule.py         # Plural forms
    │   │   ├── possessives_rule.py     # Possessive forms
    │   │   ├── prepositions_rule.py    # Preposition rules
    │   │   ├── pronouns_rule.py        # Pronoun rules
    │   │   ├── spelling_rule.py        # Spelling validation
    │   │   ├── terminology_rule.py     # Terminology consistency
    │   │   └── verbs_rule.py           # Verb usage rules
    │   ├──
    │   ├── punctuation/                # Punctuation rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_punctuation_rule.py # Base punctuation rule
    │   │   ├── colons_rule.py          # Colon usage
    │   │   ├── commas_rule.py          # Comma usage
    │   │   ├── dashes_rule.py          # Dash usage
    │   │   ├── ellipses_rule.py        # Ellipsis usage
    │   │   ├── exclamation_points_rule.py # Exclamation points
    │   │   ├── hyphens_rule.py         # Hyphen usage
    │   │   ├── parentheses_rule.py     # Parentheses usage
    │   │   ├── periods_rule.py         # Period usage
    │   │   ├── punctuation_and_symbols_rule.py # General punctuation
    │   │   ├── quotation_marks_rule.py # Quotation marks
    │   │   ├── semicolons_rule.py      # Semicolon usage
    │   │   ├── slashes_rule.py         # Slash usage
    │   │   └── spacing_rule.py         # Spacing rules
    │   ├──
    │   ├── structure_and_format/       # Structure and format rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_structure_rule.py  # Base structure rule
    │   │   ├── admonitions_rule.py     # Admonition blocks
    │   │   ├── admonition_content_rule.py # Admonition content validation
    │   │   ├── headings_rule.py        # Heading structure
    │   │   ├── highlighting_rule.py    # Text highlighting
    │   │   ├── lists_rule.py           # List formatting
    │   │   ├── list_punctuation_rule.py # List punctuation
    │   │   ├── messages_rule.py        # Message formatting
    │   │   ├── notes_rule.py           # Note formatting
    │   │   ├── paragraphs_rule.py      # Paragraph structure
    │   │   ├── procedures_rule.py      # Procedure formatting
    │   │   ├── glossaries_rule.py      # Glossary formatting
    │   │   └── indentation_rule.py     # Indentation rules
    │   ├──
    │   ├── audience_and_medium/        # Audience and medium rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_audience_rule.py   # Base audience rule
    │   │   ├── conversational_style_rule.py # Conversational style
    │   │   ├── global_audiences_rule.py # Global audience considerations
    │   │   ├── llm_consumability_rule.py # LLM consumability
    │   │   ├── tone_rule.py            # Tone validation
    │   │   └── config/                 # Configuration files
    │   │       ├── conversational_vocabularies.yaml
    │   │       ├── global_patterns.yaml
    │   │       ├── llm_patterns.yaml
    │   │       └── tone_vocabularies.yaml
    │   ├──
    │   ├── legal_information/          # Legal information rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_legal_rule.py      # Base legal rule
    │   │   ├── claims_rule.py          # Legal claims validation
    │   │   ├── company_names_rule.py   # Company name usage
    │   │   ├── personal_information_rule.py # Personal information handling
    │   │   └── config/                 # Configuration files
    │   │       └── companies.yaml      # Company name database
    │   ├──
    │   ├── modular_compliance/         # Modular documentation compliance
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── assembly_module_rule.py # Assembly module compliance
    │   │   ├── concept_module_rule.py  # Concept module compliance
    │   │   ├── procedure_module_rule.py # Procedure module compliance
    │   │   ├── reference_module_rule.py # Reference module compliance
    │   │   ├── template_compliance_rule.py # Template compliance
    │   │   ├── cross_reference_rule.py # Cross-reference validation
    │   │   ├── inter_module_analysis_rule.py # Inter-module analysis
    │   │   ├── advanced_modular_analyzer.py # Advanced analysis
    │   │   ├── modular_structure_bridge.py # Structure bridge
    │   │   └── config/                 # Configuration files
    │   ├──
    │   ├── numbers_and_measurement/    # Numbers and measurement rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_numbers_rule.py    # Base numbers rule
    │   │   ├── numbers_rule.py         # Number formatting
    │   │   ├── numerals_vs_words_rule.py # Numerals vs words
    │   │   ├── currency_rule.py        # Currency formatting
    │   │   ├── dates_and_times_rule.py # Date and time formatting
    │   │   ├── units_of_measurement_rule.py # Unit formatting
    │   │   └── config/                 # Configuration files
    │   ├──
    │   ├── references/                 # Reference rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_references_rule.py # Base references rule
    │   │   ├── citations_rule.py       # Citation formatting
    │   │   ├── geographic_locations_rule.py # Geographic locations
    │   │   ├── names_and_titles_rule.py # Names and titles
    │   │   ├── product_names_rule.py   # Product name usage
    │   │   ├── product_versions_rule.py # Product version formatting
    │   │   └── config/                 # Configuration files
    │   ├──
    │   ├── technical_elements/         # Technical elements rules
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_technical_rule.py  # Base technical rule
    │   │   ├── commands_rule.py        # Command formatting
    │   │   ├── files_and_directories_rule.py # File/directory formatting
    │   │   ├── keyboard_keys_rule.py   # Keyboard key formatting
    │   │   ├── mouse_buttons_rule.py   # Mouse button formatting
    │   │   ├── programming_elements_rule.py # Programming element formatting
    │   │   ├── ui_elements_rule.py     # UI element formatting
    │   │   ├── web_addresses_rule.py   # Web address formatting
    │   │   └── config/                 # Configuration files
    │   └──
    │   └── word_usage/                 # Word usage rules (IBM specific)
    │       ├── __init__.py             # Package initialization
    │       └── [29 word-specific rules] # Individual word usage rules
    ├──
    ├── ambiguity/                      # Ambiguity detection system
    │   ├── __init__.py                 # Package initialization
    │   ├── types.py                    # Type definitions
    │   ├── ambiguity_rule.py           # Main ambiguity rule
    │   ├── base_ambiguity_rule.py      # Base ambiguity rule
    │   ├── config/
    │   │   └── ambiguity_types.yaml    # Ambiguity type configuration
    │   ├── detectors/                  # Specific ambiguity detectors
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── missing_actor_detector.py # Missing actor detection
    │   │   ├── pronoun_ambiguity_detector.py # Pronoun ambiguity
    │   │   ├── unsupported_claims_detector.py # Unsupported claims
    │   │   └── fabrication_risk_detector.py # Fabrication risk
    │   └── resolvers/                  # Ambiguity resolution (future)
    │       └── __init__.py             # Package initialization
    ├──
    ├── rewriter/                       # AI rewriting system
    │   ├── __init__.py                 # Package initialization
    │   ├── core.py                     # AIRewriter base class
    │   ├── document_rewriter.py        # Main DocumentRewriter class
    │   ├── assembly_line_rewriter.py   # Assembly line approach
    │   ├── surgical_snippet_processor.py # Surgical precision processing
    │   ├── generators.py               # Text generation
    │   ├── processors.py               # Text processing
    │   ├── evaluators.py               # Rewrite evaluation
    │   ├── prompts.py                  # Prompt generation
    │   ├── example_selector.py         # Example selection for prompts
    │   ├── output_enforcer.py          # Output format enforcement
    │   ├── progress_tracker.py         # Progress tracking
    │   ├── station_mapper.py           # Station mapping for assembly line
    │   ├── assembly_line_config.yaml   # Assembly line configuration
    │   ├── quality_control_config.py   # Quality control settings
    │   └── multi_shot_examples.yaml    # Multi-shot example repository
    ├──
    ├── structural_parsing/             # Document structure parsing
    │   ├── __init__.py                 # Package initialization
    │   ├── format_detector.py          # Format detection
    │   ├── parser_factory.py           # Parser factory
    │   ├── extractors/                 # Document extraction
    │   │   ├── __init__.py             # Package initialization
    │   │   └── document_processor.py   # Document processing
    │   ├── markdown/                   # Markdown parsing
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── parser.py               # Markdown parser
    │   │   └── types.py                # Markdown types
    │   ├── asciidoc/                   # AsciiDoc parsing
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── parser.py               # AsciiDoc parser
    │   │   ├── ruby_client.py          # Ruby subprocess client
    │   │   ├── types.py                # AsciiDoc types
    │   │   └── ruby_scripts/           # Ruby parsing scripts
    │   │       └── asciidoc_parser.rb  # Asciidoctor parser
    │   ├── dita/                       # DITA XML parsing
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── parser.py               # DITA parser
    │   │   └── types.py                # DITA types
    │   └── plaintext/                  # Plain text parsing
    │       ├── __init__.py             # Package initialization
    │       ├── parser.py               # Plain text parser
    │       └── types.py                # Plain text types
    ├──
    ├── shared/                         # Shared utilities and singletons
    │   ├── __init__.py                 # Package initialization
    │   └── spacy_singleton.py          # SpaCy model singleton (performance)
    ├──
    ├── docs/                           # Antora-based documentation system
    │   ├── antora-playbook.yml         # Antora build configuration
    │   ├── antora.yml                  # Component configuration
    │   ├── modules/
    │   │   ├── ROOT/                   # Main documentation
    │   │   │   ├── nav.adoc            # Navigation structure
    │   │   │   └── pages/
    │   │   │       ├── index.adoc      # Documentation homepage
    │   │   │       ├── getting-started.adoc # Setup guide
    │   │   │       └── api-reference.adoc   # Complete API docs
    │   │   ├── architecture/           # Architecture documentation
    │   │   │   └── pages/
    │   │   │       └── architecture.adoc    # This document
    │   │   └── how-to/                # How-to guides
    │   │       └── pages/
    │   │           ├── how-to-add-new-rule.adoc
    │   │           ├── how-to-add-new-ambiguity-detector.adoc
    │   │           └── how-to-add-new-model.adoc
    │   ├── antora-lunr-ui/            # Custom UI components
    │   └── package.json               # Node.js dependencies
    ├──
    ├── llamastack/                     # LlamaStack configuration
    │   └── config.yaml                 # LlamaStack deployment config
    ├──
    ├── models/                         # AI model management system
    │   ├── __init__.py                 # Package initialization
    │   ├── config.py                   # Model configuration
    │   ├── factory.py                  # Model factory pattern
    │   ├── model_manager.py            # Model lifecycle management
    │   ├── providers/                  # Model provider implementations
    │   │   ├── ollama_provider.py      # Local Ollama integration
    │   │   ├── api_provider.py         # Remote API integration
    │   │   ├── llamastack_provider.py  # Enterprise LlamaStack
    │   │   └── base_provider.py        # Provider base class
    │   └── README.md                   # Model system documentation
    ├──
    ├── database/                       # Database layer
    │   ├── __init__.py                 # Package initialization
    │   ├── models.py                   # SQLAlchemy models
    │   ├── dao.py                      # Data access objects
    │   └── services.py                 # Database services
    ├──
    ├── migrations/                     # Database migrations
    │   ├── init_database.py            # Database initialization
    │   └── add_feedback_unique_constraint.py # Schema updates
    ├──
    ├── error_consolidation/            # Error processing system
    │   ├── __init__.py                 # Package initialization
    │   ├── consolidator.py             # Main error consolidation logic
    │   ├── message_merger.py           # Message deduplication and merging
    │   ├── rule_priority.py            # Rule priority management
    │   ├── text_span_analyzer.py       # Text span overlap analysis
    │   └── config/                     # Configuration files
    │       ├── consolidation_rules.yaml # Consolidation rules
    │       └── priority_mappings.yaml  # Priority mappings
    ├──
    ├── validation/                     # Validation and monitoring
    │   ├── __init__.py                 # Package initialization
    │   ├── confidence/                 # Confidence scoring system
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── confidence_calculator.py # Confidence calculations
    │   │   ├── context_analyzer.py     # Context analysis
    │   │   ├── domain_classifier.py    # Domain classification
    │   │   ├── linguistic_anchors.py   # Linguistic anchor detection
    │   │   └── rule_reliability.py     # Rule reliability tracking
    │   ├── feedback/                   # Feedback processing
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── instruction_template_tracker.py # Template tracking
    │   │   └── reliability_tuner.py    # Reliability tuning
    │   ├── monitoring/                 # System monitoring
    │   │   ├── __init__.py             # Package initialization
    │   │   └── metrics.py              # Prometheus metrics
    │   ├── multi_pass/                 # Multi-pass validation
    │   │   ├── __init__.py             # Package initialization
    │   │   ├── base_validator.py       # Base validator
    │   │   ├── validation_pipeline.py  # Validation pipeline
    │   │   └── pass_validators/        # Individual validators
    │   │       ├── context_validator.py # Context validation
    │   │       ├── cross_rule_validator.py # Cross-rule validation
    │   │       ├── domain_validator.py # Domain validation
    │   │       └── morphological_validator.py # Morphological validation
    │   ├── config/                     # Configuration files
    │   │   ├── confidence_weights.yaml # Confidence weight settings
    │   │   ├── linguistic_anchors.yaml # Linguistic anchor patterns
    │   │   ├── reliability_overrides.yaml # Reliability overrides
    │   │   └── validation_thresholds.yaml # Validation thresholds
    │   └── negative_example_validator.py # Negative example validation
    ├──
    ├── rule_enhancements/              # Rule enhancement system
    │   ├── __init__.py                 # Package initialization
    │   ├── enterprise_integration.py   # Enterprise integration
    │   ├── evidence_orchestrator.py    # Evidence orchestration
    │   ├── nlp_correction_layer.py     # NLP correction layer
    │   └── README.md                   # Enhancement documentation
    ├──
    ├── testing_agent/                  # Automated testing and analysis
    │   ├── __init__.py                 # Package initialization
    │   ├── test_runner.py              # Test runner
    │   ├── test_analyzer.py            # Test analysis
    │   ├── report_generator.py         # Report generation
    │   ├── config.py                   # Configuration
    │   └── README.md                   # Testing documentation
    ├──
    ├── validation/                     # Validation and monitoring
    │   ├── confidence/                 # Confidence scoring system
    │   ├── feedback/                   # Feedback processing
    │   ├── monitoring/                 # System monitoring
    │   └── multi_pass/                 # Multi-pass validation
    ├──
    ├── uploads/                        # Uploaded files (temporary)
    ├── instance/                       # Instance-specific files
    ├── feedback_data/                  # User feedback storage
    │   ├── aggregated/                 # Processed feedback data
    │   ├── daily/                      # Daily feedback logs
    │   └── sessions/                   # Session-based feedback
    ├──
    ├── scripts/                        # Utility scripts
    │   ├── run_quality_checks.py       # Quality assurance
    │   ├── tune_reliability.py         # Performance tuning
    │   ├── memory_profiler.py          # Memory profiling
    │   ├── apply_universal_code_guard.py # Code guard application
    │   ├── load_test_blocks.py         # Load testing
    │   ├── validate_guards.py          # Guard validation
    │   └── websocket_stress_test.py    # WebSocket load testing
    ├──
    ├── Dockerfile                      # Docker image definition
    ├── gunicorn.conf.py                # Gunicorn production server config
    ├── openshift-deployment-patch.yaml # OpenShift deployment config
    ├── openshift-route.yaml            # OpenShift routing config
    ├── deploy.sh                       # Deployment automation script
    ├── main.sh                         # Container startup script
    ├──
    ├── uploads/                        # Uploaded files (temporary)
    ├── temp/                           # Temporary processing files
    ├── logs/                           # Application logs
    └── venv/                           # Virtual environment
[/code]

## [](<#_high_level_system_architecture>)3\. High-level system architecture
[code] 
    graph TB
        subgraph "Client Layer"
            WEB[Web Browser]
            UI[Modern UI Interface]
        end
    
        subgraph "Application Layer"
            FLASK[Flask Application]
            WS[WebSocket Handler]
            API[REST API Routes]
            ERR[Error Handlers]
        end
    
        subgraph "Core Processing Layer"
            SA[Style Analyzer]
            AI[DocumentRewriter]
            SP[Structural Parser]
            AD[Ambiguity Detector]
            VAL[Validation System]
        end
    
        subgraph "Service Layer"
            DOC[Document Processor]
            RULES[Rules Engine]
            MODELS[Model Manager]
            EVAL[Evaluator]
            CONF[Confidence Calculator]
            ENH[Rule Enhancements]
        end
    
        subgraph "External Services"
            OLLAMA[Ollama/AI APIs]
            SPACY[SpaCy NLP]
            RUBY[Ruby Subprocess]
            SENT[Sentence Transformers]
        end
    
        subgraph "Data Layer"
            DB[(SQLite Database)]
            UPLOAD[File Storage]
            LOGS[Log Files]
            CONFIG[Configuration]
            FEEDBACK[Feedback Data]
        end
    
        subgraph "Monitoring"
            PROM[Prometheus Metrics]
            HEALTH[Health Checks]
        end
    
        WEB --> UI
        UI --> FLASK
        FLASK --> WS
        FLASK --> API
        FLASK --> ERR
    
        API --> SA
        API --> AI
        API --> DOC
    
        SA --> SP
        SA --> AD
        SA --> RULES
        SA --> VAL
    
        AI --> MODELS
        AI --> EVAL
    
        VAL --> CONF
        VAL --> ENH
    
        SP --> RUBY
        SA --> SPACY
        SA --> SENT
        AI --> OLLAMA
    
        DOC --> UPLOAD
        FLASK --> LOGS
        FLASK --> CONFIG
        FLASK --> DB
        FLASK --> FEEDBACK
    
        FLASK --> PROM
        FLASK --> HEALTH
[/code]

## [](<#_component_interaction_flow>)4\. Component interaction flow
[code] 
    sequenceDiagram
        participant Client
        participant Flask
        participant StyleAnalyzer
        participant StructuralParser
        participant RulesEngine
        participant ValidationSystem
        participant AIRewriter
        participant DocumentRewriter
        participant Ollama
    
        Client->>Flask: Upload document / Input text
        Flask->>StyleAnalyzer: analyze_with_blocks()
        StyleAnalyzer->>StructuralParser: parse_document()
        StructuralParser->>StructuralParser: Detect format (MD/ADOC/DITA)
        StructuralParser->>StyleAnalyzer: Return structured blocks
        StyleAnalyzer->>RulesEngine: Apply rules to blocks
        RulesEngine->>ValidationSystem: Validate detections
        ValidationSystem->>StyleAnalyzer: Return validated errors
        StyleAnalyzer->>Flask: Return analysis results
        Flask->>Client: Display analysis (via WebSocket)
    
        Client->>Flask: Request AI rewrite
        Flask->>DocumentRewriter: rewrite_document_with_structure_preservation()
        DocumentRewriter->>AIRewriter: Assembly line rewrite
        AIRewriter->>Ollama: Generate improvements (surgical)
        Ollama->>AIRewriter: Return rewritten segments
        AIRewriter->>DocumentRewriter: Return rewrite results
        DocumentRewriter->>Flask: Return final results
        Flask->>Client: Show rewrite results
[/code]

## [](<#_entry_point_and_configuration>)5\. Entry point and configuration

### [](<#_main_application_entry_point>)5.1. Main application entry point

#### [](<#_main_py>)5.1.1. `main.py`

The main application file that bootstraps the entire system for production deployment.

**Purpose** : Production entry point for the Content Editorial Assistant **Key Functions** : \- Initializes LlamaStack client for enterprise deployment \- Creates Flask app using factory pattern \- Configures upload settings and directories \- Handles graceful shutdown and signals \- Supports both development and production environments

**Dependencies** : \- `app_modules.app_factory`: Application factory \- `config`: Configuration management \- `llama_stack_client`: Enterprise AI model integration

**Code Structure** :
[code] 
    from app_modules.app_factory import create_app, configure_upload_folder
    from config import Config
    
    # Initialize LlamaStack client for enterprise deployment
    setup_llama_stack_client()
    
    # Create application using factory pattern
    app, socketio = create_app(Config)
    configure_upload_folder(app)
    
    # Add LlamaStack client to app context
    if llama_stack_client:
        app.llama_stack_client = llama_stack_client
[/code]

#### [](<#_requirements_txt>)5.1.2. `requirements.txt`

Python dependencies specification with cross-platform compatibility.

**Purpose** : Defines all Python package dependencies **Key Dependencies** : \- Flask 3.0+ (Web framework) \- SpaCy 3.7+ (NLP processing) \- Transformers 4.36+ (AI models) \- Ollama 0.1.7+ (Local AI models) \- PyMuPDF, python-docx (Document processing)

#### [](<#_setup_py>)5.1.3. `setup.py`

Installation and configuration script for the application.

**Purpose** : Package installation, dependency management, and testing **Key Functions** : \- `install_spacy_model()`: Downloads SpaCy language model \- `test_installation()`: Validates successful installation \- `setup()`: Package configuration with entry points

### [](<#_configuration_layer>)5.2. Configuration layer

#### [](<#_config_py>)5.2.1. `config.py`

Central configuration management for the entire application.

**Purpose** : Environment-based configuration with fallbacks **Key Classes** : \- `Config`: Main configuration class \- `DevelopmentConfig`: Development-specific settings

**Configuration Categories** : \- **Flask Configuration** : Secret keys, debug settings, auto-generated secure keys \- **Database Configuration** : SQLAlchemy settings with connection pooling \- **File Upload Configuration** : 16MB size limits, multi-format support \- **Style Guide Rules Configuration** : Rule thresholds and confidence settings \- **Block Processing Configuration** : Timeout, retry, and batch size settings \- **Performance Monitoring** : Error rate monitoring, WebSocket configuration \- **Environment-Specific Settings** : Development vs. production configurations

**Key Methods** : \- `get_ai_config()`: Returns AI model configuration \- `is_ollama_enabled()`: Checks if Ollama is configured \- `get_upload_config()`: Returns file upload settings \- `get_analysis_config()`: Returns style analysis configuration

## [](<#_application_layer_components>)6\. Application layer components

### [](<#_flask_application_factory>)6.1. Flask application factory

#### [](<#_app_modulesapp_factory_py>)6.1.1. `app_modules/app_factory.py`

Implements the Flask factory pattern for modular application creation.

**Purpose** : Creates and configures Flask application with all components **Key Functions** : \- `create_app(config_class)`: Main factory function \- `initialize_services()`: Service initialization with fallbacks \- `setup_logging(app)`: Logging configuration \- `log_initialization_status()`: Service status reporting \- `register_cleanup_handlers()`: Graceful shutdown handlers

**Service Initialization Pattern** :
[code] 
    try:
        from structural_parsing.extractors import DocumentProcessor
        services['document_processor'] = DocumentProcessor()
        services['document_processor_available'] = True
    except ImportError:
        services['document_processor'] = SimpleDocumentProcessor()
        services['document_processor_available'] = False
[/code]

#### [](<#_app_modulesapi_routes_py>)6.1.2. `app_modules/api_routes.py`

HTTP API route handlers for all application endpoints.

**Purpose** : Defines all REST API endpoints and their handlers **Key Routes** : \- `GET /`: Main application page \- `POST /upload`: File upload and text extraction \- `POST /analyze`: Text analysis with style checking \- `POST /rewrite`: AI-powered rewriting (Pass 1) \- `POST /refine`: AI-powered refinement (Pass 2) \- `GET /health`: Health check endpoint

**Route Handler Pattern** :
[code] 
    @app.route('/analyze', methods=['POST'])
    def analyze_content():
        data = request.get_json()
        content = data.get('content', '')
    
        # Emit progress via WebSocket
        emit_progress(session_id, 'analysis_start', 'Starting analysis...', 5)
    
        # Perform analysis
        result = style_analyzer.analyze_with_blocks(content)
    
        # Return results
        return jsonify(result)
[/code]

#### [](<#_app_moduleserror_handlers_py>)6.1.3. `app_modules/error_handlers.py`

Global error handling for HTTP errors and application exceptions.

**Purpose** : Provides user-friendly error pages and JSON error responses **Key Handlers** : \- `404 Not Found`: Page not found errors \- `500 Internal Server Error`: Application errors \- `413 Request Entity Too Large`: File upload size errors \- `400 Bad Request`: Invalid request errors \- `429 Too Many Requests`: Rate limiting errors \- `Exception`: Catch-all for unexpected errors

#### [](<#_app_moduleswebsocket_handlers_py>)6.1.4. `app_modules/websocket_handlers.py`

Real-time communication for progress updates and notifications.

**Purpose** : WebSocket event handling for real-time feedback **Key Functions** : \- `emit_progress()`: Send progress updates to clients \- `emit_completion()`: Send completion notifications \- `setup_websocket_handlers()`: Configure WebSocket events

**Event Handlers** : \- `connect`: Client connection handling \- `disconnect`: Client disconnection handling \- `join_session`: Session-based room management

#### [](<#_app_modulesfallback_services_py>)6.1.5. `app_modules/fallback_services.py`

Fallback service implementations when dependencies are unavailable.

**Purpose** : Graceful degradation when services fail to initialize **Fallback Classes** : \- `SimpleDocumentProcessor`: Basic text extraction \- `SimpleStyleAnalyzer`: Rule-based analysis without SpaCy \- `SimpleAIRewriter`: Basic rewriting with Ollama fallback

## [](<#_error_consolidation_system>)7\. Error consolidation system

### [](<#_purpose_and_design>)7.1. Purpose and design

The error consolidation system intelligently groups, deduplicates, and prioritizes detected issues to provide clear, actionable feedback without overwhelming users.

### [](<#_core_components>)7.2. Core components

#### [](<#_error_consolidationconsolidator_py>)7.2.1. `error_consolidation/consolidator.py`

Main orchestrator for error consolidation.

**Purpose** : Manages the complete error consolidation pipeline

**Key Features** : \- Overlap detection for co-located errors \- Rule priority management \- Message merging for similar issues \- Confidence-based filtering

**Process Flow** :
[code] 
    def consolidate_errors(errors: List[Dict]) -> List[Dict]:
        # 1. Group errors by location overlap
        grouped = self.text_span_analyzer.group_overlapping(errors)
    
        # 2. Apply priority rules (highest priority wins)
        prioritized = self.rule_priority.apply_priorities(grouped)
    
        # 3. Merge similar messages
        merged = self.message_merger.merge_similar(prioritized)
    
        # 4. Return consolidated errors
        return merged
[/code]

#### [](<#_error_consolidationmessage_merger_py>)7.2.2. `error_consolidation/message_merger.py`

Intelligent message deduplication and combination.

**Purpose** : Merge similar error messages to reduce noise

**Key Functions** : \- Semantic similarity detection \- Message template matching \- Combined suggestion generation \- Evidence aggregation

#### [](<#_error_consolidationrule_priority_py>)7.2.3. `error_consolidation/rule_priority.py`

Rule priority management system.

**Purpose** : Determine which rule takes precedence when multiple rules flag the same text

**Priority Factors** : \- Rule category importance \- Confidence scores \- Context specificity \- User feedback history

#### [](<#_error_consolidationtext_span_analyzer_py>)7.2.4. `error_consolidation/text_span_analyzer.py`

Text span overlap detection and analysis.

**Purpose** : Identify when multiple rules detect issues in overlapping text

**Key Methods** : \- `find_overlaps()`: Detect overlapping error spans \- `calculate_overlap_percentage()`: Measure overlap degree \- `group_by_proximity()`: Cluster nearby errors \- `resolve_conflicts()`: Handle competing detections

### [](<#_configuration>)7.3. Configuration

#### [](<#_configconsolidation_rules_yaml>)7.3.1. `config/consolidation_rules.yaml`

Defines how errors should be consolidated:
[code] 
    consolidation_rules:
      # Merge similar passive voice detections
      passive_voice:
        merge_threshold: 0.8
        max_distance: 50  # characters
        priority: medium
    
      # Keep all ambiguity detections separate
      ambiguity:
        merge_threshold: 0.0
        priority: high
[/code]

#### [](<#_configpriority_mappings_yaml>)7.3.2. `config/priority_mappings.yaml`

Rule priority hierarchy:
[code] 
    priority_levels:
      critical:
        - fabrication_risk
        - unsupported_claims
      high:
        - ambiguous_pronoun
        - missing_actor
      medium:
        - passive_voice
        - sentence_length
      low:
        - stylistic_preferences
[/code]

### [](<#_integration_pattern>)7.4. Integration pattern
[code] 
    from error_consolidation import ErrorConsolidator
    
    # In style analyzer
    consolidator = ErrorConsolidator()
    
    # After all rules have run
    raw_errors = collect_all_rule_outputs()
    
    # Consolidate errors
    consolidated = consolidator.consolidate_errors(raw_errors)
    
    # Return to user
    return {
        'errors': consolidated,
        'original_count': len(raw_errors),
        'consolidated_count': len(consolidated)
    }
[/code]

## [](<#_database_and_analytics>)8\. Database and analytics

### [](<#_database_schema_extensions>)8.1. Database schema extensions

#### [](<#_phase_3_analytics_models>)8.1.1. Phase 3 analytics models

### [](<#_database_services>)8.2. Database services

#### [](<#_databaseservices_py>)8.2.1. `database/services.py`

High-level database services providing business logic.

**Key Services** :

**Analytics Service** :
[code] 
    class AnalyticsService:
        def record_performance(self, analysis_id, metrics):
            """Record content performance metrics"""
    
        def get_performance_trends(self, date_range):
            """Get performance trends over time"""
    
        def calculate_roi(self, content_id):
            """Calculate content ROI based on metrics"""
[/code]

**Learning Service** :
[code] 
    class LearningService:
        def collect_feedback(self, analysis_id, feedback):
            """Collect user feedback on analysis"""
    
        def analyze_patterns(self):
            """Analyze feedback patterns for model improvement"""
    
        def update_model_weights(self):
            """Adjust classification based on learning"""
[/code]

## [](<#_deployment_configuration>)9\. Deployment Configuration

### [](<#_database_models_and_services>)9.1. Database models and services

#### [](<#_databaseinit_py>)9.1.1. `database/_init_.py`

Database initialization and configuration.

**Purpose** : SQLAlchemy database setup and initialization **Key Functions** : \- `init_db(app)`: Initialize database with Flask app \- Database connection management \- Session configuration

#### [](<#_databasemodels_py>)9.1.2. `database/models.py`

SQLAlchemy ORM models for data persistence.

**Purpose** : Data model definitions for all database tables **Key Models** : \- `User`: User account information \- `Feedback`: User feedback on analysis results \- `StyleRule`: Style rule configuration \- `AnalysisSession`: Analysis session tracking

#### [](<#_databasedao_py>)9.1.3. `database/dao.py`

Data Access Objects for database operations.

**Purpose** : Abstraction layer for database operations **Key Classes** : \- `FeedbackDAO`: Feedback CRUD operations \- `StyleRuleDAO`: Rule management operations \- `SessionDAO`: Session management

#### [](<#_databaseservices_py_2>)9.1.4. `database/services.py`

High-level database services and business logic.

**Purpose** : Business logic layer for database operations **Key Functions** : \- `database_service`: Main service instance \- `initialize_default_rules()`: Set up default style rules \- Feedback aggregation and analytics \- Session management

#### [](<#_migrations>)9.1.5. `migrations/`

Database migration scripts for schema updates.

**Purpose** : Version control for database schema **Migration Scripts** : \- `init_database.py`: Initial database setup \- `add_feedback_unique_constraint.py`: Feedback schema update \- `add_phase3_analytics_tables.py`: Analytics tables

## [](<#_validation_and_quality_control>)10\. Validation and quality control

### [](<#_confidence_scoring_system>)10.1. Confidence scoring system

#### [](<#_validationconfidence>)10.1.1. `validation/confidence/`

Advanced confidence scoring for rule detections.

**Purpose** : Calculate confidence scores for detected issues **Key Components** : \- `confidence_calculator.py`: Main confidence calculation engine \- `context_analyzer.py`: Context-aware confidence adjustment \- `domain_classifier.py`: Domain-specific confidence tuning \- `linguistic_anchors.py`: Linguistic pattern detection \- `rule_reliability.py`: Rule reliability tracking

**Confidence Factors** : \- Linguistic anchor presence \- Context appropriateness \- Domain relevance \- Historical reliability \- Multi-validator agreement

### [](<#_multi_pass_validation>)10.2. Multi-Pass Validation

#### [](<#_validationmulti_pass>)10.2.1. `validation/multi_pass/`

Multi-pass validation pipeline for enhanced accuracy.

**Purpose** : Layered validation to reduce false positives **Key Components** : \- `validation_pipeline.py`: Orchestrates validation passes \- `base_validator.py`: Base validator interface \- `context_validator.py`: Context-based validation \- `cross_rule_validator.py`: Cross-rule consistency \- `domain_validator.py`: Domain-specific validation \- `morphological_validator.py`: Morphological analysis

**Validation Passes** : 1\. Syntactic validation 2\. Semantic validation 3\. Context validation 4\. Cross-rule validation 5\. Domain validation

### [](<#_monitoring_and_metrics>)10.3. Monitoring and Metrics

#### [](<#_validationmonitoringmetrics_py>)10.3.1. `validation/monitoring/metrics.py`

Prometheus metrics for system monitoring.

**Purpose** : Production monitoring and observability **Key Metrics** : \- Analysis request counts \- Error detection rates \- Rule performance metrics \- Confidence score distributions \- Processing time histograms \- False positive rates

**Integration** : \- Prometheus exporter \- Health check integration \- Performance dashboards

### [](<#_feedback_system>)10.4. Feedback System

#### [](<#_validationfeedback>)10.4.1. `validation/feedback/`

User feedback processing and reliability tuning.

**Purpose** : Learn from user feedback to improve accuracy **Key Components** : \- `instruction_template_tracker.py`: Track template effectiveness \- `reliability_tuner.py`: Automatic reliability adjustment

**Feedback Loop** : 1\. Collect user feedback on detections 2\. Analyze feedback patterns 3\. Adjust rule reliability scores 4\. Update confidence weights 5\. Monitor improvement metrics

## [](<#_rule_enhancement_system>)11\. Rule Enhancement System

### [](<#_advanced_rule_processing>)11.1. Advanced Rule Processing

#### [](<#_rule_enhancementsenterprise_integration_py>)11.1.1. `rule_enhancements/enterprise_integration.py`

Enterprise-grade rule integration and orchestration.

**Purpose** : Advanced rule coordination and management **Features** : \- Rule dependency resolution \- Priority-based execution \- Performance optimization \- Rule composition

#### [](<#_rule_enhancementsevidence_orchestrator_py>)11.1.2. `rule_enhancements/evidence_orchestrator.py`

Evidence collection and presentation system.

**Purpose** : Gather and present evidence for rule detections **Features** : \- Multi-source evidence collection \- Evidence ranking \- Supporting example extraction \- Explanation generation

#### [](<#_rule_enhancementsnlp_correction_layer_py>)11.1.3. `rule_enhancements/nlp_correction_layer.py`

NLP-based correction suggestions.

**Purpose** : Enhanced suggestion generation using NLP **Features** : \- Context-aware corrections \- Synonym suggestions \- Paraphrase generation \- Grammar-aware replacements

## [](<#_style_analysis_engine>)12\. Style Analysis Engine

### [](<#_core_analyzer_components>)12.1. Core Analyzer Components

#### [](<#_style_analyzerbase_analyzer_py>)12.1.1. `style_analyzer/base_analyzer.py`

Main StyleAnalyzer class that coordinates all analysis components.

**Purpose** : Central orchestration of style analysis **Key Classes** : \- `StyleAnalyzer`: Main analyzer class

**Key Methods** : \- `analyze_with_blocks()`: Primary analysis method with structured parsing \- `analyze()`: Legacy analysis method \- `_determine_analysis_mode()`: Intelligent mode selection \- `_initialize_nlp()`: SpaCy model initialization

**Analysis Flow** :
[code] 
    def analyze_with_blocks(self, content: str) -> AnalysisResult:
        # 1. Determine analysis mode
        mode = self._determine_analysis_mode()
    
        # 2. Parse document structure
        blocks = self.structural_analyzer.parse_document_to_blocks(content)
    
        # 3. Execute analysis mode
        results = self.mode_executor.execute_mode(mode, content, blocks)
    
        # 4. Return structured results
        return create_analysis_result(results)
[/code]

#### [](<#_style_analyzerbase_types_py>)12.1.2. `style_analyzer/base_types.py`

Type definitions and data structures for style analysis.

**Purpose** : Common data structures and type definitions **Key Types** : \- `AnalysisResult`: Main result container \- `AnalysisMode`: Analysis mode enumeration \- `ErrorDict`: Error representation \- `BlockResult`: Block-level analysis results

#### [](<#_style_analyzeranalysis_modes_py>)12.1.3. `style_analyzer/analysis_modes.py`

Analysis mode implementations with intelligent fallbacks.

**Purpose** : Multiple analysis strategies based on available dependencies **Analysis Modes** : \- `SPACY_RULES`: SpaCy + Modular Rules (optimal) \- `RULES_FALLBACK`: Rules + fallbacks (good) \- `SPACY_LEGACY`: SpaCy legacy only (basic) \- `MINIMAL`: Minimal safe mode (fallback)

#### [](<#_style_analyzercore_analyzer_py>)12.1.4. `style_analyzer/core_analyzer.py`

Core analysis logic and rule application.

**Purpose** : Rule execution and error detection **Key Functions** : \- Rule discovery and loading \- Error detection and reporting \- Context-aware analysis

#### [](<#_style_analyzerblock_processors_py>)12.1.5. `style_analyzer/block_processors.py`

Block-level processing for structured documents.

**Purpose** : Process document blocks with context awareness **Key Functions** : \- Block type detection \- Context-aware rule application \- Block-specific error handling

#### [](<#_style_analyzersentence_analyzer_py>)12.1.6. `style_analyzer/sentence_analyzer.py`

Sentence-level analysis and processing.

**Purpose** : Individual sentence analysis and error detection **Key Functions** : \- Sentence segmentation \- Per-sentence rule application \- Sentence-level statistics

#### [](<#_style_analyzerreadability_analyzer_py>)12.1.7. `style_analyzer/readability_analyzer.py`

Readability calculations and metrics.

**Purpose** : Text readability assessment **Metrics Calculated** : \- Flesch Reading Ease \- Flesch-Kincaid Grade Level \- Automated Readability Index \- Coleman-Liau Index \- Gunning Fog Index

#### [](<#_style_analyzerstatistics_calculator_py>)12.1.8. `style_analyzer/statistics_calculator.py`

Statistics computation for analysis results.

**Purpose** : Calculate comprehensive text statistics **Statistics Calculated** : \- Word count, sentence count, paragraph count \- Average sentence length \- Complex word percentage \- Reading time estimation

#### [](<#_style_analyzerstructural_analyzer_py>)12.1.9. `style_analyzer/structural_analyzer.py`

Structural analysis of documents.

**Purpose** : Document structure parsing and analysis **Key Functions** : \- Format detection (Markdown, AsciiDoc) \- Block extraction and parsing \- Structural rule application

#### [](<#_style_analyzersuggestion_generator_py>)12.1.10. `style_analyzer/suggestion_generator.py`

Improvement suggestions based on analysis results.

**Purpose** : Generate actionable improvement suggestions **Key Functions** : \- Rule-based suggestion generation \- Context-aware recommendations \- Prioritized suggestion ordering

#### [](<#_style_analyzererror_converters_py>)12.1.11. `style_analyzer/error_converters.py`

Error format conversion for different output formats.

**Purpose** : Convert internal error formats to external representations **Key Functions** : \- JSON error formatting \- HTML error formatting \- Plain text error formatting

## [](<#_rules_system>)13\. Rules System

### [](<#_rules_registry_and_discovery>)13.1. Rules Registry and Discovery

#### [](<#_rulesinit_py>)13.1.1. `rules/_init_.py`

Central rules registry with automatic discovery system.

**Purpose** : Discovers and loads all rule modules automatically **Key Classes** : \- `RulesRegistry`: Main registry class for rule discovery and management

**Discovery Process** :
[code] 
    def _load_all_rules(self):
        # Recursively walk through rules directory
        for root, dirs, files in os.walk(rules_dir):
            # Process files ending with '_rule.py'
            for filename in files:
                if filename.endswith('_rule.py') and filename != 'base_rule.py':
                    # Import and register rule
                    module = self._import_rule_module_enhanced(import_path)
                    self._register_rule_from_module(module)
[/code]

**Rule Registration** : \- Automatic discovery of rule classes \- Dynamic import with error handling \- Support for nested directory structures (up to 4 levels) \- Graceful fallback when rules fail to load

#### [](<#_rulesbase_rule_py>)13.1.2. `rules/base_rule.py`

Base class for all style guide rules.

**Purpose** : Common interface and functionality for all rules **Key Classes** : \- `BaseRule`: Abstract base class for all rules

**Key Methods** : \- `analyze()`: Main analysis method (abstract) \- `get_rule_type()`: Returns rule type identifier \- `get_description()`: Returns rule description \- `is_enabled()`: Checks if rule is enabled

#### [](<#_rulesrule_mappings_yaml>)13.1.3. `rules/rule_mappings.yaml`

Configuration mapping for rule categories and settings.

**Purpose** : Centralized rule configuration and categorization **Configuration Structure** : \- Rule categories (language_and_grammar, punctuation, structure_and_format) \- Rule priorities and weights \- Rule-specific settings and thresholds

### [](<#_language_and_grammar_rules>)13.2. Language and Grammar Rules

#### [](<#_ruleslanguage_and_grammarbase_language_rule_py>)13.2.1. `rules/language_and_grammar/base_language_rule.py`

Base class for language and grammar rules.

**Purpose** : Common functionality for language-specific rules **Shared Methods** : \- NLP processing utilities \- Context analysis functions \- Language pattern matching

#### [](<#_individual_language_rules>)13.2.2. Individual Language Rules

**`abbreviations_rule.py`** \- **Purpose** : Validates abbreviation usage and formatting \- **Checks** : Proper abbreviation definitions, consistent usage

**`adverbs_only_rule.py`** \- **Purpose** : Detects unnecessary adverb usage \- **Checks** : Excessive adverbs, weak adverb choices

**`anthropomorphism_rule.py`** \- **Purpose** : Identifies anthropomorphic language \- **Checks** : Human characteristics attributed to non-human entities

**`articles_rule.py`** \- **Purpose** : Validates article usage (a, an, the) \- **Checks** : Correct article selection, missing articles

**`capitalization_rule.py`** \- **Purpose** : Enforces capitalization rules \- **Checks** : Title case, sentence case, proper nouns

**`conjunctions_rule.py`** \- **Purpose** : Validates conjunction usage \- **Checks** : Proper conjunction selection, overuse

**`contractions_rule.py`** \- **Purpose** : Manages contraction usage in technical writing \- **Checks** : Formal vs. informal tone consistency

**`inclusive_language_rule.py`** \- **Purpose** : Promotes inclusive language practices \- **Checks** : Gender-neutral language, cultural sensitivity

**`plurals_rule.py`** \- **Purpose** : Validates plural forms \- **Checks** : Correct plural formations, consistency

**`possessives_rule.py`** \- **Purpose** : Enforces possessive form rules \- **Checks** : Apostrophe placement, possessive consistency

**`prepositions_rule.py`** \- **Purpose** : Validates preposition usage \- **Checks** : Correct preposition selection, clarity

**`pronouns_rule.py`** \- **Purpose** : Manages pronoun usage and clarity \- **Checks** : Pronoun-antecedent agreement, clarity

**`spelling_rule.py`** \- **Purpose** : Spell checking and consistency \- **Checks** : Spelling errors, variant spellings

**`terminology_rule.py`** \- **Purpose** : Enforces terminology consistency \- **Checks** : Consistent term usage, approved terminology

**`verbs_rule.py`** \- **Purpose** : Validates verb usage and forms \- **Checks** : Verb tense consistency, active vs. passive voice

### [](<#_punctuation_rules>)13.3. Punctuation Rules

#### [](<#_rulespunctuationbase_punctuation_rule_py>)13.3.1. `rules/punctuation/base_punctuation_rule.py`

Base class for punctuation rules.

**Purpose** : Common functionality for punctuation-specific rules **Shared Methods** : \- Punctuation pattern detection \- Context-aware punctuation analysis \- Formatting validation

#### [](<#_individual_punctuation_rules>)13.3.2. Individual Punctuation Rules

**`punctuation_and_symbols_rule.py`** \- **Purpose** : General punctuation and symbol usage \- **Checks** : Symbol consistency, proper punctuation

**`colons_rule.py`** \- **Purpose** : Colon usage rules \- **Checks** : Proper colon placement, list introductions

**`commas_rule.py`** \- **Purpose** : Comma usage and placement \- **Checks** : Oxford commas, comma splices, clarity

**`dashes_rule.py`** \- **Purpose** : Dash usage (em dashes, en dashes) \- **Checks** : Proper dash types, formatting

**`ellipses_rule.py`** \- **Purpose** : Ellipsis usage and formatting \- **Checks** : Proper ellipsis formation, overuse

**`exclamation_points_rule.py`** \- **Purpose** : Exclamation point usage \- **Checks** : Professional tone, overuse detection

**`hyphens_rule.py`** \- **Purpose** : Hyphen usage and compound words \- **Checks** : Compound word formation, line breaks

**`parentheses_rule.py`** \- **Purpose** : Parentheses usage and nesting \- **Checks** : Proper nesting, clarity, overuse

**`periods_rule.py`** \- **Purpose** : Period usage and sentence endings \- **Checks** : Sentence completion, abbreviations

**`quotation_marks_rule.py`** \- **Purpose** : Quotation mark usage and formatting \- **Checks** : Proper quotation formatting, nested quotes

**`semicolons_rule.py`** \- **Purpose** : Semicolon usage and placement \- **Checks** : Proper semicolon usage, list formatting

**`slashes_rule.py`** \- **Purpose** : Slash usage and alternatives \- **Checks** : Proper slash usage, clarity alternatives

### [](<#_structure_and_format_rules>)13.4. Structure and Format Rules

#### [](<#_rulesstructure_and_formatbase_structure_rule_py>)13.4.1. `rules/structure_and_format/base_structure_rule.py`

Base class for structure and format rules.

**Purpose** : Common functionality for document structure rules **Shared Methods** : \- Document structure analysis \- Formatting pattern detection \- Hierarchy validation

#### [](<#_individual_structure_rules>)13.4.2. Individual Structure Rules

**`admonitions_rule.py`** \- **Purpose** : Admonition block formatting \- **Checks** : Proper admonition structure, consistency

**`headings_rule.py`** \- **Purpose** : Heading structure and hierarchy \- **Checks** : Heading levels, formatting consistency

**`highlighting_rule.py`** \- **Purpose** : Text highlighting and emphasis \- **Checks** : Consistent highlighting, overuse

**`lists_rule.py`** \- **Purpose** : List formatting and structure \- **Checks** : List consistency, proper nesting

**`messages_rule.py`** \- **Purpose** : Message formatting (warnings, notes) \- **Checks** : Message structure, consistency

**`notes_rule.py`** \- **Purpose** : Note formatting and placement \- **Checks** : Note structure, appropriate usage

**`paragraphs_rule.py`** \- **Purpose** : Paragraph structure and flow \- **Checks** : Paragraph length, coherence

**`procedures_rule.py`** \- **Purpose** : Procedure and step formatting \- **Checks** : Step numbering, clarity

### [](<#_specialized_rules>)13.5. Specialized Rules

#### [](<#_rulessecond_person_rule_py>)13.5.1. `rules/second_person_rule.py`

Detects and manages second-person usage.

**Purpose** : Controls second-person pronoun usage in technical writing **Checks** : \- "You" usage in formal contexts \- Consistency with writing style \- Alternative suggestions

#### [](<#_rulessentence_length_rule_py>)13.5.2. `rules/sentence_length_rule.py`

Validates sentence length for readability.

**Purpose** : Ensures sentences are appropriately sized for clarity **Checks** : \- Maximum sentence length (configurable) \- Complex sentence structure \- Readability impact

#### [](<#_rulesambiguity_rule_py>)13.5.3. `rules/ambiguity_rule.py`

Integration point for ambiguity detection system.

**Purpose** : Connects ambiguity detection to rules system **Integration** : Links to `ambiguity/` package for specialized ambiguity detection

## [](<#_ai_rewriting_system>)14\. AI Rewriting System

### [](<#_core_ai_components>)14.1. Core AI Components

#### [](<#_rewritercore_py>)14.1.1. `rewriter/core.py`

AIRewriter base class that orchestrates assembly line rewriting.

**Purpose** : Central coordination using assembly line precision approach **Key Classes** : \- `AIRewriter`: Main rewriter orchestrator

**Key Methods** : \- `rewrite()`: Delegates to AssemblyLineRewriter \- Component initialization with ModelManager integration

**Assembly Line Integration** :
[code] 
    def __init__(self, use_ollama: bool = True, ollama_model: str = "llama3:8b",
                 progress_callback: Optional[Callable] = None):
        self.model_manager = ModelManager()
        self.text_generator = TextGenerator(self.model_manager)
        self.text_processor = TextProcessor()
        self.evaluator = RewriteEvaluator()
    
        # Initialize assembly line (ONLY approach)
        self.assembly_line = AssemblyLineRewriter(
            self.text_generator,
            self.text_processor,
            progress_callback
        )
[/code]

#### [](<#_rewriterdocument_rewriter_py>)14.1.2. `rewriter/document_rewriter.py`

Main DocumentRewriter class for structure-preserving rewrites.

**Purpose** : High-level document rewriting with structure preservation **Key Classes** : \- `DocumentRewriter`: Main entry point for document-level rewrites

**Key Methods** : \- `rewrite_document_with_structure_preservation()`: Structure-aware rewriting

#### [](<#_rewriterassembly_line_rewriter_py>)14.1.3. `rewriter/assembly_line_rewriter.py`

Assembly line precision rewriting system.

**Purpose** : Multi-station single-pass rewriting process **Key Classes** : \- `AssemblyLineRewriter`: Orchestrates station-based processing

**Assembly Line Stations** : \- Station 1: Error triage and categorization \- Station 2: Surgical snippet processing \- Station 3: Quality control and validation \- Station 4: Integration and coherence

**Key Methods** : \- `rewrite_with_assembly_line()`: Main assembly line processing \- Station-specific processing methods \- Shared instance management for performance

#### [](<#_rewritersurgical_snippet_processor_py>)14.1.4. `rewriter/surgical_snippet_processor.py`

Surgical precision snippet processing.

**Purpose** : Fine-grained error correction at snippet level **Key Features** : \- Context-aware snippet extraction \- Targeted error fixing \- Original structure preservation

#### [](<#_rewritermodels_py_now_modelsmodel_manager_py>)14.1.5. `rewriter/models.py` (Now: `models/model_manager.py`)

Model management system (moved to models/ package).

**Purpose** : Unified interface for multiple AI model types **Key Classes** : \- `ModelManager`: Manages model initialization and connectivity (in models/ package) \- `ModelConfig`: Configuration management \- `ModelFactory`: Creates appropriate model providers

**Supported Providers** : \- **Ollama** : Local LLM serving (primary) \- **API Providers** : OpenAI, Anthropic, custom APIs \- **LlamaStack** : Enterprise deployment

**Model Provider Pattern** :
[code] 
    class ModelManager:
        def __init__(self):
            self.provider = ModelFactory.create_provider()
    
        def generate(self, prompt: str, **kwargs) -> str:
            return self.provider.generate(prompt, **kwargs)
[/code]

#### [](<#_rewritergenerators_py>)14.1.6. `rewriter/generators.py`

Text generation handling for various models.

**Purpose** : Actual AI text generation using configured models **Key Classes** : \- `TextGenerator`: Handles text generation across model types

**Generation Methods** : \- `generate_with_ollama()`: Ollama API calls \- `generate_with_hf_model()`: Hugging Face model generation \- `generate_text()`: Unified generation interface

#### [](<#_rewriterprocessors_py>)14.1.7. `rewriter/processors.py`

Text processing and cleanup for generated content.

**Purpose** : Post-processing of AI-generated text **Key Functions** : \- Text cleaning and normalization \- Format preservation \- Quality validation

#### [](<#_rewriterevaluators_py>)14.1.8. `rewriter/evaluators.py`

Rewrite quality evaluation and confidence calculation.

**Purpose** : Assesses quality of AI rewrites and calculates confidence scores **Key Classes** : \- `RewriteEvaluator`: Quality assessment and metrics

**Evaluation Methods** : \- `evaluate_rewrite_quality()`: Comprehensive quality assessment \- `calculate_confidence()`: Confidence score calculation \- `extract_improvements()`: Improvement identification

#### [](<#_rewriterprompts_py>)14.1.9. `rewriter/prompts.py`

Prompt generation with style guide integration.

**Purpose** : Dynamic prompt creation based on detected errors and style guide rules **Key Classes** : \- `PromptGenerator`: Creates context-aware prompts

**Prompt Features** : \- Dynamic instruction loading from YAML configs \- Error-specific prompt customization \- Style guide rule integration \- Model-specific prompt optimization

### [](<#_prompt_configuration_system>)14.2. Prompt Configuration System

#### [](<#_rewriterprompt_configsibm_style>)14.2.1. `rewriter/prompt_configs/ibm_style/`

Style guide specific prompt configurations.

**Purpose** : Modular prompt templates for different style guide rules **Configuration Files** :

**`language_and_grammar.yaml`** \- Language and grammar rule prompts \- Error-specific instructions \- Examples and corrections

**`punctuation.yaml`** \- Punctuation rule prompts \- Formatting instructions \- Style-specific guidelines

**`structure_and_format.yaml`** \- Document structure prompts \- Format preservation instructions \- Layout guidelines

**`voice_and_tone.yaml`** \- Voice and tone prompts \- Style consistency instructions \- Brand voice guidelines

## [](<#_ambiguity_detection_system>)15\. Ambiguity Detection System

### [](<#_core_ambiguity_components>)15.1. Core Ambiguity Components

#### [](<#_ambiguitytypes_py>)15.1.1. `ambiguity/types.py`

Type definitions and data structures for ambiguity detection.

**Purpose** : Core type system for ambiguity detection **Key Types** : \- `AmbiguityType`: Enumeration of ambiguity types \- `AmbiguityCategory`: Categorization system \- `AmbiguitySeverity`: Severity levels \- `AmbiguityContext`: Context information \- `AmbiguityEvidence`: Evidence supporting detection \- `AmbiguityDetection`: Complete detection result

**Ambiguity Types** : \- `MISSING_ACTOR`: Passive voice without clear actors \- `AMBIGUOUS_PRONOUN`: Pronouns with unclear referents \- `UNCLEAR_SUBJECT`: Unclear subject references \- `FABRICATION_RISK`: Risk of adding unverified information \- And others…​

#### [](<#_ambiguitybase_ambiguity_rule_py>)15.1.2. `ambiguity/base_ambiguity_rule.py`

Base ambiguity rule and detector framework.

**Purpose** : Integration with rules system and detector coordination **Key Classes** : \- `BaseAmbiguityRule`: Integration with rules system \- `AmbiguityDetector`: Base class for specific detectors

**Integration Pattern** :
[code] 
    def analyze(self, text, sentences, nlp=None, context=None):
        errors = []
        for detector_type, detector in self.detectors.items():
            if self._is_detector_enabled(detector_type):
                detections = detector.detect(sentence_context, nlp)
                errors.extend([d.to_error_dict() for d in detections])
        return errors
[/code]

#### [](<#_ambiguityambiguity_rule_py>)15.1.3. `ambiguity/ambiguity_rule.py`

Main ambiguity detection rule for integration.

**Purpose** : Primary integration point with the rules system **Provides** : Seamless integration with existing rule framework

### [](<#_ambiguity_detectors>)15.2. Ambiguity Detectors

#### [](<#_ambiguitydetectorsmissing_actor_detector_py>)15.2.1. `ambiguity/detectors/missing_actor_detector.py`

Detects passive voice sentences without clear actors.

**Purpose** : Identifies passive constructions lacking clear performers **Detection Logic** : \- Passive voice pattern recognition \- Actor presence validation \- Context analysis for implicit actors

#### [](<#_ambiguitydetectorspronoun_ambiguity_detector_py>)15.2.2. `ambiguity/detectors/pronoun_ambiguity_detector.py`

Detects pronouns with unclear referents.

**Purpose** : Identifies ambiguous pronoun references **Detection Logic** : \- Pronoun identification \- Referent analysis \- Distance and context evaluation

#### [](<#_ambiguitydetectorsunsupported_claims_detector_py>)15.2.3. `ambiguity/detectors/unsupported_claims_detector.py`

Detects unsupported claims and promises.

**Purpose** : Identifies statements that cannot be substantiated **Detection Logic** : \- Claim pattern recognition \- Evidence requirement analysis \- Certainty level assessment

#### [](<#_ambiguitydetectorsfabrication_risk_detector_py>)15.2.4. `ambiguity/detectors/fabrication_risk_detector.py`

Detects risk of information fabrication.

**Purpose** : Identifies content that might invite fabrication **Detection Logic** : \- Vague instruction detection \- Missing detail identification \- Process gap analysis

### [](<#_ambiguity_configuration>)15.3. Ambiguity Configuration

#### [](<#_ambiguityconfigambiguity_types_yaml>)15.3.1. `ambiguity/config/ambiguity_types.yaml`

Configuration for ambiguity detection types and settings.

**Purpose** : Centralized configuration for ambiguity detection **Configuration Structure** : \- Ambiguity type definitions \- Detection thresholds \- Severity mappings \- Enable/disable flags

## [](<#_document_processing_structural_parsing>)16\. Document Processing & Structural Parsing

### [](<#_core_document_processing>)16.1. Core Document Processing

#### [](<#_structural_parsingextractorsdocument_processor_py>)16.1.1. `structural_parsing/extractors/document_processor.py`

Main document processing and text extraction.

**Purpose** : Unified interface for extracting text from multiple document formats **Supported Formats** : \- **PDF** : PyMuPDF-based extraction \- **DOCX** : python-docx based processing \- **Markdown** : Built-in markdown processing \- **AsciiDoc** : Ruby-based asciidoctor integration \- **Plain Text** : Direct text handling \- **DITA** : XML-based processing

**Key Methods** : \- `extract_text(filepath)`: Main extraction method \- `allowed_file(filename)`: File type validation \- `_extract_pdf_text()`: PDF-specific extraction \- `_extract_docx_text()`: DOCX-specific extraction

#### [](<#_structural_parsingformat_detector_py>)16.1.2. `structural_parsing/format_detector.py`

Document format detection and classification.

**Purpose** : Automatic detection of document formats **Detection Methods** : \- File extension analysis \- Content-based detection \- MIME type checking \- Header pattern recognition

#### [](<#_structural_parsingparser_factory_py>)16.1.3. `structural_parsing/parser_factory.py`

Factory pattern for creating format-specific parsers.

**Purpose** : Creates appropriate parser based on detected format **Parser Creation Pattern** :
[code] 
    def create_parser(content: str, format_hint: str = None):
        detected_format = detect_format(content, format_hint)
    
        if detected_format == DocumentFormat.MARKDOWN:
            return MarkdownParser()
        elif detected_format == DocumentFormat.ASCIIDOC:
            return AsciiDocParser()
        else:
            return PlainTextParser()
[/code]

### [](<#_markdown_processing>)16.2. Markdown Processing

#### [](<#_structural_parsingmarkdownparser_py>)16.2.1. `structural_parsing/markdown/parser.py`

Markdown document parsing and structure extraction.

**Purpose** : Parses Markdown documents into structured blocks **Key Features** : \- CommonMark compatibility \- Block-level structure extraction \- Metadata preservation \- Link and reference handling

**Block Types Supported** : \- Headings (H1-H6) \- Paragraphs \- Lists (ordered, unordered) \- Code blocks \- Blockquotes \- Tables \- Links and images

#### [](<#_structural_parsingmarkdowntypes_py>)16.2.2. `structural_parsing/markdown/types.py`

Type definitions for Markdown structures.

**Purpose** : Data structures for Markdown document representation **Key Types** : \- `MarkdownBlock`: Base block representation \- `HeadingBlock`: Heading structure \- `ParagraphBlock`: Paragraph content \- `ListBlock`: List structure \- `CodeBlock`: Code block representation

### [](<#_asciidoc_processing>)16.3. AsciiDoc Processing

#### [](<#_structural_parsingasciidocparser_py>)16.3.1. `structural_parsing/asciidoc/parser.py`

AsciiDoc document parsing and structure extraction.

**Purpose** : Parses AsciiDoc documents using Ruby-based asciidoctor **Key Features** : \- Full AsciiDoc specification support \- Advanced block type handling \- Attribute processing \- Include file resolution

**Advanced Block Types** : \- Admonition blocks (NOTE, TIP, WARNING) \- Sidebar blocks \- Example blocks \- Source code blocks with syntax highlighting \- Tables with complex formatting

#### [](<#_structural_parsingasciidocruby_client_py>)16.3.2. `structural_parsing/asciidoc/ruby_client.py`

Ruby subprocess client for AsciiDoc processing.

**Purpose** : Manages Ruby subprocess calls for asciidoctor integration **Key Features** : \- Simplified subprocess-based communication \- Temporary file-based data exchange \- Automatic asciidoctor availability checking \- Timeout and error handling

**Key Functions** : \- `get_client()`: Get singleton client instance \- `run()`: Parse AsciiDoc content via Ruby subprocess \- `ping()`: Check asciidoctor availability \- `shutdown_client()`: Clean client shutdown

**Ruby Integration Pattern** :
[code] 
    def run(content: str, filename: str = "") -> Dict[str, Any]:
        # Write content to temporary file
        with tempfile.NamedTemporaryFile(...) as input_file:
            input_file.write(content)
    
        # Execute Ruby script
        cmd = ['ruby', self.ruby_script_path, input_path, output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
    
        # Read result from output file
        return json.load(output_file)
[/code]

#### [](<#_structural_parsingasciidoctypes_py>)16.3.3. `structural_parsing/asciidoc/types.py`

Type definitions for AsciiDoc structures.

**Purpose** : Data structures for AsciiDoc document representation **Key Types** : \- `AsciiDocBlock`: Base AsciiDoc block \- `AdmonitionBlock`: Admonition representation \- `SidebarBlock`: Sidebar content \- `ExampleBlock`: Example block structure

## [](<#_frontend_components>)17\. Frontend Components

### [](<#_html_templates>)17.1. HTML Templates

#### [](<#_uitemplatesbase_html>)17.1.1. `ui/templates/base.html`

Base template providing common layout and functionality.

**Purpose** : Common layout structure for all pages **Features** : \- Responsive Bootstrap-based design framework \- Common CSS and JavaScript includes \- Navigation structure and branding \- Error handling integration \- WebSocket connection management

#### [](<#_uitemplatesindex_html>)17.1.2. `ui/templates/index.html`

Main application interface for the Content Editorial Assistant.

**Purpose** : Primary user interface for the Content Editorial Assistant application **Key Sections** : \- File upload interface \- Text input area \- Analysis results display \- AI rewrite interface \- Progress tracking display

**Interactive Elements** : \- Drag-and-drop file upload \- Real-time text analysis \- WebSocket progress updates \- Two-pass AI rewriting interface

#### [](<#_uitemplateserror_html>)17.1.3. `ui/templates/error.html`

Error page template for user-friendly error display.

**Purpose** : Displays errors in a user-friendly format **Error Types Handled** : \- 404 Page Not Found \- 500 Internal Server Error \- File upload errors \- Analysis errors

### [](<#_static_assets>)17.2. Static Assets

#### [](<#_uistaticcssstyles_css>)17.2.1. `ui/static/css/styles.css`

Main stylesheet for the application.

**Purpose** : Comprehensive styling for the entire application **Style Categories** : \- Layout and responsive design \- Typography and readability \- Interactive element styling \- Error and success state styling \- Progress indicator styling \- Analysis result formatting

#### [](<#_uistaticjscore_js>)17.2.2. `ui/static/js/core.js`

Core JavaScript functionality.

**Purpose** : Main application logic and coordination **Key Functions** : \- Application initialization \- Event coordination \- State management \- Error handling \- User interface updates

#### [](<#_uistaticjsfile_handler_js>)17.2.3. `ui/static/js/file-handler.js`

File upload and handling functionality.

**Purpose** : Manages file upload operations **Features** : \- Drag-and-drop support \- File type validation \- Progress tracking \- Error handling \- Multiple file format support

**File Handling Flow** :
[code] 
    class FileHandler {
        handleFileUpload(file) {
            // Validate file type and size
            if (!this.validateFile(file)) return;
    
            // Show progress
            this.showProgress();
    
            // Upload file
            this.uploadFile(file)
                .then(response => this.handleSuccess(response))
                .catch(error => this.handleError(error));
        }
    }
[/code]

#### [](<#_uistaticjssocket_handler_js>)17.2.4. `ui/static/js/socket-handler.js`

WebSocket communication management.

**Purpose** : Real-time communication with the server **Key Features** : \- Connection management \- Progress update handling \- Error state management \- Session management

**WebSocket Events Handled** : \- `connect`: Connection establishment \- `progress`: Progress updates \- `completion`: Task completion \- `error`: Error notifications

#### [](<#_uistaticjsanalysis_display_js>)17.2.5. `ui/static/js/analysis-display.js`

Analysis results display and interaction.

**Purpose** : Displays and manages analysis results **Display Features** : \- Error highlighting in text \- Rule violation details \- Improvement suggestions \- Statistics visualization \- Interactive error navigation

#### [](<#_uistaticjsutility_functions_js>)17.2.6. `ui/static/js/utility-functions.js`

Common utility functions and helpers.

**Purpose** : Shared utility functions across the application **Utility Categories** : \- DOM manipulation helpers \- Data formatting functions \- Validation utilities \- Animation helpers \- Browser compatibility functions

## [](<#_data_flow_and_integration>)18\. Data Flow and Integration

### [](<#_complete_request_processing_flow>)18.1. Complete Request Processing Flow
[code] 
    graph TD
        A[User Input/File Upload] --> B[Flask Route Handler]
        B --> C{Request Type}
    
        C -->|Upload| D[Document Processor]
        C -->|Analyze| E[Style Analyzer]
        C -->|Rewrite| F[AI Rewriter]
    
        D --> G[Format Detection]
        G --> H[Structural Parser]
        H --> I[Text Extraction]
        I --> J[Return to Client]
    
        E --> K[Analysis Mode Selection]
        K --> L[Rules Engine]
        L --> M[Block Processing]
        M --> N[Error Detection]
        N --> O[Statistics Calculation]
        O --> P[Suggestion Generation]
        P --> Q[Return Analysis Results]
    
        F --> R[Model Manager]
        R --> S[Prompt Generator]
        S --> T[Text Generator]
        T --> U[Evaluator]
        U --> V[Return Rewrite Results]
    
        J --> W[WebSocket Progress]
        Q --> W
        V --> W
        W --> X[Frontend Update]
[/code]

### [](<#_inter_component_communication>)18.2. Inter-Component Communication

**Service Layer Integration** :
[code] 
    # Application factory initializes all services
    services = {
        'document_processor': DocumentProcessor(),
        'style_analyzer': StyleAnalyzer(),
        'ai_rewriter': AIRewriter()
    }
    
    # Route handlers use services
    @app.route('/analyze', methods=['POST'])
    def analyze_content():
        result = services['style_analyzer'].analyze_with_blocks(content)
        return jsonify(result)
[/code]

**Component Dependencies** : \- **Style Analyzer** depends on: \- Rules system for error detection \- Structural parser for document analysis \- SpaCy for NLP processing \- Statistics calculator for metrics

  * **AI Rewriter** depends on:

  * Model manager for AI integration

  * Prompt generator for instruction creation

  * Evaluator for quality assessment

  * Style analyzer results for context

  * **Document Processor** depends on:

  * Format detector for type identification

  * Parser factory for appropriate parsers

  * External libraries (PyMuPDF, python-docx)

### [](<#_configuration_and_environment_management>)18.3. Configuration and Environment Management

**Environment Variable Flow** :
[code] 
    .env file → Config class → Service initialization → Runtime behavior
[/code]

**Configuration Precedence** : 1\. Environment variables 2\. Configuration file defaults 3\. Hardcoded fallbacks

**Key Configuration Points** : \- AI model selection (Ollama vs. HuggingFace) \- Analysis mode preference \- Rule enable/disable flags \- File upload limits \- Logging levels

## [](<#_performance_and_optimization>)19\. Performance and Optimization

### [](<#_analysis_performance>)19.1. Analysis Performance

**Intelligent Mode Selection** : The system automatically selects the optimal analysis mode based on available dependencies:
[code] 
    def _determine_analysis_mode(self):
        if SPACY_AVAILABLE and RULES_AVAILABLE:
            return AnalysisMode.SPACY_RULES  # Optimal performance
        elif RULES_AVAILABLE:
            return AnalysisMode.RULES_FALLBACK  # Good performance
        elif SPACY_AVAILABLE:
            return AnalysisMode.SPACY_LEGACY  # Basic performance
        else:
            return AnalysisMode.MINIMAL  # Minimal performance
[/code]

**Block-Level Processing** : \- Parallel processing of document blocks \- Context-aware rule application \- Efficient error aggregation

**Caching Strategies** : \- SpaCy model caching \- Rule compilation caching \- Parser result caching

### [](<#_ai_performance_optimization>)19.2. AI Performance Optimization

**Model Management** : \- Lazy model loading \- Connection pooling for API models \- Efficient prompt generation \- Response caching for similar inputs

**Two-Pass Optimization** : \- Selective second pass execution \- Progressive enhancement approach \- Quality threshold-based processing

### [](<#_memory_management>)19.3. Memory Management

**Large Document Handling** : \- Streaming document processing \- Block-wise analysis to prevent memory overflow \- Efficient text storage and retrieval

**Resource Cleanup** : \- Automatic cleanup handlers for external processes \- Memory-efficient data structures \- Proper resource disposal

### [](<#_scalability_considerations>)19.4. Scalability Considerations

**Horizontal Scaling** : \- Stateless application design \- External service integration (Ruby server) \- Load balancer compatible

**Vertical Scaling** : \- Multi-threaded processing support \- Efficient algorithm implementations \- Resource usage optimization

## [](<#_error_handling_and_logging>)20\. Error Handling and Logging

### [](<#_comprehensive_error_handling>)20.1. Comprehensive Error Handling

**Error Hierarchy** :
[code] 
    Application Errors
    ├── Configuration Errors
    ├── Service Initialization Errors
    ├── Processing Errors
    │   ├── Document Processing Errors
    │   ├── Analysis Errors
    │   └── AI Generation Errors
    ├── External Service Errors
    │   ├── Ollama Connection Errors
    │   ├── SpaCy Model Errors
    │   └── Ruby Server Errors
    └── User Input Errors
[/code]

**Fallback Strategy** : Each component implements graceful degradation: \- Missing dependencies → Fallback implementations \- Service failures → Reduced functionality \- External service unavailable → Local alternatives

### [](<#_logging_system>)20.2. Logging System

**Log Categories** : \- **INFO** : Normal operation status \- **WARNING** : Fallback usage, missing dependencies \- **ERROR** : Service failures, processing errors \- **DEBUG** : Detailed processing information

**Log Destinations** : \- Console output for development \- File logging for production \- Structured logging for monitoring

## [](<#_deployment_configuration_2>)21\. Deployment Configuration

### [](<#_docker_deployment>)21.1. Docker Deployment

#### [](<#_dockerfile>)21.1.1. `Dockerfile`

Production-ready Docker image definition at project root.

**Purpose** : Creates containerized deployment for production environments **Key Features** : \- Python 3.12-slim base image \- Ruby and asciidoctor gem installation \- ML model preloading (SpaCy, sentence-transformers) \- NLTK data pre-download \- Non-root user execution (appuser) \- Health check configuration \- Cache optimization for offline operation

**Build Configuration** : \- Multi-layer caching for fast rebuilds \- Precomputed embeddings at build time \- Offline-first model loading \- Gunicorn production server

#### [](<#_gunicorn_conf_py>)21.1.2. `gunicorn.conf.py`

Gunicorn WSGI server configuration for production.

**Purpose** : Production web server configuration **Key Settings** : \- Worker class: gevent (async support) \- Timeout: 300 seconds (5 minutes for long analyses) \- Preload app: true (share SpaCy model across workers) \- Dynamic worker count based on CPU \- Graceful shutdown handling

**Configuration** :
[code] 
    workers = int(os.getenv('GUNICORN_WORKERS', default_workers))
    worker_class = 'gevent'
    timeout = 300  # 5-minute timeout for long operations
    preload_app = True  # Share heavy resources
[/code]

### [](<#_openshift_deployment>)21.2. OpenShift Deployment

#### [](<#_openshift_deployment_patch_yaml>)21.2.1. `openshift-deployment-patch.yaml`

OpenShift deployment patch for persistence.

**Purpose** : Configure persistent storage for database and feedback **Key Configuration** : \- PVC mounting for /app/instance (SQLite database) \- Feedback data persistence \- Environment variable configuration \- Volume mount specifications

#### [](<#_openshift_route_yaml>)21.2.2. `openshift-route.yaml`

OpenShift route configuration for external access.

**Purpose** : Configure ingress routing for the application **Features** : \- TLS termination \- Custom domain support \- Health check integration

### [](<#_deployment_scripts>)21.3. Deployment Scripts

#### [](<#_deploy_sh>)21.3.1. `deploy.sh`

Automated deployment script for various platforms.

**Purpose** : Automates deployment process **Platforms Supported** : \- Local development \- Docker containers \- OpenShift/Kubernetes \- Cloud platforms

#### [](<#_main_sh>)21.3.2. `main.sh`

Container startup script for production.

**Purpose** : Container entry point with initialization **Responsibilities** : \- Environment validation \- Database migration \- Service health checks \- Gunicorn server startup

## [](<#_documentation_system>)22\. Documentation System

### [](<#_documentation_files>)22.1. Documentation Files

**Architecture Documentation** : \- `docs/architecture.adoc`: This comprehensive architecture document \- `docs/how-to-add-new-rule.adoc`: Guide for extending rules \- `docs/how-to-add-new-ambiguity-detector.adoc`: Ambiguity detection guide \- `docs/how-to-add-new-model.adoc`: AI model integration guide

**Implementation Guides** : \- `MARKDOWN_IMPLEMENTATION_GUIDE.md`: Markdown processing details \- `ASCIIDOC_IMPLEMENTATION_GUIDE.md`: AsciiDoc processing details \- `README.md`: Project overview and setup instructions

## [](<#_technology_stack_summary>)23\. Technology Stack Summary

### [](<#_core_technologies>)23.1. Core Technologies

Component | Technology | Version | Purpose  
---|---|---|---  
Web Framework | Flask | 3.0+ | HTTP server and routing  
Real-time Communication | Flask-SocketIO | 5.3+ | WebSocket support  
NLP Processing | SpaCy | 3.7+ | Natural language processing  
AI Models | Ollama | 0.1+ | Local LLM serving  
AI Fallback | Transformers | 4.36+ | Hugging Face models  
Document Processing | PyMuPDF | 1.23+ | PDF text extraction  
Document Processing | python-docx | 1.1+ | DOCX processing  
AsciiDoc Processing | Ruby + Asciidoctor | Latest | AsciiDoc parsing  
Configuration | YAML + python-dotenv | Latest | Settings management  
Frontend | Vanilla JavaScript | ES6+ | User interface  
Styling | CSS3 | Latest | User interface styling  
Container | Docker | Latest | Deployment packaging  
  
### [](<#_external_dependencies>)23.2. External Dependencies

**Required for Full Functionality** : \- **Ollama** : Local AI model serving \- **Ruby** : AsciiDoc processing \- **SpaCy Model** : `en_core_web_sm` for NLP

**Optional Dependencies** : \- **Redis** : Session storage and caching \- **OpenAI API** : Alternative AI model \- **Various Python packages** : See requirements.txt

## [](<#_conclusion>)24\. Conclusion

Content Editorial Assistant represents a comprehensive, modular architecture designed for:

  * **Extensibility** : Easy addition of new rules, detectors, and models

  * **Reliability** : Graceful fallbacks and error handling

  * **Performance** : Optimized processing and resource management

  * **Maintainability** : Clear separation of concerns and modular design

  * **Scalability** : Horizontal and vertical scaling capabilities

The architecture supports multiple analysis modes, various AI backends, and comprehensive document format support while maintaining user-friendly operation and developer-friendly extension points.

Last updated 2025-12-20 04:37:37 +0530 
