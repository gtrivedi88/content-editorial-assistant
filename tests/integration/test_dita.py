"""
DITA Integration Tests
Tests DITA parser integration with format detection and parser factory.
"""

import unittest
from structural_parsing import StructuralParserFactory, FormatDetector
from structural_parsing.dita.types import DITABlockType, DITATopicType, DITAParseResult


class TestDITAFormatDetection(unittest.TestCase):
    """Test DITA format detection accuracy."""

    def setUp(self):
        self.detector = FormatDetector()

    def test_detect_dita_concept(self):
        """Test detection of DITA concept documents."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="test_concept">
  <title>Test Concept</title>
  <conbody><p>Concept content.</p></conbody>
</concept>'''
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'dita')

    def test_detect_dita_task(self):
        """Test detection of DITA task documents."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="test_task">
  <title>Test Task</title>
  <taskbody>
    <steps><step><cmd>Do something.</cmd></step></steps>
  </taskbody>
</task>'''
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'dita')

    def test_detect_dita_reference(self):
        """Test detection of DITA reference documents."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="test_reference">
  <title>API Reference</title>
  <refbody><p>Reference content.</p></refbody>
</reference>'''
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'dita')

    def test_detect_dita_vs_generic_xml(self):
        """Test distinguishing DITA from generic XML."""
        dita_content = '''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="dita_doc">
  <title>DITA Document</title>
  <conbody><p>DITA content</p></conbody>
</concept>'''
        
        generic_xml = '''<?xml version="1.0"?>
<root>
  <element>Generic XML content</element>
  <data>Not DITA format</data>
</root>'''
        
        self.assertEqual(self.detector.detect_format(dita_content), 'dita')
        # Generic XML should not be detected as DITA
        detected_generic = self.detector.detect_format(generic_xml)
        self.assertNotEqual(detected_generic, 'dita')

    def test_detect_xml_files_as_dita(self):
        """Test detection of DITA content in .xml files."""
        # DITA content but in XML file
        xml_with_dita = '''<?xml version="1.0" encoding="UTF-8"?>
<concept id="xml_dita">
  <title>DITA in XML File</title>
  <shortdesc>DITA content in .xml file.</shortdesc>
  <conbody><p>Should be detected as DITA.</p></conbody>
</concept>'''
        
        format_detected = self.detector.detect_format(xml_with_dita)
        self.assertEqual(format_detected, 'dita')


class TestDITAParserFactory(unittest.TestCase):
    """Test DITA integration with parser factory."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_auto_detect_and_parse_dita(self):
        """Test automatic detection and parsing of DITA."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="auto_detect_test">
  <title>Auto Detection Test</title>
  <shortdesc>Testing automatic DITA detection.</shortdesc>
  <taskbody>
    <prereq><p>Prerequisites here.</p></prereq>
    <context><p>Context information.</p></context>
    <steps>
      <step><cmd>Execute command.</cmd></step>
      <step><cmd>Verify result.</cmd></step>
    </steps>
    <result><p>Expected outcome.</p></result>
  </taskbody>
</task>'''
        
        result = self.factory.parse(content, format_hint='auto')
        
        self.assertIsInstance(result, DITAParseResult)
        self.assertTrue(result.success)
        self.assertEqual(result.topic_type, DITATopicType.TASK)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1)

    def test_explicit_dita_hint(self):
        """Test explicit DITA format hint."""
        content = '''<?xml version="1.0"?>
<concept id="explicit_test">
  <title>Explicit DITA Test</title>
  <conbody><p>Content for explicit DITA parsing.</p></conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertIsInstance(result, DITAParseResult)
        self.assertTrue(result.success)

    def test_xml_file_with_dita_content(self):
        """Test XML file containing DITA content."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<reference id="xml_file_dita">
  <title>DITA Content in XML File</title>
  <shortdesc>This is DITA content but in an XML file.</shortdesc>
  <refbody>
    <section>
      <title>API Functions</title>
      <properties>
        <property>
          <proptype>getUser()</proptype>
          <propvalue>User object</propvalue>
          <propdesc>Retrieves user information</propdesc>
        </property>
      </properties>
    </section>
  </refbody>
</reference>'''
        
        # Should auto-detect as DITA even without DOCTYPE
        result = self.factory.parse(content, format_hint='auto')
        
        self.assertIsInstance(result, DITAParseResult)
        self.assertTrue(result.success)
        self.assertEqual(result.topic_type, DITATopicType.REFERENCE)

    def test_get_available_parsers_includes_dita(self):
        """Test that DITA parser is listed in available parsers."""
        parsers = self.factory.get_available_parsers()
        
        self.assertIn('dita', parsers)
        self.assertTrue(parsers['dita']['available'])
        self.assertEqual(parsers['dita']['parser'], 'dedicated DITA XML parser')


class TestDITAErrorHandling(unittest.TestCase):
    """Test DITA parser error handling and recovery."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_invalid_xml_content(self):
        """Test handling of invalid XML."""
        invalid_xml = '''<?xml version="1.0"?>
<concept id="invalid">
  <title>Invalid XML</title>
  <conbody>
    <p>Unclosed paragraph
    <p>Another unclosed paragraph
  </conbody>
</concept'''  # Missing closing >
        
        result = self.factory.parse(invalid_xml, format_hint='dita')
        
        # Should fail gracefully
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)

    def test_non_dita_xml_as_dita(self):
        """Test parsing non-DITA XML with DITA parser."""
        non_dita_xml = '''<?xml version="1.0"?>
<root>
  <element>Not DITA content</element>
  <data>Generic XML structure</data>
</root>'''
        
        result = self.factory.parse(non_dita_xml, format_hint='dita')
        
        # Should handle gracefully, might succeed with generic parsing
        self.assertIsNotNone(result)

    def test_empty_dita_content(self):
        """Test empty DITA content."""
        result = self.factory.parse("", format_hint='dita')
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.document)

    def test_massive_dita_document_performance(self):
        """Test performance with massive DITA document."""
        # Create massive document
        massive_sections = []
        for i in range(1000):
            massive_sections.append(f'''
    <section id="perf_section_{i}">
      <title>Performance Section {i}</title>
      <p>Performance test content for section {i}.</p>
      <ul>
        <li>Item {i}.1</li>
        <li>Item {i}.2</li>
        <li>Item {i}.3</li>
      </ul>
      <codeblock>
# Code block {i}
function test_{i}() {{
    return "test_{i}";
}}
      </codeblock>
    </section>''')
        
        massive_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="massive_performance_test">
  <title>Massive DITA Performance Test</title>
  <shortdesc>Testing parser performance with 1000 sections.</shortdesc>
  <conbody>{"".join(massive_sections)}
  </conbody>
</concept>'''
        
        import time
        start_time = time.time()
        result = self.factory.parse(massive_content, format_hint='dita')
        parse_time = time.time() - start_time
        
        self.assertTrue(result.success)
        # Count all blocks including nested ones for massive document
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 500)
        self.assertLess(parse_time, 15.0, f"Massive DITA parsing took too long: {parse_time:.2f}s")
        
        print(f"MASSIVE DITA ({len(massive_content):,} chars) parsed in {parse_time:.3f}s")


class TestDITAStyleAnalyzerCompatibility(unittest.TestCase):
    """Test DITA compatibility with style analysis system."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_dita_block_interface_compatibility(self):
        """Test DITA blocks work with style analysis interface."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="interface_test">
  <title>Interface Compatibility Test</title>
  <shortdesc>Testing block interface for style analysis.</shortdesc>
  <conbody>
    <p>This paragraph should be analyzed for style issues.</p>
    <p>Another paragraph with different content for analysis.</p>
    <codeblock>
// This code should be skipped from analysis
function example() {
    return "example";
}
    </codeblock>
    <note type="important">
      <p>Important note that should be analyzed.</p>
    </note>
  </conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        
        # Test interface compatibility
        for block in result.document.blocks:
            # Test required methods exist and work
            self.assertIsInstance(block.should_skip_analysis(), bool)
            self.assertIsInstance(block.get_text_content(), str)
            self.assertIsInstance(block.get_context_info(), dict)
            self.assertIsInstance(block.to_dict(), dict)
            
            # Test DITA-specific context
            context = block.get_context_info()
            self.assertIn('block_type', context)
            self.assertIn('topic_type', context)
            if result.topic_type:
                self.assertEqual(context['topic_type'], result.topic_type.value)

    def test_dita_text_extraction_quality(self):
        """Test quality of text extraction from DITA for style analysis."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="text_extraction">
  <title>Text Extraction Quality Test</title>
  <taskbody>
    <context>
      <p>This context paragraph has <b>bold</b> and <codeph>inline code</codeph> formatting.</p>
    </context>
    <steps>
      <step>
        <cmd>Execute this <cmdname>command</cmdname> with <parmname>parameter</parmname>.</cmd>
        <info>Additional <uicontrol>UI control</uicontrol> information.</info>
      </step>
    </steps>
  </taskbody>
</task>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        
        # Test text extraction quality
        for block in result.document.blocks:
            if not block.should_skip_analysis():
                text_content = block.get_text_content()
                # Should have clean text without XML tags
                self.assertNotIn('<', text_content)
                self.assertNotIn('>', text_content)
                # Should have meaningful content
                if block.block_type != DITABlockType.TITLE:  # Skip empty title check
                    self.assertGreater(len(text_content.strip()), 0)

    def test_dita_serialization_for_web_api(self):
        """Test DITA block serialization for web API responses."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="serialization_test">
  <title>Serialization Test</title>
  <conbody>
    <p>Test paragraph for serialization.</p>
    <section>
      <title>Test Section</title>
      <p>Section content.</p>
    </section>
  </conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        
        # Test serialization
        for block in result.document.blocks:
            block_dict = block.to_dict()
            
            # Required fields for web API
            required_fields = ['block_type', 'content', 'level', 'topic_type',
                             'should_skip_analysis', 'errors', 'children']
            for field in required_fields:
                self.assertIn(field, block_dict)
            
            # Verify data types
            self.assertIsInstance(block_dict['block_type'], str)
            self.assertIsInstance(block_dict['content'], str)
            self.assertIsInstance(block_dict['level'], int)
            self.assertIsInstance(block_dict['should_skip_analysis'], bool)
            self.assertIsInstance(block_dict['errors'], list)
            self.assertIsInstance(block_dict['children'], list)


class TestDITAFileExtensionSupport(unittest.TestCase):
    """Test support for both .dita and .xml file extensions."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_dita_file_extension_support(self):
        """Test that .dita files are properly supported."""
        from structural_parsing.extractors import DocumentProcessor
        processor = DocumentProcessor()
        
        # Test file extension acceptance
        self.assertTrue(processor.allowed_file('document.dita'))
        self.assertTrue(processor.allowed_file('concept.dita'))
        self.assertTrue(processor.allowed_file('task.dita'))
        self.assertTrue(processor.allowed_file('reference.dita'))

    def test_xml_file_extension_support(self):
        """Test that .xml files are properly supported."""
        from structural_parsing.extractors import DocumentProcessor
        processor = DocumentProcessor()
        
        # Test XML file extension acceptance
        self.assertTrue(processor.allowed_file('document.xml'))
        self.assertTrue(processor.allowed_file('dita-export.xml'))
        self.assertTrue(processor.allowed_file('aem-content.xml'))

    def test_aem_workflow_simulation(self):
        """Simulate complete AEM workflow with different file extensions."""
        # Simulate AEM export scenarios
        test_cases = [
            ('concept.dita', 'DITA file from AEM authoring'),
            ('task-export.xml', 'XML export from AEM'),
            ('reference.dita', 'Reference topic from AEM'),
            ('troubleshooting.xml', 'Troubleshooting export as XML')
        ]
        
        dita_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="aem_workflow">
  <title>AEM Workflow Test</title>
  <shortdesc>Testing AEM integration workflow.</shortdesc>
  <conbody>
    <p>Content authored in Adobe Experience Manager.</p>
    <section>
      <title>Configuration</title>
      <p>Configuration details for AEM integration.</p>
    </section>
  </conbody>
</concept>'''
        
        for filename, description in test_cases:
            with self.subTest(file=filename):
                # Parse with auto-detection (simulating web upload)
                result = self.factory.parse(dita_content, filename=filename, format_hint='auto')
                
                self.assertTrue(result.success, f"Failed to parse {filename}")
                self.assertIsInstance(result, DITAParseResult)
                self.assertIsNotNone(result.document)
                self.assertEqual(result.document.source_file, filename)


class TestDITAAdvancedFeatures(unittest.TestCase):
    """Test advanced DITA features and enterprise scenarios."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_dita_conref_and_keyref(self):
        """Test DITA content references and key references."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="conref_test">
  <title>Content Reference Test</title>
  <conbody>
    <p conref="shared-content.dita#shared/warning_para">Content reference placeholder</p>
    <p>Standard paragraph content.</p>
    <p conkeyref="standard-warnings/security-warning">Key reference placeholder</p>
    <ul conref="shared-lists.dita#lists/feature_list">
      <li>Fallback list item</li>
    </ul>
  </conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        # Should preserve conref attributes in block attributes
        for block in result.document.blocks:
            if hasattr(block, 'attributes') and block.attributes:
                # Conref attributes should be preserved
                self.assertIsInstance(block.attributes, dict)

    def test_dita_conditional_text(self):
        """Test DITA conditional text and filtering attributes."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="conditional_text">
  <title>Conditional Text Test</title>
  <conbody>
    <p>Content for all audiences.</p>
    <p audience="admin">Administrator-only content.</p>
    <p audience="user">End-user content.</p>
    <p platform="windows">Windows-specific content.</p>
    <p platform="linux mac">Unix-like systems content.</p>
    <p props="audience(developer) platform(api)">Developer API content.</p>
    <p otherprops="version(2.0) feature(advanced)">Version 2.0 advanced features.</p>
    
    <section audience="admin developer" platform="server">
      <title>Advanced Configuration</title>
      <p>Content for admins and developers on server platforms.</p>
    </section>
  </conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        # Should preserve filtering attributes (check flattened blocks)
        all_blocks = result.document.get_all_blocks_flat()
        conditional_blocks = [b for b in all_blocks 
                            if b.attributes and ('audience' in b.attributes or 'platform' in b.attributes)]
        self.assertGreater(len(conditional_blocks), 0)

    def test_dita_with_processing_instructions(self):
        """Test DITA with processing instructions and comments."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="dita2html.xsl"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<!-- This is a DITA concept document -->
<concept id="processing_instructions">
  <title>Processing Instructions Test</title>
  <!-- Internal comment -->
  <conbody>
    <p>Content with processing instructions.</p>
    <?custom-processing instruction="value"?>
    <!-- Another comment -->
    <section>
      <title>Section Title</title>
      <p>Section content.</p>
    </section>
  </conbody>
</concept>'''
        
        result = self.factory.parse(content, format_hint='dita')
        
        self.assertTrue(result.success)
        # Should handle processing instructions and comments gracefully


if __name__ == '__main__':
    unittest.main()
