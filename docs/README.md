# ChatrixCD Documentation

This directory contains the documentation for ChatrixCD, which is published to GitHub Pages.

## Documentation Site

The documentation is available at: https://cjfweatherhead.github.io/ChatrixCD/

## Local Development

To preview the documentation locally with Jekyll:

```bash
# Install Ruby and Jekyll
gem install bundler jekyll

# Serve the documentation
cd docs
jekyll serve

# View at http://localhost:4000/ChatrixCD/
```

## Documentation Structure

- `index.md` - Home page
- `installation.md` - Installation guide
- `quickstart.md` - Quick start guide
- `configuration.md` - Configuration reference
- `architecture.md` - Architecture overview
- `contributing.md` - Contributing guidelines
- `security.md` - Security policy
- `deployment.md` - Deployment guide
- `support.md` - Support and troubleshooting
- `_config.yml` - Jekyll configuration

## Adding New Pages

1. Create a new `.md` file in the `docs/` directory
2. Add front matter with title and nav_order:
   ```yaml
   ---
   layout: default
   title: Your Page Title
   nav_order: 10
   ---
   ```
3. Write your content in Markdown
4. Commit and push - GitHub Actions will automatically deploy

## Theme

This site uses the [Just the Docs](https://just-the-docs.github.io/just-the-docs/) theme with the Cayman fallback.

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the `main` branch via the `.github/workflows/pages.yml` workflow.
