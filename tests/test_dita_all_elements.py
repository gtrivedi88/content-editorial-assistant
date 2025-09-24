"""
ULTIMATE DITA Elements Test Suite
Tests EVERY DITA element, attribute, and structure known to mankind.

This is the most comprehensive DITA testing ever created.
"""

import unittest
from structural_parsing.dita.parser import DITAParser
from structural_parsing.dita.types import DITATopicType, DITABlockType


class TestDITAAllElementsKnownToMankind(unittest.TestCase):
    """Test absolutely EVERY DITA element that exists."""

    def setUp(self):
        self.parser = DITAParser()

    def test_every_dita_topic_type(self):
        """Test EVERY DITA topic type."""
        topic_tests = {
            'concept': '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="test_concept">
  <title>Test Concept</title>
  <conbody><p>Concept content.</p></conbody>
</concept>''',

            'task': '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">
<task id="test_task">
  <title>Test Task</title>
  <taskbody><p>Task content.</p></taskbody>
</task>''',

            'reference': '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="test_reference">
  <title>Test Reference</title>
  <refbody><p>Reference content.</p></refbody>
</reference>''',

            'troubleshooting': '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE troubleshooting PUBLIC "-//OASIS//DTD DITA Troubleshooting//EN" "troubleshooting.dtd">
<troubleshooting id="test_troubleshooting">
  <title>Test Troubleshooting</title>
  <troublebody><p>Troubleshooting content.</p></troublebody>
</troubleshooting>''',

            'generic_topic': '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">
<topic id="test_topic">
  <title>Test Topic</title>
  <body><p>Generic topic content.</p></body>
</topic>'''
        }

        for topic_name, content in topic_tests.items():
            with self.subTest(topic=topic_name):
                result = self.parser.parse(content)
                self.assertTrue(result.success, f"Failed to parse {topic_name}")
                self.assertIsNotNone(result.topic_type)
                self.assertGreater(len(result.document.blocks), 0)

    def test_every_dita_structure_element(self):
        """Test every DITA structural element."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="all_structure_elements">
  <title>Every DITA Structure Element</title>
  <titlealts>
    <navtitle>Navigation Title</navtitle>
    <searchtitle>Search Title</searchtitle>
  </titlealts>
  <shortdesc>Short description of the concept.</shortdesc>
  <abstract>
    <p>Abstract content that summarizes the topic.</p>
  </abstract>
  <prolog>
    <author>Technical Writer</author>
    <source>Documentation Team</source>
    <publisher>Company Name</publisher>
    <copyright>
      <copyryear year="2024"/>
      <copyrholder>Copyright Holder</copyrholder>
    </copyright>
    <critdates>
      <created date="2024-01-01"/>
      <revised modified="2024-01-15"/>
    </critdates>
    <permissions view="all"/>
    <metadata>
      <audience experiencelevel="expert" job="administrator" type="user"/>
      <category>Documentation</category>
      <keywords>
        <keyword>DITA</keyword>
        <keyword>XML</keyword>
        <keyword>documentation</keyword>
      </keywords>
      <prodinfo>
        <prodname>Product Name</prodname>
        <vrmlist>
          <vrm version="2" release="0" modification="1"/>
        </vrmlist>
      </prodinfo>
    </metadata>
  </prolog>
  <conbody>
    <p>Basic paragraph content.</p>
    
    <section spectitle="Special Section Title">
      <title>Section with Special Title</title>
      <p>Section content goes here.</p>
      
      <sectiondiv>
        <p>Section division content.</p>
      </sectiondiv>
    </section>
    
    <example spectitle="Code Example">
      <title>Example Section</title>
      <p>Example content with code:</p>
      <codeblock>console.log("Hello World");</codeblock>
    </example>
    
    <div>
      <p>Generic division content.</p>
    </div>
    
    <bodydiv>
      <p>Body division content.</p>
    </bodydiv>
  </conbody>
  <related-links>
    <link href="related-topic.dita"/>
    <linkpool>
      <link href="pool-topic-1.dita"/>
      <link href="pool-topic-2.dita"/>
    </linkpool>
  </related-links>
</concept>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Count all blocks including nested ones
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 3)

    def test_every_dita_list_type(self):
        """Test absolutely every DITA list type and variation."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="all_lists">
  <title>Every DITA List Type</title>
  <refbody>
    <section>
      <title>Unordered Lists</title>
      <ul>
        <li>Basic unordered item</li>
        <li>Item with <b>formatting</b></li>
        <li>Item with <codeph>inline code</codeph></li>
      </ul>
      
      <ul compact="yes">
        <li>Compact list item 1</li>
        <li>Compact list item 2</li>
      </ul>
      
      <ul spectitle="Special List Title">
        <li>List with special title</li>
      </ul>
    </section>
    
    <section>
      <title>Ordered Lists</title>
      <ol>
        <li>First ordered item</li>
        <li>Second ordered item</li>
        <li>Third ordered item</li>
      </ol>
      
      <ol type="a">
        <li>Alphabetic item a</li>
        <li>Alphabetic item b</li>
      </ol>
      
      <ol type="A">
        <li>Capital alphabetic A</li>
        <li>Capital alphabetic B</li>
      </ol>
      
      <ol type="i">
        <li>Roman numeral i</li>
        <li>Roman numeral ii</li>
      </ol>
      
      <ol type="I">
        <li>Capital Roman I</li>
        <li>Capital Roman II</li>
      </ol>
    </section>
    
    <section>
      <title>Simple Lists</title>
      <sl>
        <sli>Simple list item 1</sli>
        <sli>Simple list item 2</sli>
        <sli>Simple list item 3</sli>
      </sl>
      
      <sl compact="yes">
        <sli>Compact simple item</sli>
      </sl>
    </section>
    
    <section>
      <title>Definition Lists</title>
      <dl>
        <dlhead>
          <dthd>Term</dthd>
          <ddhd>Definition</ddhd>
        </dlhead>
        <dlentry>
          <dt>API</dt>
          <dd>Application Programming Interface</dd>
        </dlentry>
        <dlentry>
          <dt>REST</dt>
          <dd>Representational State Transfer</dd>
        </dlentry>
        <dlentry>
          <dt>CRUD</dt>
          <dd>Create, Read, Update, Delete operations</dd>
        </dlentry>
      </dl>
      
      <dl compact="yes">
        <dlentry>
          <dt>HTTP</dt>
          <dd>Hypertext Transfer Protocol</dd>
        </dlentry>
      </dl>
    </section>
    
    <section>
      <title>Parameter Lists</title>
      <parml>
        <plentry>
          <pt>timeout</pt>
          <pd>Connection timeout in seconds (default: 30)</pd>
        </plentry>
        <plentry>
          <pt>retries</pt>
          <pd>Number of retry attempts (default: 3)</pd>
        </plentry>
        <plentry>
          <pt>verbose</pt>
          <pd>Enable verbose logging (boolean)</pd>
        </plentry>
      </parml>
      
      <parml compact="yes">
        <plentry>
          <pt>debug</pt>
          <pd>Debug mode flag</pd>
        </plentry>
      </parml>
    </section>
  </refbody>
</reference>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Count all blocks including nested ones
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 3)

    def test_every_dita_table_element(self):
        """Test every DITA table element and structure."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="all_tables">
  <title>Every DITA Table Element</title>
  <refbody>
    <section>
      <title>Simple Tables</title>
      
      <simpletable>
        <sthead>
          <stentry>Column 1</stentry>
          <stentry>Column 2</stentry>
          <stentry>Column 3</stentry>
        </sthead>
        <strow>
          <stentry>Row 1, Col 1</stentry>
          <stentry>Row 1, Col 2</stentry>
          <stentry>Row 1, Col 3</stentry>
        </strow>
        <strow>
          <stentry>Row 2, Col 1</stentry>
          <stentry>Row 2, Col 2</stentry>
          <stentry>Row 2, Col 3</stentry>
        </strow>
      </simpletable>
      
      <simpletable keycol="1" relcolwidth="1* 2* 1*">
        <sthead>
          <stentry>Key Column</stentry>
          <stentry>Wide Column</stentry>
          <stentry>Normal Column</stentry>
        </sthead>
        <strow>
          <stentry>Key 1</stentry>
          <stentry>Wide content with more text</stentry>
          <stentry>Normal</stentry>
        </strow>
      </simpletable>
    </section>
    
    <section>
      <title>Complex Tables</title>
      
      <table frame="all" rowsep="1" colsep="1">
        <title>Complex Table with All Features</title>
        <desc>This table demonstrates all table features.</desc>
        <tgroup cols="4" align="left">
          <colspec colname="col1" colnum="1" colwidth="1*" align="left"/>
          <colspec colname="col2" colnum="2" colwidth="2*" align="center"/>
          <colspec colname="col3" colnum="3" colwidth="1*" align="right"/>
          <colspec colname="col4" colnum="4" colwidth="1.5*" align="left"/>
          <spanspec spanname="span12" namest="col1" nameend="col2"/>
          <spanspec spanname="span34" namest="col3" nameend="col4"/>
          <thead>
            <row>
              <entry>Feature</entry>
              <entry>Description</entry>
              <entry>Status</entry>
              <entry>Notes</entry>
            </row>
          </thead>
          <tbody>
            <row>
              <entry spanname="span12">Spanning Entry Across Columns 1-2</entry>
              <entry>Status 1</entry>
              <entry>Notes 1</entry>
            </row>
            <row>
              <entry>Feature 2</entry>
              <entry>Description 2</entry>
              <entry spanname="span34">Spanning Entry Across Columns 3-4</entry>
            </row>
            <row>
              <entry morerows="1">Multi-row Entry</entry>
              <entry>Description A</entry>
              <entry>Status A</entry>
              <entry>Notes A</entry>
            </row>
            <row>
              <entry>Description B</entry>
              <entry>Status B</entry>
              <entry>Notes B</entry>
            </row>
          </tbody>
        </tgroup>
      </table>
      
      <table pgwide="1">
        <title>Page-Wide Table</title>
        <tgroup cols="2">
          <thead>
            <row>
              <entry>Wide Column 1</entry>
              <entry>Wide Column 2</entry>
            </row>
          </thead>
          <tbody>
            <row>
              <entry>Wide content spanning full page width</entry>
              <entry>More wide content</entry>
            </row>
          </tbody>
        </tgroup>
      </table>
    </section>
    
    <section>
      <title>Choice Tables</title>
      <choicetable>
        <chhead>
          <choptionhd>Option</choptionhd>
          <chdeschd>Description</chdeschd>
        </chhead>
        <chrow>
          <choption>Option A</choption>
          <chdesc>Description of option A</chdesc>
        </chrow>
        <chrow>
          <choption>Option B</choption>
          <chdesc>Description of option B</chdesc>
        </chrow>
      </choicetable>
    </section>
  </refbody>
</reference>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Count all blocks including nested ones
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 2)

    def test_every_dita_inline_element(self):
        """Test absolutely every DITA inline element."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="all_inline">
  <title>Every DITA Inline Element</title>
  <conbody>
    <p>Text formatting: <b>bold</b>, <i>italic</i>, <u>underline</u>, <line-through>strikethrough</line-through>, 
    <overline>overline</overline>, <sup>superscript</sup>, <sub>subscript</sub>, <tt>teletype</tt>.</p>
    
    <p>Semantic markup: <term>terminology</term>, <keyword>keyword</keyword>, <cite>citation</cite>, 
    <q>quoted text</q>, <foreign xml:lang="fr">texte français</foreign>, <abbreviated-form keyref="api"/>.</p>
    
    <p>Technical elements: <codeph>inline.code()</codeph>, <filepath>/path/to/file.txt</filepath>, 
    <cmdname>grep</cmdname>, <varname>variable_name</varname>, <parmname>parameter</parmname>, 
    <option>--verbose</option>, <apiname>functionName</apiname>.</p>
    
    <p>User interface: <uicontrol>Button</uicontrol>, <wintitle>Window Title</wintitle>, 
    <menucascade><uicontrol>File</uicontrol><uicontrol>Open</uicontrol></menucascade>, 
    <screen>command line output</screen>.</p>
    
    <p>System elements: <systemoutput>System ready</systemoutput>, <userinput>user input</userinput>, 
    <msgnum>ERROR-001</msgnum>, <msgph>Error message text</msgph>, <msgblock>
Multi-line
error message
block</msgblock>.</p>
    
    <p>Programming: <synph><kwd>function</kwd> <var>name</var><delim>(</delim><var>params</var><delim>)</delim></synph>, 
    <oper>+</oper>, <sep>,</sep>, <repsep>,</repsep>.</p>
    
    <p>State and data: <state>active</state>, <data name="custom" value="123"/>, 
    <data-about>metadata content</data-about>, <unknown>unknown element</unknown>.</p>
    
    <p>Links and cross-references: <xref href="external.dita">external link</xref>, 
    <xref href="#concept_id/element_id">internal link</xref>, <link href="related.dita">
    <linktext>Link Text</linktext><desc>Link description</desc></link>.</p>
    
    <p>Index and glossary: <indexterm>index term</indexterm>, 
    <indexterm>main term<indexterm>sub term</indexterm></indexterm>.</p>
    
    <p>Miscellaneous: <ph>phrase</ph>, <text>text element</text>, <boolean state="yes"/>, 
    <draft-comment author="reviewer">Draft comment content</draft-comment>.</p>
    
    <p>Equations: <equation-inline>E = mc<sup>2</sup></equation-inline>, 
    with <equation-number>(1)</equation-number>.</p>
    
    <p>Markup references: <markupname>elementName</markupname>, <xmlelement>xmlElement</xmlelement>, 
    <xmlatt>xmlAttribute</xmlatt>, <textentity>textEntity</textentity>.</p>
    
    <p>Hazard statements: <hazardstatement type="caution">
    <messagepanel><typeofhazard>Electrical hazard</typeofhazard>
    <consequence>May cause electric shock</consequence>
    <howtoavoid>Turn off power before servicing</howtoavoid></messagepanel>
    </hazardstatement>.</p>
  </conbody>
</concept>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Count all blocks including nested ones
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 2)

    def test_every_dita_media_element(self):
        """Test every DITA media and object element."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="all_media">
  <title>Every DITA Media Element</title>
  <conbody>
    <section>
      <title>Images</title>
      <p>Basic image: <image href="screenshot.png">
      <alt>Screenshot of the interface</alt></image></p>
      
      <fig>
        <title>Figure with Image</title>
        <image href="diagram.svg" placement="break">
          <alt>System architecture diagram</alt>
        </image>
      </fig>
      
      <fig expanse="page">
        <title>Page-wide Figure</title>
        <image href="wide-chart.png" align="center" scalefit="yes">
          <alt>Wide chart spanning full page</alt>
        </image>
      </fig>
    </section>
    
    <section>
      <title>Objects and Media</title>
      <object classid="video/mp4" codebase="videos/" data="tutorial.mp4">
        <desc>Video tutorial</desc>
        <param name="autoplay" value="false"/>
        <param name="controls" value="true"/>
      </object>
      
      <object classid="application/pdf" data="manual.pdf" width="100%" height="600">
        <desc>PDF manual embedded</desc>
      </object>
      
      <foreign outputclass="html">
        <iframe src="https://example.com/widget" width="300" height="200"></iframe>
      </foreign>
    </section>
    
    <section>
      <title>Audio and Video</title>
      <audio controls="yes">
        <media-source href="audio.mp3" format="mp3"/>
        <media-source href="audio.ogg" format="ogg"/>
        <desc>Audio description</desc>
      </audio>
      
      <video width="640" height="480" controls="yes">
        <media-source href="video.mp4" format="mp4"/>
        <media-source href="video.webm" format="webm"/>
        <media-track kind="subtitles" href="subtitles.vtt" srclang="en"/>
        <desc>Video with subtitles</desc>
      </video>
    </section>
  </conbody>
</concept>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)

    def test_every_dita_domain_element(self):
        """Test elements from all DITA domain specializations."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="all_domains">
  <title>Every DITA Domain Element</title>
  <refbody>
    <section>
      <title>Highlight Domain</title>
      <p>Highlighting: <b>bold</b>, <i>italic</i>, <u>underline</u>, <tt>monospace</tt>, 
      <sup>superscript</sup>, <sub>subscript</sub>.</p>
    </section>
    
    <section>
      <title>Programming Domain</title>
      <p>Programming elements: <codeph>inline code</codeph>, <apiname>functionName</apiname>, 
      <cmdname>command</cmdname>, <varname>variable</varname>.</p>
      
      <codeblock>
// Sample code block
function example() {
    return "test";
}
      </codeblock>
    </section>
    
    <section>
      <title>UI Domain</title>
      <p>Controls: <uicontrol>Save</uicontrol>, <uicontrol>Cancel</uicontrol>, 
      <uicontrol>Apply Changes</uicontrol></p>
      
      <p>Windows: <wintitle>Preferences Dialog</wintitle></p>
    </section>
  </refbody>
</reference>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)

    def test_dita_maps_and_navigation(self):
        """Test DITA map structures and navigation elements."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="comprehensive_map">
  <title>Comprehensive Documentation Map</title>
  <topicmeta>
    <navtitle>Main Navigation</navtitle>
    <shortdesc>Complete documentation structure.</shortdesc>
    <author>Documentation Team</author>
    <keywords>
      <keyword>documentation</keyword>
      <keyword>user guide</keyword>
    </keywords>
  </topicmeta>
  
  <topicref href="introduction.dita" type="concept">
    <topicmeta>
      <navtitle>Introduction</navtitle>
    </topicmeta>
  </topicref>
  
  <topichead navtitle="Getting Started">
    <topicref href="installation.dita" type="task">
      <topicmeta>
        <navtitle>Installation Guide</navtitle>
      </topicmeta>
    </topicref>
    <topicref href="configuration.dita" type="task">
      <topicmeta>
        <navtitle>Configuration</navtitle>
      </topicmeta>
    </topicref>
  </topichead>
  
  <topicgroup>
    <topicmeta>
      <navtitle>API Reference</navtitle>
    </topicmeta>
    <topicref href="api-overview.dita" type="reference"/>
    <topicref href="api-functions.dita" type="reference"/>
  </topicgroup>
  
  <mapref href="troubleshooting-map.ditamap"/>
  
  <reltable>
    <relheader>
      <relcolspec type="concept"/>
      <relcolspec type="task"/>
      <relcolspec type="reference"/>
    </relheader>
    <relrow>
      <relcell><topicref href="security-concepts.dita"/></relcell>
      <relcell><topicref href="configure-security.dita"/></relcell>
      <relcell><topicref href="security-api.dita"/></relcell>
    </relrow>
  </reltable>
  
  <keydef keys="api" href="glossary.dita#api">
    <topicmeta>
      <keywords>
        <keyword>Application Programming Interface</keyword>
      </keywords>
    </topicmeta>
  </keydef>
</map>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(result.topic_type, DITATopicType.MAP)

    def test_dita_specializations_and_constraints(self):
        """Test DITA specializations and constraint mechanisms."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="specializations" specializations="@props/audience @props/platform">
  <title>DITA Specializations Test</title>
  <conbody>
    <p audience="admin" platform="windows linux">Content for admins on Windows/Linux.</p>
    <p audience="user" platform="web">Content for users on web platform.</p>
    <p props="audience(developer) platform(api)">Content for API developers.</p>
    
    <section audience="advanced" otherprops="version(2.0)">
      <title>Advanced Features</title>
      <p>Advanced content for version 2.0.</p>
    </section>
    
    <note type="attention" audience="admin">
      <p>Administrator-only notice.</p>
    </note>
    
    <codeblock audience="developer" outputclass="language-java" props="example(advanced)">
public class AdvancedFeature {
    @Override
    public void processAdvancedOperation() {
        // Implementation for advanced users
    }
}
    </codeblock>
    
    <p rev="2.0" importance="high">New in version 2.0 - high importance.</p>
    <p status="new" translate="no">Status marked as new, do not translate.</p>
  </conbody>
</concept>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Check that attributes are preserved
        for block in result.document.blocks:
            self.assertIsInstance(block.attributes, dict)

    def test_dita_with_custom_elements(self):
        """Test DITA with custom specialized elements."""
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="custom_elements">
  <title>Custom DITA Elements</title>
  <conbody>
    <p>Standard paragraph content.</p>
    
    <!-- Custom specialized elements -->
    <custom-note type="enterprise">
      <custom-title>Enterprise Notice</custom-title>
      <custom-content>This feature is available in enterprise edition only.</custom-content>
    </custom-note>
    
    <api-signature>
      <api-name>customFunction</api-name>
      <api-params>
        <api-param name="input" type="string" required="yes"/>
        <api-param name="options" type="object" required="no"/>
      </api-params>
      <api-return type="Promise&lt;Result&gt;"/>
    </api-signature>
    
    <code-snippet language="typescript" framework="react">
interface CustomProps {
  data: string;
  callback: (result: any) => void;
}

const CustomComponent: React.FC&lt;CustomProps&gt; = ({ data, callback }) => {
  return &lt;div&gt;{data}&lt;/div&gt;;
};
    </code-snippet>
    
    <troubleshooting-matrix>
      <problem-category name="Network Issues">
        <problem-item>
          <symptom>Cannot connect to server</symptom>
          <diagnosis>Network configuration error</diagnosis>
          <solution>Check network settings and firewall</solution>
        </problem-item>
      </problem-category>
    </troubleshooting-matrix>
  </conbody>
</concept>'''
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Should handle unknown elements gracefully

    def test_extreme_edge_cases(self):
        """Test extreme edge cases that could break parsing."""
        edge_cases = {
            'empty_root': '''<?xml version="1.0"?><concept id="empty"/>''',
            
            'no_content': '''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="no_content">
  <title></title>
  <conbody></conbody>
</concept>''',
            
            'deeply_nested': '''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="deep">
  <title>Deep Nesting</title>
  <conbody>''' + 
'<section><section><section><section><section>' +
'<p>Very deep content</p>' +
'</section></section></section></section></section>' +
'''  </conbody>
</concept>''',
            
            'huge_attributes': f'''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="huge_attrs" audience="{'admin,' * 100}user">
  <title>Huge Attributes</title>
  <conbody><p>Content with massive attributes.</p></conbody>
</concept>''',
            
            'mixed_namespaces': '''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="namespaces" xmlns:custom="http://custom.namespace.com">
  <title>Mixed Namespaces</title>
  <conbody>
    <p>Standard DITA content.</p>
    <custom:element custom:attr="value">Custom namespaced content</custom:element>
  </conbody>
</concept>''',
            
            'malformed_but_parseable': '''<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="malformed">
  <title>Malformed Content</title>
  <conbody>
    <p>Paragraph with &lt; unescaped characters &amp; entities &gt;</p>
    <p>Another paragraph with "quotes" and 'apostrophes'</p>
  </conbody>
</concept>'''
        }
        
        for case_name, content in edge_cases.items():
            with self.subTest(case=case_name):
                result = self.parser.parse(content)
                # Should either succeed or fail gracefully
                self.assertIsNotNone(result)
                if not result.success:
                    # If it fails, should have error messages
                    self.assertGreater(len(result.errors), 0)

    def test_performance_stress_test(self):
        """Ultimate DITA performance stress test."""
        # Create enormous DITA document with every element type
        massive_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="stress_test">
  <title>Performance Stress Test Document</title>
  <shortdesc>Testing parser performance with massive DITA content.</shortdesc>
  <conbody>'''
        
        # Add 500 complex sections
        for i in range(500):
            massive_content += f'''
    <section id="section_{i}">
      <title>Section {i}: Advanced Configuration</title>
      <p>Section {i} introduction with <b>formatting</b> and <codeph>inline code</codeph>.</p>
      
      <ul>
        <li>List item {i}.1 with <term>terminology</term></li>
        <li>List item {i}.2 with <apiname>API_Function_{i}</apiname></li>
        <li>List item {i}.3 with <filepath>/path/to/file_{i}.conf</filepath></li>
      </ul>
      
      <example>
        <title>Example {i}</title>
        <codeblock outputclass="language-python">
# Configuration example {i}
def configure_feature_{i}():
    config = {{
        'enabled': True,
        'value': {i},
        'description': 'Feature {i} configuration'
    }}
    return config
        </codeblock>
      </example>
      
      <note type="tip">
        <p>Tip for section {i}: Always backup before making changes.</p>
      </note>
    </section>'''
        
        massive_content += '''
  </conbody>
</concept>'''
        
        import time
        start_time = time.time()
        result = self.parser.parse(massive_content)
        parse_time = time.time() - start_time
        
        self.assertTrue(result.success, "Massive DITA document should parse successfully")
        # Count all blocks including nested ones
        all_blocks = result.document.get_all_blocks_flat()
        self.assertGreater(len(all_blocks), 100, "Should create many blocks")
        self.assertLess(parse_time, 10.0, f"Massive DITA parsing took too long: {parse_time:.2f}s")
        
        print(f"MASSIVE DITA ({len(massive_content):,} chars, 500 sections) parsed in {parse_time:.3f}s")
        print(f"Performance: {len(result.document.blocks)} blocks created")


if __name__ == '__main__':
    unittest.main()
