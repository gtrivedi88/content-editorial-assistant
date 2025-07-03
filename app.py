"""
Style Guide Application - Main Entry Point
A modular Flask application for content analysis and AI-powered rewriting.
"""


import os
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import re
from werkzeug.exceptions import RequestEntityTooLarge
from flask_socketio import SocketIO, emit
import uuid
import time


# Try to import our custom modules with fallbacks
try:
   from src.document_processor import DocumentProcessor
   DOCUMENT_PROCESSOR_AVAILABLE = True
   print("✅ DocumentProcessor imported successfully")
except ImportError as e:
   DOCUMENT_PROCESSOR_AVAILABLE = False
   print(f"⚠️ Document processor not available - {e}")


try:
   from src.style_analyzer import StyleAnalyzer
   STYLE_ANALYZER_AVAILABLE = True
   print("✅ StyleAnalyzer imported successfully")
except ImportError as e:
   STYLE_ANALYZER_AVAILABLE = False
   print(f"⚠️ Style analyzer not available - {e}")


try:
   from rewriter import AIRewriter
   AI_REWRITER_AVAILABLE = True
   print("✅ AIRewriter imported successfully")
except ImportError as e:
   AI_REWRITER_AVAILABLE = False
   print(f"⚠️ AI rewriter not available - {e}")


from src.config import Config


# Simple fallback classes
class SimpleDocumentProcessor:
   def allowed_file(self, filename):
       return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'md'}
  
   def extract_text(self, filepath):
       try:
           with open(filepath, 'r', encoding='utf-8') as f:
               return f.read()
       except:
           return None


class SimpleStyleAnalyzer:
   def analyze(self, content: str):
       """Simple style analysis without complex NLP."""
       errors = []
       suggestions = []
      
       sentences = re.split(r'[.!?]+', content)
      
       for i, sentence in enumerate(sentences):
           sentence = sentence.strip()
           if not sentence:
               continue
              
           words = sentence.split()
           word_count = len(words)
          
           # Check sentence length
           if word_count > 25:
               errors.append({
                   'type': 'sentence_length',
                   'sentence': sentence,
                   'message': f'Sentence is too long ({word_count} words). Consider breaking it up.',
                   'position': i,
                   'word_count': word_count
               })
          
           # Check for passive voice (simple detection)
           if re.search(r'\b(was|were|is|are|been)\s+\w+ed\b', sentence, re.IGNORECASE):
               errors.append({
                   'type': 'passive_voice',
                   'sentence': sentence,
                   'message': 'Consider using active voice instead of passive voice.',
                   'position': i
               })
          
           # Check for wordy phrases
           wordy_phrases = ['in order to', 'due to the fact that', 'at this point in time', 'utilize', 'facilitate']
           for phrase in wordy_phrases:
               if phrase in sentence.lower():
                   errors.append({
                       'type': 'conciseness',
                       'sentence': sentence,
                       'message': f'Consider replacing "{phrase}" with a more concise alternative.',
                       'position': i
                   })
      
       return {
           'errors': errors,
           'suggestions': suggestions,
           'word_count': len(content.split()),
           'sentence_count': len([s for s in sentences if s.strip()]),
           'readability_score': 65.0  # Placeholder
       }


class SimpleAIRewriter:
   def __init__(self):
       import requests
       self.requests = requests
       ai_config = Config.get_ai_config()
       self.use_ollama = ai_config['use_ollama']
       self.ollama_model = ai_config['ollama_model']
       self.ollama_url = ai_config['ollama_url']
  
   def rewrite(self, content: str, errors=None, context: str = "sentence"):
       """Generate AI-powered rewrite."""
       if errors is None:
           errors = []
       if not content.strip():
           return {
               'rewritten_text': '',
               'improvements': [],
               'confidence': 0.0,
               'error': 'No content provided'
           }
      
       if self.use_ollama:
           return self._rewrite_with_ollama(content, errors)
       else:
           return self._rule_based_rewrite(content, errors)
  
   def _rewrite_with_ollama(self, content: str, errors=None):
       """Generate rewrite using Ollama."""
       if errors is None:
           errors = []
       prompt = f"""You are a professional writing assistant. Please rewrite the following text to make it clearer, more concise, and more professional while preserving the original meaning.


Original text:
{content}


Improved text:"""
      
       try:
           payload = {
               "model": self.ollama_model,
               "prompt": prompt,
               "stream": False,
               "options": {
                   "temperature": 0.7,
                   "top_p": 0.9,
                   "top_k": 40,
                   "num_predict": 100
               }
           }
          
           response = self.requests.post(self.ollama_url, json=payload, timeout=60)
          
           if response.status_code == 200:
               result = response.json()
               rewritten = result.get('response', '').strip()
              
               return {
                   'rewritten_text': rewritten if rewritten else content,
                   'improvements': ['AI-generated improvements'],
                   'confidence': 0.8,
                   'model_used': 'ollama'
               }
           else:
               return self._rule_based_rewrite(content, errors)
       except Exception as e:
           return self._rule_based_rewrite(content, errors)
  
   def _rule_based_rewrite(self, content: str, errors=None):
       """Fallback rule-based rewriting."""
       if errors is None:
           errors = []
       rewritten = content
       improvements = []
      
       # Simple replacements
       replacements = {
           'in order to': 'to',
           'due to the fact that': 'because',
           'utilize': 'use',
           'facilitate': 'help'
       }
      
       for old, new in replacements.items():
           if old in rewritten.lower():
               rewritten = re.sub(r'\b' + re.escape(old) + r'\b', new, rewritten, flags=re.IGNORECASE)
               improvements.append(f'Replaced "{old}" with "{new}"')
      
       return {
           'rewritten_text': rewritten,
           'improvements': improvements or ['Applied basic style improvements'],
           'confidence': 0.6,
           'model_used': 'rule-based'
       }
  
   def get_system_info(self):
       """Get system information for AI rewriter."""
       return {
           'model_info': {
               'use_ollama': self.use_ollama,
               'ollama_model': self.ollama_model,
               'ollama_url': self.ollama_url
           },
           'status': 'ready'
       }
  
   def refine_text(self, content: str, errors=None, context: str = "sentence"):
       """Refine text (Pass 2 processing)."""
       if errors is None:
           errors = []
       # For simplicity, use the same rewrite logic but with different confidence
       result = self.rewrite(content, errors, context)
       result['pass_number'] = 2
       result['can_refine'] = False
       return result


# Configure logging
logging.basicConfig(
   level=getattr(logging, Config.LOG_LEVEL),
   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)


# Initialize extensions
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
db = SQLAlchemy(app)


# Initialize processors with fallbacks
if DOCUMENT_PROCESSOR_AVAILABLE:
   document_processor = DocumentProcessor()
else:
   document_processor = SimpleDocumentProcessor()
   logger.warning("Using simple document processor fallback")


if STYLE_ANALYZER_AVAILABLE:
   style_analyzer = StyleAnalyzer()
else:
   style_analyzer = SimpleStyleAnalyzer()
   logger.warning("Using simple style analyzer fallback")


if AI_REWRITER_AVAILABLE:
   ai_config = Config.get_ai_config()
   ai_rewriter = AIRewriter(
       model_name=ai_config['hf_model_name'],
       use_ollama=ai_config['use_ollama'],
       ollama_model=ai_config['ollama_model']
   )
else:
   ai_rewriter = SimpleAIRewriter()
   logger.warning("Using simple AI rewriter fallback")


# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Progress tracking
progress_sessions = {}


def emit_progress(session_id, step, status, detail, progress_percent=None):
   """Emit progress update to specific session"""
   if session_id in progress_sessions:
       socketio.emit('progress_update', {
           'step': step,
           'status': status,
           'detail': detail,
           'progress': progress_percent,
           'timestamp': datetime.now().isoformat()
       }, to=session_id)
       logger.info(f"Progress update sent to {session_id}: {step} - {status}")


def emit_completion(session_id, success, data=None, error=None):
   """Emit completion status to specific session"""
   if session_id in progress_sessions:
       socketio.emit('process_complete', {
           'success': success,
           'data': data,
           'error': error,
           'timestamp': datetime.now().isoformat()
       }, to=session_id)
       logger.info(f"Completion sent to {session_id}: {'Success' if success else 'Error'}")


@socketio.on('connect')
def handle_connect():
   session_id = str(uuid.uuid4())
   progress_sessions[session_id] = True
   emit('session_id', {'session_id': session_id})
   logger.info(f"Client connected with session ID: {session_id}")


@socketio.on('disconnect')
def handle_disconnect():
   # Clean up session if needed
   pass


@app.route('/')
def index():
   """Main application homepage."""
   # Use simple built-in template if template files are missing
   try:
       return render_template('index.html')
   except:
       return """
       <!DOCTYPE html>
       <html>
       <head>
           <title>Peer lens</title>
           <style>
               body { font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }
               .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
               textarea { width: 100%; height: 200px; margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
               button { padding: 12px 24px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
               button:hover { background: #0056b3; }
               .result { background: #f8f9fa; padding: 20px; margin: 20px 0; border: 1px solid #dee2e6; border-radius: 4px; }
               .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 5px 0; }
               .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; margin: 5px 0; }
               .stats { display: flex; gap: 20px; margin: 20px 0; }
               .stat { background: #e9ecef; padding: 15px; border-radius: 4px; text-align: center; flex: 1; }
               h1 { color: #333; margin-bottom: 10px; }
               h3 { color: #495057; }
               .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }
               .feature { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
           </style>
       </head>
       <body>
           <div class="container">
               <h1>🎯 Peer lens</h1>
               <p>AI-powered writing assistant with local Ollama integration</p>
              
               <div class="features">
                   <div class="feature">
                       <h4>📝 Style Analysis</h4>
                       <p>Detects long sentences, passive voice, and wordy phrases</p>
                   </div>
                   <div class="feature">
                       <h4>🤖 AI Rewriting</h4>
                       <p>Uses local Llama 8B model for professional text improvements</p>
                   </div>
                   <div class="feature">
                       <h4>🔒 Privacy First</h4>
                       <p>All processing happens locally on your machine</p>
                   </div>
               </div>
              
               <h3>Test Your Text:</h3>
               <textarea id="content" placeholder="Enter your text here for analysis...">In order to facilitate the implementation of the new system, it was decided by the team that the best approach would be to utilize a modular architecture that can be implemented in a cost-effective manner.</textarea>
              
               <div>
                   <button onclick="analyzeText()">📊 Analyze Style</button>
                   <button onclick="rewriteText()">✨ Rewrite with AI</button>
                   <button onclick="checkHealth()">🔧 System Health</button>
                   <button onclick="clearResults()">🗑️ Clear</button>
               </div>
              
               <div id="stats" class="stats" style="display:none;">
                   <div class="stat">
                       <div id="wordCount">-</div>
                       <small>Words</small>
                   </div>
                   <div class="stat">
                       <div id="sentenceCount">-</div>
                       <small>Sentences</small>
                   </div>
                   <div class="stat">
                       <div id="errorCount">-</div>
                       <small>Issues</small>
                   </div>
                   <div class="stat">
                       <div id="readabilityScore">-</div>
                       <small>Readability</small>
                   </div>
               </div>
              
               <div id="results"></div>
           </div>
          
           <script>
               async function analyzeText() {
                   const content = document.getElementById('content').value;
                   if (!content.trim()) {
                       alert('Please enter some text to analyze.');
                       return;
                   }
                  
                   try {
                       const response = await fetch('/analyze', {
                           method: 'POST',
                           headers: {'Content-Type': 'application/json'},
                           body: JSON.stringify({content})
                       });
                       const result = await response.json();
                      
                       if (result.success) {
                           displayAnalysisResults(result);
                       } else {
                           displayError('Analysis failed: ' + (result.error || 'Unknown error'));
                       }
                   } catch (error) {
                       displayError('Network error: ' + error.message);
                   }
               }
              
               async function rewriteText() {
                   const content = document.getElementById('content').value;
                   if (!content.trim()) {
                       alert('Please enter some text to rewrite.');
                       return;
                   }
                  
                   document.getElementById('results').innerHTML = '<div class="result">⏳ AI is rewriting your text...</div>';
                  
                   try {
                       const response = await fetch('/rewrite', {
                           method: 'POST',
                           headers: {'Content-Type': 'application/json'},
                           body: JSON.stringify({content, errors: []})
                       });
                       const result = await response.json();
                      
                       if (result.success) {
                           displayRewriteResults(result);
                       } else {
                           displayError('Rewrite failed: ' + (result.error || 'Unknown error'));
                       }
                   } catch (error) {
                       displayError('Network error: ' + error.message);
                   }
               }
              
               async function checkHealth() {
                   try {
                       const response = await fetch('/health');
                       const result = await response.json();
                       displayHealthResults(result);
                   } catch (error) {
                       displayError('Health check failed: ' + error.message);
                   }
               }
              
               function displayAnalysisResults(result) {
                   const analysis = result.analysis;
                  
                   // Update stats
                   document.getElementById('stats').style.display = 'flex';
                   document.getElementById('wordCount').textContent = analysis.word_count;
                   document.getElementById('sentenceCount').textContent = analysis.sentence_count;
                   document.getElementById('errorCount').textContent = analysis.errors.length;
                   document.getElementById('readabilityScore').textContent = analysis.readability_score || 'N/A';
                  
                   let html = '<div class="result"><h3>Analysis Results</h3>';
                  
                   if (analysis.errors.length === 0) {
                       html += '<div class="success">✅ No major style issues detected!</div>';
                   } else {
                       html += '<h4>Issues Found:</h4>';
                       analysis.errors.forEach(error => {
                           html += `<div class="error">
                               <strong>${error.type.replace('_', ' ').toUpperCase()}:</strong> ${error.message}
                               <br><em>"${error.sentence}"</em>
                           </div>`;
                       });
                   }
                  
                   html += '</div>';
                   document.getElementById('results').innerHTML = html;
               }
              
               function displayRewriteResults(result) {
                   let html = '<div class="result"><h3>✨ AI Rewrite Results</h3>';
                  
                   if (result.error) {
                       html += `<div class="error">❌ ${result.error}</div>`;
                   } else {
                       html += `
                           <div class="success">
                               <h4>Original:</h4>
                               <p style="background: #fff; padding: 10px; border-left: 3px solid #dc3545;">${result.original || result.rewritten_text}</p>
                              
                               <h4>Improved:</h4>
                               <p style="background: #fff; padding: 10px; border-left: 3px solid #28a745;">${result.rewritten_text}</p>
                              
                               <p><strong>Model:</strong> ${result.model_used || 'Unknown'} |
                                  <strong>Confidence:</strong> ${Math.round((result.confidence || 0) * 100)}%</p>
                              
                               <h4>Improvements:</h4>
                               <ul>
                                   ${(result.improvements || []).map(imp => '<li>' + imp + '</li>').join('')}
                               </ul>
                           </div>
                       `;
                   }
                  
                   html += '</div>';
                   document.getElementById('results').innerHTML = html;
               }
              
               function displayHealthResults(result) {
                   let html = '<div class="result"><h3>🔧 System Health</h3>';
                  
                   html += `<p><strong>Status:</strong> ${result.status}</p>`;
                   html += `<p><strong>Version:</strong> ${result.version}</p>`;
                   html += `<p><strong>AI Model:</strong> ${result.ai_model_type || result.ollama_model || 'N/A'}</p>`;
                  
                   if (result.services) {
                       html += '<h4>Services:</h4><ul>';
                       Object.entries(result.services).forEach(([service, status]) => {
                           const icon = status.includes('ready') || status === 'available' ? '✅' : '❌';
                           html += `<li>${icon} ${service}: ${status}</li>`;
                       });
                       html += '</ul>';
                   }
                  
                   html += '</div>';
                   document.getElementById('results').innerHTML = html;
               }
              
               function displayError(message) {
                   document.getElementById('results').innerHTML =
                       '<div class="result"><div class="error">❌ ' + message + '</div></div>';
               }
              
               function clearResults() {
                   document.getElementById('results').innerHTML = '';
                   document.getElementById('stats').style.display = 'none';
                   document.getElementById('content').value = '';
               }
           </script>
       </body>
       </html>
       """


@app.route('/upload', methods=['POST'])
def upload_file():
   """Handle file upload and initial processing."""
   try:
       if 'file' not in request.files:
           return jsonify({'error': 'No file provided'}), 400
      
       file = request.files['file']
       if file.filename == '':
           return jsonify({'error': 'No file selected'}), 400
      
       if file and file.filename and document_processor.allowed_file(file.filename):
           filename = secure_filename(file.filename)
           timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
           filename = timestamp + filename
          
           filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
           file.save(filepath)
          
           # Process the document
           text_content = document_processor.extract_text(filepath)
          
           if text_content:
               return jsonify({
                   'success': True,
                   'filename': filename,
                   'content': text_content,
                   'message': 'File uploaded and processed successfully'
               })
           else:
               return jsonify({'error': 'Failed to extract text from file'}), 400
              
       else:
           return jsonify({'error': 'File type not supported'}), 400
          
   except Exception as e:
       logger.error(f"Upload error: {str(e)}")
       return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/analyze', methods=['POST'])
def analyze_content():
   """Analyze text content for style issues with real-time progress."""
   try:
       data = request.get_json()
       content = data.get('content', '')
       session_id = data.get('session_id', '')
      
       if not content:
           return jsonify({'error': 'No content provided'}), 400
      
       # Send initial progress
       emit_progress(session_id, 'analysis_start', 'Starting text analysis...',
                    'Initializing SpaCy NLP processor', 10)
      
       # Perform analysis
       emit_progress(session_id, 'spacy_processing', 'Processing with SpaCy NLP...',
                    'Detecting sentence structure and style issues', 30)
      
       analysis = style_analyzer.analyze(content)
      
       emit_progress(session_id, 'metrics_calculation', 'Calculating readability metrics...',
                    'Computing Flesch, Fog, SMOG, and other scores', 60)
      
       # Add some processing time for metrics
       time.sleep(0.5)  # Small delay to show progress
      
       emit_progress(session_id, 'analysis_complete', 'Analysis completed successfully!',
                    f'Found {len(analysis.get("errors", []))} style issues', 100)
      
       return jsonify({
           'success': True,
           'analysis': analysis
       })
      
   except Exception as e:
       logger.error(f"Analysis error: {str(e)}")
       if 'session_id' in locals():
           emit_completion(session_id, False, error=f'Analysis failed: {str(e)}')
       return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/rewrite', methods=['POST'])
def rewrite_content():
   """Generate AI-powered rewrite suggestions (Pass 1)."""
   try:
       data = request.get_json()
       content = data.get('content', '')
       errors = data.get('errors', [])
       context = data.get('context', 'sentence')
       session_id = data.get('session_id', '')
      
       if not content:
           return jsonify({'error': 'No content provided'}), 400
      
       # Send initial progress
       emit_progress(session_id, 'rewrite_start', 'Starting AI rewrite process...',
                    f'Processing {len(errors)} detected issues', 5)
      
       # Create progress callback function
       def progress_callback(step, status, detail, progress):
           emit_progress(session_id, step, status, detail, progress)
      
       # Create AI rewriter with progress callback using system info
       system_info = ai_rewriter.get_system_info()
       model_info = system_info.get('model_info', {})
      
       progress_ai_rewriter = AIRewriter(
           use_ollama=model_info.get('use_ollama', True),
           ollama_model=model_info.get('ollama_model', 'llama3:8b'),
           progress_callback=progress_callback
       )
      
       # Perform Pass 1 rewrite with real-time progress
       rewrite_result = progress_ai_rewriter.rewrite(content, errors, context, pass_number=1)
      
       return jsonify({
           'success': True,
           'original': content,
           'rewritten': rewrite_result.get('rewritten_text', ''),
           'rewritten_text': rewrite_result.get('rewritten_text', ''),
           'improvements': rewrite_result.get('improvements', []),
           'confidence': rewrite_result.get('confidence', 0.0),
           'model_used': rewrite_result.get('model_used', 'unknown'),
           'pass_number': rewrite_result.get('pass_number', 1),
           'can_refine': rewrite_result.get('can_refine', False),
           'original_errors': errors  # Store for potential Pass 2
       })
      
   except Exception as e:
       logger.error(f"Rewrite error: {str(e)}")
       if 'session_id' in locals():
           emit_completion(session_id, False, error=f'Rewrite failed: {str(e)}')
       return jsonify({'error': f'Rewrite failed: {str(e)}'}), 500


@app.route('/refine', methods=['POST'])
def refine_content():
   """Generate AI-powered refinement (Pass 2)."""
   try:
       data = request.get_json()
       first_pass_result = data.get('first_pass_result', '')
       original_errors = data.get('original_errors', [])
       context = data.get('context', 'sentence')
       session_id = data.get('session_id', '')
      
       if not first_pass_result:
           return jsonify({'error': 'No first pass result provided'}), 400
      
       # Send initial progress
       emit_progress(session_id, 'refine_start', 'Starting AI refinement process...',
                    'AI reviewing and polishing the first pass result', 5)
      
       # Create progress callback function
       def progress_callback(step, status, detail, progress):
           emit_progress(session_id, step, status, detail, progress)
      
       # Create AI rewriter with progress callback using system info
       system_info = ai_rewriter.get_system_info()
       model_info = system_info.get('model_info', {})
      
       progress_ai_rewriter = AIRewriter(
           use_ollama=model_info.get('use_ollama', True),
           ollama_model=model_info.get('ollama_model', 'llama3:8b'),
           progress_callback=progress_callback
       )
      
       # Perform Pass 2 refinement with real-time progress
       refinement_result = progress_ai_rewriter.refine_text(first_pass_result, original_errors, context)
      
       return jsonify({
           'success': True,
           'first_pass': first_pass_result,
           'refined': refinement_result.get('rewritten_text', ''),
           'rewritten_text': refinement_result.get('rewritten_text', ''),
           'improvements': refinement_result.get('improvements', []),
           'confidence': refinement_result.get('confidence', 0.0),
           'model_used': refinement_result.get('model_used', 'unknown'),
           'pass_number': refinement_result.get('pass_number', 2),
           'can_refine': refinement_result.get('can_refine', False)
       })
      
   except Exception as e:
       logger.error(f"Refinement error: {str(e)}")
       if 'session_id' in locals():
           emit_completion(session_id, False, error=f'Refinement failed: {str(e)}')
       return jsonify({'error': f'Refinement failed: {str(e)}'}), 500


@app.route('/health')
def health_check():
   """Health check endpoint to verify service status."""
   try:
       # Check if Ollama is available when configured
       ollama_status = "not_configured"
       if Config.is_ollama_enabled():
           try:
               import requests
               response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
               if response.status_code == 200:
                   models = response.json().get('models', [])
                   model_names = [m['name'] for m in models]
                   ollama_status = "available" if Config.OLLAMA_MODEL in model_names else "model_not_found"
               else:
                   ollama_status = "service_unavailable"
           except:
               ollama_status = "connection_failed"
      
       return jsonify({
           'status': 'healthy',
           'timestamp': datetime.now().isoformat(),
           'version': '1.0.0',
           'ai_model_type': Config.AI_MODEL_TYPE,
           'ollama_status': ollama_status,
           'ollama_model': Config.OLLAMA_MODEL if Config.is_ollama_enabled() else None,
           'services': {
               'document_processor': 'ready' if DOCUMENT_PROCESSOR_AVAILABLE else 'fallback',
               'style_analyzer': 'ready' if STYLE_ANALYZER_AVAILABLE else 'fallback',
               'ai_rewriter': 'ready' if AI_REWRITER_AVAILABLE else 'fallback',
               'ollama': ollama_status
           }
       }), 200
      
   except Exception as e:
       logger.error(f"Health check failed: {str(e)}")
       return jsonify({
           'status': 'unhealthy',
           'error': str(e),
           'timestamp': datetime.now().isoformat()
       }), 500


@app.errorhandler(404)
def not_found(error):
   """Handle 404 errors."""
   try:
       return render_template('error.html', error='Page not found'), 404
   except:
       return jsonify({'error': 'Page not found'}), 404


@app.errorhandler(500)
def internal_error(error):
   """Handle 500 errors."""
   try:
       return render_template('error.html', error='Internal server error'), 500
   except:
       return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
   print("🚀 Starting Peer lens...")
   print("📊 Style Analysis: ✅ Available" if STYLE_ANALYZER_AVAILABLE else "📊 Style Analysis: ⚠️ Using fallback")
   print("📁 Document Processing: ✅ Available" if DOCUMENT_PROCESSOR_AVAILABLE else "📁 Document Processing: ⚠️ Using fallback")
   print("🤖 AI Rewriting: ✅ Available" if AI_REWRITER_AVAILABLE else "🤖 AI Rewriting: ⚠️ Using fallback")
   print("🌐 Server starting at: http://localhost:5000")
   print("🔄 Real-time progress tracking: ✅ Enabled")
   print()
  
   socketio.run(app, debug=True, host='0.0.0.0', port=5000)