
The process begins when you paste the raw AsciiDoc content from the Canvas into the application.

* **Input:**  
  \= Document Title for Style Guide AI  
  :author: Jane Doe

  . Installation Procedure  
  . Download the installer package...

#### Step 2: Structural Parsing (The New, Correct First Step)

Instead of treating the input as plain text, the application first sends the raw AsciiDoc to a dedicated **AsciidoctorParser**. This parser's only job is to identify the document's structure.

* **Action:** The AsciidoctorParser processes the text. It does **not** look for grammar errors. It only identifies headings, lists, admonitions, paragraphs, etc.  
* **Output:** The parser produces a structured list of "blocks." Each block is a dictionary containing the raw text and its structural metadata.  
* **Example Structured Output:**  
  \[  
    { "type": "heading", "level": 1, "content": "Document Title for Style Guide AI" },  
    { "type": "attribute", "content": "author: Jane Doe" },  
    { "type": "paragraph", "content": "This is the first paragraph..." },  
    { "type": "heading", "level": 2, "content": "Section 1: Initial Setup" },  
    { "type": "list\_title", "content": "Installation Procedure" },  
    { "type": "list\_item\_ordered", "content": "Download the installer package..." }  
  \]

#### Step 3: Context-Aware Analysis

Your main application logic now iterates through this structured list of blocks. For each block, it sends the content to your SpaCy analyzer rules, but now it also provides the structural **context** (the type of the block).

* **Action:** The application intelligently applies the correct rules based on the block type.  
* **Example Logic:**  
  * For the block {'type': 'heading', ...}, it runs only the headings\_rule.py.  
  * For the block {'type': 'attribute', ...}, it **skips all analysis**. This is why the :author: Jane Doe line will no longer generate false colon errors.  
  * For the blocks {'type': 'list\_item\_ordered', ...}, it correctly runs the procedures\_rule.py and lists\_rule.py.  
  * For the block {'type': 'list\_title', ...}, it runs the headings\_rule.py but knows not to flag the leading period.

#### Step 4: Highly Accurate Error Detection

Because the rules now know the context of the text they are analyzing, they are far more accurate.

* **Result:** The procedures\_rule.py no longer has to guess if a sentence is a step; it *knows* it is. The colons\_rule.py will not run on the document attributes. This eliminates the false positives you were seeing.  
* **Output:** A clean and reliable list of genuine errors is generated.

#### Step 5 & 6: Prompt Generation and AI Rewrite

The rest of the workflow proceeds as before, but it is now working with high-quality, accurate data.

* The accurate list of errors is passed to your PromptGenerator.  
* The PromptGenerator builds a precise, targeted prompt using your .yaml configuration files.  
* The AI Rewriter receives these correct instructions and generates the improved text without introducing new errors caused by misunderstanding the document's structure.