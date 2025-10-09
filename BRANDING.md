# ChatrixCD Branding Guide

This document defines the visual identity and branding guidelines for the ChatrixCD project.

## Brand Identity

ChatrixCD is a Matrix bot that enables CI/CD automation through chat. Our branding reflects:
- **Automation**: Represented by the bot/robot icon
- **Communication**: Shown through the chat bubble design
- **Technical Excellence**: Clean, modern aesthetics
- **Approachability**: Friendly robot character

## Logo

### Primary Logo

The ChatrixCD logo consists of:
- **Icon**: A green robot head with a speech bubble, featuring an antenna
- **Logotype**: "ChatrixCD" in white, modern sans-serif typeface

**Usage**: The full logo (icon + text) should be used in most contexts.

### Logo Variations

1. **Full Logo (Horizontal)**: Icon on the left, text on the right - primary usage
2. **Icon Only**: For small spaces, favicons, or when context is clear
3. **Stacked Logo**: Icon on top, text below - for square/vertical layouts

### Logo Files

Logo files are located in the `assets/` directory:
- `logo-horizontal.svg` - Full horizontal logo (default) - SVG format for scalability
- `logo-icon.svg` - Icon only - SVG format
- `logo-stacked.svg` - Stacked layout - SVG format
- `logo-social.svg` - Social media preview (1200x630px) - SVG format
- `favicon.svg` - Favicon for web pages - SVG format

**Note**: All logos are provided in SVG format for perfect scalability and easy programmatic manipulation. PNG versions can be generated from SVG as needed for specific use cases.

## Color Palette

### Primary Colors

- **ChatrixCD Green**: `#4A9B7F` (RGB: 74, 155, 127)
  - Used for: Logo icon, primary buttons, accents, links
  - Represents: Growth, automation, reliability

- **White**: `#FFFFFF` (RGB: 255, 255, 255)
  - Used for: Logo text, primary text on dark backgrounds
  - Represents: Clarity, simplicity

### Secondary Colors

- **Dark Background**: `#2D3238` (RGB: 45, 50, 56)
  - Used for: Backgrounds, containers, header areas
  - Represents: Professionalism, focus

- **Light Background**: `#F6F8FA` (RGB: 246, 248, 250)
  - Used for: Light theme backgrounds, alternating sections
  - Represents: Openness, accessibility

### Accent Colors

- **Success Green**: `#28A745` (RGB: 40, 167, 69)
  - Used for: Success messages, completed tasks
  
- **Warning Yellow**: `#FFC107` (RGB: 255, 193, 7)
  - Used for: Warnings, in-progress tasks

- **Error Red**: `#DC3545` (RGB: 220, 53, 69)
  - Used for: Errors, failed tasks

- **Info Blue**: `#17A2B8` (RGB: 23, 162, 184)
  - Used for: Information messages, tips

## Typography

### Primary Font

- **Headings**: Sans-serif (system font stack)
  - `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
  - Bold weights for emphasis

- **Body Text**: Sans-serif (system font stack)
  - Regular weight for readability
  - Line height: 1.6 for optimal reading

### Code Font

- **Code Blocks**: Monospace (system font stack)
  - `"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace`

## Logo Usage Guidelines

### Do's ✅

- Use the logo on a dark background for maximum contrast
- Maintain adequate clear space around the logo (minimum 20% of logo height)
- Scale the logo proportionally
- Use the provided color values
- Ensure the logo is clearly visible and readable

### Don'ts ❌

- Don't change the logo colors (except for approved variations)
- Don't distort or skew the logo
- Don't add effects (shadows, gradients, etc.) to the logo
- Don't place the logo on busy backgrounds
- Don't recreate or modify the logo artwork

### Minimum Size

- **Full Logo**: 200px width minimum
- **Icon Only**: 32px × 32px minimum

## Brand Voice

When writing content for ChatrixCD:

- **Clear**: Use simple, straightforward language
- **Technical but Approachable**: Balance technical accuracy with accessibility
- **Helpful**: Focus on solving user problems
- **Professional**: Maintain a professional tone while being friendly

## Application in Documentation

### README Files

- Include the full horizontal logo at the top
- Use brand colors for section headers (with emoji icons)
- Maintain consistent formatting

### GitHub Pages

- Logo in the site header/navigation
- Use the dark color scheme with ChatrixCD Green accents
- Consistent use of emoji icons for visual interest

### Code Comments

- Use clear, descriptive comments
- Follow PEP 8 style guide
- No branding needed in code comments

## Social Media

### GitHub Social Preview

- Image size: 1200 × 630 pixels
- Logo prominently displayed on dark background
- Project tagline included

### Profile Images

- Use icon-only logo
- Ensure visibility at small sizes (48 × 48 pixels)

## Examples

### Markdown Header with Branding

```markdown
<div align="center">
  <img src="assets/logo-horizontal.png" alt="ChatrixCD Logo" width="400">
  
  # ChatrixCD
  
  **Matrix bot for CI/CD automation through chat**
  
  [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
</div>
```

### Badges

Use shields.io badges with brand colors:
- Color: `4A9B7F` (ChatrixCD Green)
- Label color: `2D3238` (Dark Background)

## Assets Checklist

To fully implement the branding, add the following assets:

- [ ] `assets/logo-horizontal.png` - Full horizontal logo (800 × 250px recommended)
- [ ] `assets/logo-icon.png` - Icon only (512 × 512px)
- [ ] `assets/logo-stacked.png` - Stacked layout (500 × 600px)
- [ ] `assets/logo-social.png` - Social media preview (1200 × 630px)
- [ ] `assets/favicon.ico` - Browser favicon (32 × 32px)
- [ ] `docs/assets/logo-horizontal.png` - Copy for GitHub Pages
- [ ] `docs/assets/logo-icon.png` - Copy for GitHub Pages

## Brand Evolution

This branding guide may be updated over time. Major changes will be:
- Documented in CHANGELOG.md
- Announced to contributors
- Implemented gradually to avoid breaking existing usage

## Questions?

For questions about branding usage, please:
- Open a discussion on GitHub
- Reference this guide when proposing visual changes
- Consult with maintainers for major branding decisions

---

*ChatrixCD Branding Guide v1.0*
