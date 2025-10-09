# ChatrixCD Documentation Assets

This directory contains branding assets for the ChatrixCD GitHub Pages documentation.

## Logo Files

Copy logo files from the main `assets/` directory to this location:

- `logo-horizontal.png` - Full horizontal logo
- `logo-icon.png` - Icon only

These files are used in:
- Site header/navigation
- Documentation home page
- README files in the docs directory

## Usage in Jekyll

Reference assets using the `baseurl` variable:

```liquid
{{ site.baseurl }}/assets/logo-horizontal.png
```

Or in markdown with relative paths:

```markdown
![ChatrixCD Logo](assets/logo-horizontal.png)
```

## Source

Assets should be copied from `/assets/` directory in the repository root.

See [BRANDING.md](../../BRANDING.md) for complete branding guidelines.
