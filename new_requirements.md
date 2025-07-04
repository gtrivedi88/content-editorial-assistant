### **Full Application Workflow**

This outlines the complete, step-by-step process your application now follows, from initial user input to the final, AI-generated rewrite. The key enhancement is the new **Structural Parsing** step, which makes the entire system context-aware.

#### Step 1: User Input

The process begins when you paste raw, structured text (like Markdown) into the application.

* **Input:**  
  \#\#\# Our New Features.

  To update the software, you should complete these steps:  
  1\. The new installer is downloaded by the user.  
  2\. Clicking the "Update Now" button to begin.

#### Step 2: Structural Parsing (The New Engine)

Instead of immediately analyzing the text, the application first sends the raw Markdown to the **MarkdownParser**. The parser's job is to understand the document's structure.

* **Action:** The MarkdownParser processes the text.  
* **Output:** It produces a structured list of "blocks." Each block is a dictionary containing the raw text and its structural metadata.  
* **Example Structured Output:**  
  \[  
    {  
      "type": "heading",  
      "level": 3,  
      "content": "Our New Features."  
    },  
    {  
      "type": "paragraph",  
      "content": "To update the software, you should complete these steps:"  
    },  
    {  
      "type": "list\_item\_ordered",  
      "content": "The new installer is downloaded by the user."  
    },  
    {  
      "type": "list\_item\_ordered",  
      "content": "Clicking the 'Update Now' button to begin."  
    }  
  \]

#### Step 3: Context-Aware Analysis (The Smart Part)

Your main application logic now iterates through this structured list of blocks. For each block, it sends the content to your SpaCy analyzer rules, but now it also provides the structural **context** (the type of the block).

* **Action:** The application loops through the blocks.  
* **Example Logic:**  
  * For the block {'type': 'heading', ...}, it runs only the headings\_rule.py.  
  * For the blocks {'type': 'list\_item\_ordered', ...}, it runs the procedures\_rule.py and lists\_rule.py.  
  * For the block {'type': 'paragraph', ...}, it runs the general language\_and\_grammar rules.

#### Step 4: Highly Accurate Error Detection

Because the rules now know the context of the text they are analyzing, they are far more accurate and avoid the false positives we were seeing before.

* **Action:** The SpaCy rules analyze the text *with context*.  
* **Result:** The procedures\_rule.py no longer has to guess if a sentence is a step; it *knows* it is, because it was told the block type is list\_item\_ordered. This eliminates errors.  
* **Output:** A clean and reliable list of genuine errors is generated.

#### Step 5: Dynamic Prompt Generation

The highly accurate list of errors is passed to your PromptGenerator.

* **Action:** The PromptGenerator loads the instructions from your .yaml configuration files based on the specific error types that were found.  
* **Output:** A precise, targeted prompt is built for the AI Rewriter.

#### Step 6: AI Rewrite

The AI Rewriter receives the targeted prompt and generates the improved text. Because the instructions are so specific and based on a more accurate analysis, the AI is much more likely to produce a high-quality result without introducing new errors.

#### Step 7: Final Output

The user is presented with the final, rewritten text, which has been corrected based on a deep, structural understanding of the original document.