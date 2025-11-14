# ChatrixCD Documentation

This directory contains the documentation for ChatrixCD, published at: https://chatrix.cd/

## Documentation Structure

The documentation is organized into the following pages:

- **`index.md`** - Home page with overview and quick links
- **`installation.md`** - Installation guide for all deployment methods
- **`quickstart.md`** - Quick start guide to get up and running
- **`configuration.md`** - Configuration reference with all options
- **`architecture.md`** - Architecture overview and technical details
- **`TUI.md`** - Text User Interface guide with features and screenshots
- **`contributing.md`** - Contributing guidelines for developers
- **`security.md`** - Security policy and best practices
- **`deployment.md`** - Deployment guide for various platforms
- **`support.md`** - Support resources and troubleshooting

## Building the Documentation Site

This site uses the [Just the Docs](https://just-the-docs.github.io/just-the-docs/) theme with GitHub Pages.

To preview locally:

```bash
# Install Jekyll dependencies (requires Ruby)
bundle install

# Serve the site locally
bundle exec jekyll serve

# Visit http://localhost:4000
```

## Documentation Guidelines

When updating documentation:

1. **Keep it in sync**: Ensure documentation aligns with the current codebase
2. **Update frontmatter**: Each page should have proper Jekyll frontmatter (layout, title, nav_order)
3. **Use relative links**: Link to other documentation pages using relative paths
4. **Test locally**: Preview changes locally before committing
5. **Update both locations**: Some docs exist in both root (e.g., README.md) and docs/ - keep them synchronized

## Theme Configuration

The site uses the Just the Docs theme configured in `_config.yml`:
- Modern, responsive design
- Built-in search functionality
- Mobile-friendly navigation
- Syntax highlighting for code blocks
