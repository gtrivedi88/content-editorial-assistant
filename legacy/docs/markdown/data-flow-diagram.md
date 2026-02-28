# Data flow diagram

Table of Contents

  * [1\. Overview](<#_overview>)
  * [2\. High-level data flow diagram](<#_high_level_data_flow_diagram>)
  * [3\. User input data flow](<#_user_input_data_flow>)
    * [3.1. Input types and processing](<#_input_types_and_processing>)
    * [3.2. User input processing flow](<#_user_input_processing_flow>)
  * [4\. Content standards ingestion](<#_content_standards_ingestion>)
    * [4.1. IBM Style Guide integration](<#_ibm_style_guide_integration>)
    * [4.2. Red Hat modular documentation standards](<#_red_hat_modular_documentation_standards>)
    * [4.3. Standards configuration files](<#_standards_configuration_files>)
  * [5\. Red Hat systems integration](<#_red_hat_systems_integration>)
    * [5.1. Integration architecture](<#_integration_architecture>)
    * [5.2. System integration details](<#_system_integration_details>)
  * [6\. Data security and privacy](<#_data_security_and_privacy>)
    * [6.1. Data flow security controls](<#_data_flow_security_controls>)
    * [6.2. Data handling policies](<#_data_handling_policies>)
  * [7\. AI model data flow](<#_ai_model_data_flow>)
    * [7.1. AI processing pipeline](<#_ai_processing_pipeline>)
    * [7.2. AI data boundaries](<#_ai_data_boundaries>)
  * [8\. Appendix: Data flow summary table](<#_appendix_data_flow_summary_table>)
  * [9\. Document history](<#_document_history>)

## 1\. Overview

This document provides a comprehensive data flow diagram showing:

  * User inputs and how they flow through the system

  * Integrations between Red Hat systems and the Content Editorial Assistant

  * How Red Hat and IBM content standards are ingested by the tool

**Last updated** : November 2025

**Document owner** : Content Editorial Assistant team

* * *

## 2\. High-level data flow diagram

The following diagram illustrates the complete data flow through the Content Editorial Assistant system.
[code] 
    flowchart TB
        subgraph UserInputs["USER INPUTS"]
            UI_TEXT[Direct text entry]
            UI_FILE[File upload<br/>PDF, DOCX, MD, ADOC, DITA, TXT]
            UI_PASTE[Clipboard paste]
        end
    
        subgraph ContentStandards["CONTENT STANDARDS INGESTION"]
            IBM_STYLE[IBM Style Guide rules<br/>45+ style rules]
            RH_MOD[Red Hat modular<br/>documentation standards]
            YAML_CONFIG[YAML configuration<br/>files]
        end
    
        subgraph CEA["CONTENT EDITORIAL ASSISTANT"]
            subgraph InputProcessing["Input processing layer"]
                DOC_PROC[Document processor]
                FORMAT_DET[Format detector]
                TEXT_EXTRACT[Text extractor]
            end
    
            subgraph AnalysisEngine["Analysis engine"]
                STYLE_ANALYZER[Style analyzer]
                RULES_ENGINE[Rules engine]
                AMBIGUITY_DET[Ambiguity detector]
                READABILITY[Readability calculator]
            end
    
            subgraph AIProcessing["AI processing layer"]
                MODEL_MGR[Model manager]
                PROMPT_GEN[Prompt generator]
                REWRITER[Document rewriter]
            end
    
            subgraph OutputGeneration["Output generation"]
                RESULTS[Analysis results]
                SUGGESTIONS[Improvement suggestions]
                REPORTS[PDF reports]
            end
        end
    
        subgraph AIProviders["AI MODEL PROVIDERS"]
            OLLAMA[Ollama<br/>Local LLM]
            LLAMASTACK[LlamaStack<br/>Enterprise]
        end
    
        subgraph RedHatSystems["RED HAT SYSTEMS"]
            OPENSHIFT[OpenShift<br/>Container Platform]
            GITLAB[GitLab<br/>Source control]
            SSO[Red Hat SSO<br/>Authentication]
        end
    
        subgraph DataStorage["DATA STORAGE"]
            SESSION[Session data<br/>In-memory only]
            FEEDBACK[Feedback storage<br/>SQLite]
            LOGS[Application logs]
        end
    
        %% User input flow
        UI_TEXT --> DOC_PROC
        UI_FILE --> DOC_PROC
        UI_PASTE --> DOC_PROC
    
        %% Content standards flow
        IBM_STYLE --> RULES_ENGINE
        RH_MOD --> RULES_ENGINE
        YAML_CONFIG --> RULES_ENGINE
        YAML_CONFIG --> AMBIGUITY_DET
    
        %% Internal processing flow
        DOC_PROC --> FORMAT_DET
        FORMAT_DET --> TEXT_EXTRACT
        TEXT_EXTRACT --> STYLE_ANALYZER
    
        STYLE_ANALYZER --> RULES_ENGINE
        STYLE_ANALYZER --> AMBIGUITY_DET
        STYLE_ANALYZER --> READABILITY
    
        RULES_ENGINE --> RESULTS
        AMBIGUITY_DET --> RESULTS
        READABILITY --> RESULTS
    
        RESULTS --> SUGGESTIONS
        RESULTS --> REPORTS
    
        %% AI processing flow
        STYLE_ANALYZER --> MODEL_MGR
        MODEL_MGR --> PROMPT_GEN
        PROMPT_GEN --> REWRITER
        REWRITER --> OLLAMA
        REWRITER --> LLAMASTACK
        OLLAMA --> REWRITER
        LLAMASTACK --> REWRITER
        REWRITER --> RESULTS
    
        %% Red Hat systems integration
        OPENSHIFT -.-> CEA
        GITLAB -.-> CEA
        SSO -.-> CEA
    
        %% Data storage flow
        CEA --> SESSION
        CEA --> FEEDBACK
        CEA --> LOGS
    
        %% Output to user
        RESULTS --> UI_TEXT
        SUGGESTIONS --> UI_TEXT
        REPORTS --> UI_FILE
[/code]

* * *

## 3\. User input data flow

### 3.1. Input types and processing

Input type | Format | Processing method | Data retention  
---|---|---|---  
**Direct text entry** | Plain text via web form | Immediate in-memory processing | Session only - deleted on close  
**File upload** | PDF, DOCX, MD, ADOC, DITA, TXT | Format detection + extraction | Temporary - deleted after processing  
**Clipboard paste** | Plain text | Direct text processing | Session only - deleted on close  
  
### 3.2. User input processing flow
[code] 
    sequenceDiagram
        participant User
        participant Browser
        participant Flask as Flask server
        participant DocProc as Document processor
        participant Analyzer as Style analyzer
        participant AI as AI rewriter
    
        User->>Browser: Enter text / Upload file
        Browser->>Flask: POST /upload or /analyze
        Flask->>DocProc: Process input
    
        alt File upload
            DocProc->>DocProc: Detect format (PDF/DOCX/etc.)
            DocProc->>DocProc: Extract text content
        end
    
        DocProc->>Flask: Return extracted text
        Flask->>Analyzer: Analyze content
        Analyzer->>Analyzer: Apply style rules
        Analyzer->>Analyzer: Calculate readability
        Analyzer->>Analyzer: Detect ambiguities
        Analyzer->>Flask: Return analysis results
        Flask->>Browser: Display results (WebSocket)
        Browser->>User: Show analysis + suggestions
    
        opt AI rewrite requested
            User->>Browser: Click Rewrite
            Browser->>Flask: POST /rewrite
            Flask->>AI: Generate improvements
            AI->>Flask: Return rewritten content
            Flask->>Browser: Display rewrite
            Browser->>User: Show AI suggestions
        end
[/code]

* * *

## 4\. Content standards ingestion

### 4.1. IBM Style Guide integration

The tool ingests IBM Style Guide rules through a modular rule system:
[code] 
    flowchart LR
        subgraph IBMStyleGuide["IBM STYLE GUIDE"]
            LG[Language and grammar]
            PUNCT[Punctuation]
            STRUCT[Structure and format]
            TECH[Technical elements]
            WORD[Word usage]
        end
    
        subgraph RuleSystem["RULE SYSTEM"]
            subgraph LangRules["Language rules"]
                ABB[Abbreviations]
                CAPS[Capitalization]
                INCL[Inclusive language]
                TERM[Terminology]
            end
    
            subgraph PunctRules["Punctuation rules"]
                COMMA[Commas]
                COLON[Colons]
                DASH[Dashes]
                QUOTE[Quotation marks]
            end
    
            subgraph StructRules["Structure rules"]
                HEAD[Headings]
                LIST[Lists]
                PARA[Paragraphs]
                PROC[Procedures]
            end
        end
    
        LG --> LangRules
        PUNCT --> PunctRules
        STRUCT --> StructRules
    
        subgraph Config["CONFIGURATION"]
            YAML1[rule_mappings.yaml]
            YAML2[ambiguity_types.yaml]
            YAML3[confidence_weights.yaml]
        end
    
        Config --> RuleSystem
[/code]

### 4.2. Red Hat modular documentation standards

Standard | Implementation | Configuration file  
---|---|---  
**Concept modules** | Template compliance checking | `modular_compliance/config/`  
**Procedure modules** | Step validation, prerequisites | `modular_compliance/config/`  
**Reference modules** | Structure validation | `modular_compliance/config/`  
**Assembly modules** | Cross-reference checking | `modular_compliance/config/`  
  
### 4.3. Standards configuration files
[code] 
    rules/
      rule_mappings.yaml           # Rule category mappings
    
      language_and_grammar/
        config/
          terminology.yaml         # Approved terminology
          inclusive_language.yaml  # Inclusive language patterns
    
      punctuation/
        config/
          punctuation_rules.yaml   # Punctuation patterns
    
      modular_compliance/
        config/
          concept_template.yaml    # Concept module standards
          procedure_template.yaml  # Procedure module standards
          reference_template.yaml  # Reference module standards
    
      ambiguity/
        config/
          ambiguity_types.yaml     # Ambiguity detection patterns
[/code]

* * *

## 5\. Red Hat systems integration

### 5.1. Integration architecture
[code] 
    flowchart TB
        subgraph RedHatInfra["RED HAT INFRASTRUCTURE"]
            subgraph OpenShift["OpenShift Container Platform"]
                POD[CEA pod]
                SVC[Service]
                ROUTE[Route/Ingress]
                PVC[Persistent volume]
            end
    
            subgraph GitLab["GitLab"]
                REPO[Source repository]
                CI[CI/CD pipeline]
                REG[Container registry]
            end
    
            subgraph Monitoring["Monitoring"]
                PROM[Prometheus]
                ALERT[Alertmanager]
            end
        end
    
        subgraph CEA["Content Editorial Assistant"]
            APP[Flask application]
            DB[(SQLite database)]
            LOGS[Application logs]
        end
    
        subgraph AIServices["AI SERVICES"]
            OLLAMA[Ollama server]
            LLAMA[LlamaStack]
        end
    
        %% OpenShift integration
        ROUTE --> SVC
        SVC --> POD
        POD --> APP
        PVC --> DB
    
        %% GitLab integration
        REPO --> CI
        CI --> REG
        REG --> POD
    
        %% Monitoring integration
        APP --> PROM
        PROM --> ALERT
    
        %% AI integration
        APP --> OLLAMA
        APP --> LLAMA
[/code]

### 5.2. System integration details

System | Integration type | Purpose | Data exchanged  
---|---|---|---  
**OpenShift** | Container orchestration | Application hosting and scaling | Container images, configs  
**GitLab** | CI/CD pipeline | Source control, automated deployment | Source code, build artifacts  
**Prometheus** | Metrics collection | Performance monitoring | Application metrics  
**Ollama/LlamaStack** | API integration | AI model inference | Text prompts, responses  
  
* * *

## 6\. Data security and privacy

### 6.1. Data flow security controls
[code] 
    flowchart TB
        subgraph Security["SECURITY CONTROLS"]
            TLS[TLS encryption<br/>In transit]
            ISOLATION[Session isolation]
            CLEANUP[Automatic cleanup]
            NORETAIN[No data retention]
        end
    
        subgraph UserData["USER DATA"]
            INPUT[User input]
            UPLOAD[Uploaded files]
            RESULTS[Analysis results]
        end
    
        subgraph Processing["PROCESSING"]
            INMEM[In-memory processing]
            TEMP[Temporary storage]
            SESSION[Session-bound]
        end
    
        INPUT --> TLS
        UPLOAD --> TLS
        TLS --> INMEM
        INMEM --> SESSION
        SESSION --> ISOLATION
        TEMP --> CLEANUP
        CLEANUP --> NORETAIN
        RESULTS --> SESSION
[/code]

### 6.2. Data handling policies

Data type | Handling | Retention  
---|---|---  
**User-entered text** | In-memory processing only | Deleted when session ends  
**Uploaded files** | Temporary extraction, then deleted | No retention  
**Analysis results** | Session-bound display | Deleted when session ends  
**AI-generated content** | Transient processing | No retention  
**Feedback data** | Anonymized storage | Retained for improvement  
  
* * *

## 7\. AI model data flow

### 7.1. AI processing pipeline
[code] 
    sequenceDiagram
        participant Analyzer as Style analyzer
        participant ModelMgr as Model manager
        participant PromptGen as Prompt generator
        participant Provider as AI provider<br/>(Ollama/LlamaStack)
        participant Evaluator as Quality evaluator
    
        Analyzer->>ModelMgr: Request rewrite
        ModelMgr->>ModelMgr: Select provider
        ModelMgr->>PromptGen: Generate prompt
    
        Note over PromptGen: Include:<br/>- Original text<br/>- Detected errors<br/>- Style guidelines<br/>- Rewrite instructions
    
        PromptGen->>Provider: Send prompt
        Provider->>Provider: Generate response
        Provider->>ModelMgr: Return generated text
        ModelMgr->>Evaluator: Evaluate quality
        Evaluator->>Evaluator: Check improvements
        Evaluator->>Analyzer: Return results + confidence
[/code]

### 7.2. AI data boundaries

**Data sent to AI models:**

  * Original text content (user-provided)

  * Detected style issues

  * Rewrite instructions (from prompts)

**Data NOT sent to AI models:**

  * User identifiers

  * Session information

  * System credentials

  * Historical data

* * *

## 8\. Appendix: Data flow summary table

Source | Destination | Data type | Purpose | Retention  
---|---|---|---|---  
User browser | Flask server | Text/Files | Content analysis | Session only  
Flask server | Style analyzer | Extracted text | Rule application | Processing only  
Style analyzer | Rules engine | Text segments | Error detection | Processing only  
Rules engine | Configuration | Rule parameters | Rule execution | Persistent (config)  
Flask server | AI provider | Text + prompts | Content rewriting | None  
AI provider | Flask server | Generated text | Display to user | Session only  
Flask server | User browser | Analysis results | User feedback | Session only  
User browser | Feedback storage | Anonymized ratings | Tool improvement | Persistent (anonymized)  
  
* * *

## 9\. Document history

Version | Date | Changes  
---|---|---  
1.0 | November 2025 | Initial data flow diagram documentation  
  
Last updated 2025-11-25 17:45:26 +0530 
