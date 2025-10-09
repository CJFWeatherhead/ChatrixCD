# ChatrixCD Logo Files

## Logo Files Available

✅ **Logo files are now included!** This directory contains SVG logo files that are infinitely scalable and easy to manipulate programmatically.

### Included SVG Files

All logo files are provided in SVG (Scalable Vector Graphics) format:

- **logo-horizontal.svg** - Full horizontal logo for README and headers
- **logo-icon.svg** - Icon only for favicons and small spaces  
- **logo-stacked.svg** - Stacked layout for square/vertical spaces
- **logo-social.svg** - Social media preview with tagline
- **favicon.svg** - Browser favicon in modern SVG format

## Source Image

The original ChatrixCD branding image is available at:
https://github.com/user-attachments/assets/c6b68aa0-3f5b-4f55-9c61-8068085c4602

## Working with SVG Files

SVG files offer several advantages over raster formats:

### Advantages

- **Infinite Scalability**: Scale to any size without quality loss
- **Small File Size**: Typically smaller than equivalent PNG files
- **Easy Editing**: Modify colors, shapes, and text programmatically
- **Modern Support**: Supported by all modern browsers and tools

### Converting SVG to PNG (Optional)

If you need PNG versions for specific use cases, you can convert the SVG files:

#### Using Inkscape (Recommended)

```bash
# Install Inkscape if not already installed
# Ubuntu/Debian: sudo apt install inkscape
# macOS: brew install inkscape

# Convert horizontal logo to PNG
inkscape assets/logo-horizontal.svg --export-filename=assets/logo-horizontal.png --export-width=800

# Convert icon to PNG
inkscape assets/logo-icon.svg --export-filename=assets/logo-icon.png --export-width=512

# Convert social preview to PNG
inkscape assets/logo-social.svg --export-filename=assets/logo-social.png --export-width=1200

# Convert favicon to PNG
inkscape assets/favicon.svg --export-filename=assets/favicon.png --export-width=32
```

#### Using ImageMagick with rsvg

```bash
# Install ImageMagick with SVG support
# Ubuntu/Debian: sudo apt install imagemagick librsvg2-bin
# macOS: brew install imagemagick librsvg

# Convert SVG files to PNG
convert -density 300 assets/logo-horizontal.svg -resize 800x assets/logo-horizontal.png
convert -density 300 assets/logo-icon.svg -resize 512x512 assets/logo-icon.png
convert -density 300 assets/logo-social.svg -resize 1200x630 assets/logo-social.png
```

#### Using Online Tools

For quick conversions without installing software:
- [CloudConvert](https://cloudconvert.com/svg-to-png) - Online SVG to PNG converter
- [SVG to PNG Converter](https://svgtopng.com/) - Simple online tool

### Using the Logo Files

The logos are already integrated into the project:

✅ **README.md** - Uses `assets/logo-horizontal.svg`  
✅ **docs/index.md** - Uses `assets/logo-horizontal.svg`  
✅ **docs/_config.yml** - Configured with `favicon.svg`  
✅ **docs/assets/** - Contains copies of horizontal and icon logos

### Customizing the Logo

Since the logos are in SVG format, you can easily customize them:

#### Changing Colors

Edit the SVG files directly to change colors:

```xml
<!-- Change the robot color from #4A9B7F to another color -->
<rect ... fill="#4A9B7F"/> <!-- Change this hex color -->

<!-- Change text color from #FFFFFF to another color -->
<text ... fill="#FFFFFF">ChatrixCD</text> <!-- Change this hex color -->
```

#### Modifying Size

SVG files scale perfectly to any size. Just specify width or height in your HTML/Markdown:

```html
<!-- Small -->
<img src="assets/logo-horizontal.svg" width="300">

<!-- Medium -->
<img src="assets/logo-horizontal.svg" width="500">

<!-- Large -->
<img src="assets/logo-horizontal.svg" width="800">
```

### Configure GitHub Social Preview

To set the social preview image on GitHub:

1. Go to repository Settings
2. Scroll to "Social preview"  
3. If using SVG: Convert `assets/logo-social.svg` to PNG first (GitHub requires PNG/JPG)
4. Upload the PNG version
5. Save changes

### Testing the Logos

1. View locally by opening README.md in a browser or Markdown viewer
2. Test Jekyll site locally:
   ```bash
   cd docs
   jekyll serve
   # View at http://localhost:4000/ChatrixCD/
   ```
3. Verify all SVG images display correctly and scale properly

## Color Specifications

The logo uses these exact brand colors:

- **ChatrixCD Green**: `#4A9B7F` (RGB: 74, 155, 127)
- **Dark Background**: `#2D3238` (RGB: 45, 50, 56)
- **White Text**: `#FFFFFF` (RGB: 255, 255, 255)

## File Checklist

Logo files included in this repository:

- [x] `assets/logo-horizontal.svg` - Horizontal logo (SVG)
- [x] `assets/logo-icon.svg` - Icon only (SVG)
- [x] `assets/logo-stacked.svg` - Stacked layout (SVG)
- [x] `assets/logo-social.svg` - Social media preview (SVG)
- [x] `assets/favicon.svg` - Browser favicon (SVG)
- [x] `docs/assets/logo-horizontal.svg` - Copy for GitHub Pages
- [x] `docs/assets/logo-icon.svg` - Copy for GitHub Pages
- [x] `docs/favicon.svg` - Favicon for GitHub Pages
- [x] README.md updated with logo
- [x] docs/index.md updated with logo
- [x] docs/_config.yml configured with favicon

Optional (if PNG versions are needed):
- [ ] PNG versions of logos (use conversion commands above)
- [ ] GitHub social preview configured (requires PNG conversion)

## Questions?

For questions about logo implementation, refer to:
- [BRANDING.md](../BRANDING.md) - Complete branding guidelines
- [assets/README.md](README.md) - Asset directory documentation

Or open a GitHub discussion for help.
