# Style Guide AI Documentation

This directory contains the complete documentation for the Style Guide AI project, built with [Antora](https://antora.org/) and deployed to GitHub Pages.

## Documentation Structure

The documentation is organized into three main sections:

- **Architecture**: Complete system architecture and design documentation
- **How-to Guides**: Step-by-step guides for extending and customizing the system
- **API Reference**: Complete API documentation for REST and WebSocket interfaces

## Building the Documentation

### Prerequisites

- Node.js 18 or higher
- npm (comes with Node.js)

### Local Development

1. **Install dependencies**:
   ```bash
   cd docs
   npm install
   ```

2. **Build the documentation**:
   ```bash
   npx antora --fetch antora-playbook.yml
   ```

3. **Serve locally**:
   ```bash
   npx http-server dist -p 8080
   ```

4. **Open in browser**:
   ```
   http://localhost:8080
   ```

### Live Reload (Optional)

For development with live reload:

```bash
# Install live-server globally
npm install -g live-server

# Build and serve with live reload
npx antora --fetch antora-playbook.yml && live-server dist
```

## GitHub Pages Deployment

The documentation is automatically deployed to GitHub Pages via GitHub Actions when changes are pushed to the `main` branch.

### Deployment Process

1. **Trigger**: Push to `main` branch or changes to `docs/**` files
2. **Build**: GitHub Actions runs Antora to build the site
3. **Deploy**: Built site is deployed to GitHub Pages
4. **Access**: Available at `https://your-username.github.io/style-guide-ai`

### Manual Deployment

To manually trigger deployment:

1. Go to the **Actions** tab in your GitHub repository
2. Select **Deploy Documentation to GitHub Pages**
3. Click **Run workflow**

## Mermaid Diagrams

The documentation supports Mermaid diagrams for visualizing architecture and workflows:

### Usage

```asciidoc
[mermaid]
----
graph TD
    A[Start] --> B[Process]
    B --> C[End]
----
```

### Supported Diagram Types

- **Flowcharts**: System architecture and process flows
- **Sequence Diagrams**: API interactions and component communication
- **Class Diagrams**: Object relationships and inheritance
- **State Diagrams**: System states and transitions
- **Git Graphs**: Development workflows

## Content Organization

### Module Structure

```
docs/
├── antora-playbook.yml          # Antora configuration
├── docs/
│   ├── antora.yml              # Component configuration
│   └── modules/
│       ├── ROOT/               # Main documentation
│       │   ├── nav.adoc        # Navigation
│       │   └── pages/          # Content pages
│       ├── architecture/       # Architecture documentation
│       │   ├── nav.adoc        # Architecture navigation
│       │   └── pages/          # Architecture pages
│       └── how-to/            # How-to guides
│           ├── nav.adoc        # How-to navigation
│           └── pages/          # How-to pages
└── package.json               # Node.js dependencies
```

### Adding New Content

#### 1. Add a New Page

Create a new `.adoc` file in the appropriate module's `pages/` directory:

```asciidoc
= Page Title
:page-layout: doc

== Section

Content goes here...
```

#### 2. Update Navigation

Add the page to the relevant `nav.adoc` file:

```asciidoc
* xref:new-page.adoc[New Page Title]
```

#### 3. Add Cross-References

Reference other pages using `xref`:

```asciidoc
For more information, see xref:architecture:architecture.adoc[System Architecture].
```

### Content Guidelines

#### AsciiDoc Syntax

- Use `=` for page titles
- Use `==` for major sections
- Use `===` for subsections
- Use `****` for admonitions
- Use `----` for code blocks

#### Code Examples

```asciidoc
[source,python]
----
def example_function():
    return "Hello, World!"
----
```

#### Admonitions

```asciidoc
WARNING: This is a warning message.

NOTE: This is a note.

TIP: This is a tip.
```

## Customization

### UI Customization

Custom UI elements are in `antora-lunr-ui/`:

- `partials/head-meta.hbs`: Custom head elements (Mermaid support)
- `css/`: Custom CSS styles
- `partials/`: Custom partial templates

### Antora Configuration

Edit `antora-playbook.yml` to customize:

- Site title and URL
- Content sources
- UI bundle
- Extensions and plugins
- Output directory

## Troubleshooting

### Common Issues

**Build fails with "Module not found"**:
```bash
npm install
rm -rf node_modules package-lock.json
npm install
```

**Mermaid diagrams not rendering**:
- Check syntax in the AsciiDoc source
- Verify the Mermaid CDN is accessible
- Check browser console for JavaScript errors

**Navigation not updating**:
- Verify `nav.adoc` file syntax
- Check that `antora.yml` references the correct navigation files
- Rebuild the documentation

**Cross-references broken**:
- Verify the target page exists
- Check the module and page name in the `xref`
- Ensure the reference follows the correct format

### Debug Mode

Run Antora with debug output:

```bash
npx antora --fetch --log-level=debug antora-playbook.yml
```

## Contributing

### Documentation Standards

1. **Use clear, concise language**
2. **Include code examples for all procedures**
3. **Add diagrams for complex concepts**
4. **Test all links and cross-references**
5. **Follow the existing structure and style**

### Review Process

1. Create a feature branch
2. Make documentation changes
3. Test locally with `npx antora --fetch antora-playbook.yml`
4. Submit a pull request
5. Wait for review and automated checks

## Support

For help with the documentation:

- **Build Issues**: Check the GitHub Actions logs
- **Content Issues**: Review the AsciiDoc syntax guide
- **Antora Questions**: See the [Antora documentation](https://docs.antora.org/)
- **Mermaid Issues**: Check the [Mermaid documentation](https://mermaid.js.org/)

## License

This documentation is part of the Style Guide AI project and follows the same license terms.
