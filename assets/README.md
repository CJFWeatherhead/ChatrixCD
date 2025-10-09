# ChatrixCD Assets

This directory contains branding assets for the ChatrixCD project.

## Logo Files

To add the logo files to this directory, save the ChatrixCD branding image in the following formats:

### Required Files

1. **logo-horizontal.png** (800 × 250px)
   - Full horizontal logo with icon and text
   - Primary usage for README and documentation headers
   - Dark background version

2. **logo-icon.png** (512 × 512px)
   - Icon only (robot chat bubble)
   - For favicons, social profiles, small spaces
   - Transparent or dark background

3. **logo-stacked.png** (500 × 600px)
   - Icon on top, text below
   - For square/vertical layouts
   - Dark background version

4. **logo-social.png** (1200 × 630px)
   - Social media preview image
   - Includes logo and tagline: "Matrix bot for CI/CD automation through chat"
   - Dark background with proper padding

5. **favicon.ico** (32 × 32px)
   - Browser favicon
   - Icon only version

### Source Image

The source branding image can be found at:
https://github.com/user-attachments/assets/c6b68aa0-3f5b-4f55-9c61-8068085c4602

### Creating Assets

To create these assets from the source image:

```bash
# Using ImageMagick (if available)
convert source-logo.png -resize 800x250 logo-horizontal.png
convert source-logo.png -resize 512x512 logo-icon.png
convert source-logo.png -resize 32x32 favicon.ico

# Or use any image editing software (GIMP, Photoshop, etc.)
```

### Color Specifications

- **ChatrixCD Green**: #4A9B7F (RGB: 74, 155, 127)
- **Dark Background**: #2D3238 (RGB: 45, 50, 56)
- **White Text**: #FFFFFF (RGB: 255, 255, 255)

## Usage

After adding the logo files, they can be referenced in markdown:

```markdown
![ChatrixCD Logo](assets/logo-horizontal.png)
```

Or in HTML:

```html
<img src="assets/logo-horizontal.png" alt="ChatrixCD Logo" width="400">
```

## Documentation

For complete branding guidelines, see [BRANDING.md](../BRANDING.md) in the root directory.

## GitHub Pages

Logo files should also be copied to `docs/assets/` for use in GitHub Pages documentation.
