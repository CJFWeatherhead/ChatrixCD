# Adding Logo Images to ChatrixCD

This guide explains how to add the actual logo image files to the ChatrixCD project.

## Source Image

The ChatrixCD branding image is available at:
https://github.com/user-attachments/assets/c6b68aa0-3f5b-4f55-9c61-8068085c4602

## Steps to Add Logo Files

### 1. Download the Source Image

Download the branding image from the URL above and save it as `source-logo.png` in a temporary location.

### 2. Create Required Logo Variations

Using an image editor (GIMP, Photoshop, ImageMagick, etc.), create the following variations:

#### a. Horizontal Logo (800 × 250px)
- Full logo with icon and "ChatrixCD" text
- Save as: `assets/logo-horizontal.png`
- Format: PNG with transparency or dark background
- Used in: README.md, documentation headers

#### b. Icon Only (512 × 512px)
- Just the robot chat bubble icon
- Save as: `assets/logo-icon.png`
- Format: PNG with transparency
- Used in: Favicons, small spaces, social profiles

#### c. Stacked Logo (500 × 600px)
- Icon on top, text below
- Save as: `assets/logo-stacked.png`
- Format: PNG with transparency or dark background
- Used in: Square/vertical layouts

#### d. Social Media Preview (1200 × 630px)
- Full logo with tagline: "Matrix bot for CI/CD automation through chat"
- Save as: `assets/logo-social.png`
- Format: PNG, dark background
- Used in: GitHub social preview, social media sharing

#### e. Favicon (32 × 32px)
- Icon only, small size
- Save as: `assets/favicon.ico`
- Format: ICO file
- Used in: Browser tab icon

### 3. Using ImageMagick (Command Line)

If you have ImageMagick installed, you can use these commands:

```bash
# Navigate to assets directory
cd assets

# Create horizontal logo (adjust size as needed)
convert source-logo.png -resize 800x250 logo-horizontal.png

# Create icon only
convert source-logo.png -resize 512x512 logo-icon.png

# Create favicon
convert source-logo.png -resize 32x32 favicon.ico

# For stacked and social versions, use an image editor for best results
```

### 4. Copy to Documentation Directory

After creating the logo files in `assets/`, copy the needed files to the docs directory:

```bash
cp assets/logo-horizontal.png docs/assets/
cp assets/logo-icon.png docs/assets/
```

### 5. Update Markdown Files

Once the logo files are added, uncomment the logo references in:

#### In `README.md`:
```markdown
<!-- Change this: -->
<!-- ![ChatrixCD Logo](assets/logo-horizontal.png) -->

<!-- To this: -->
![ChatrixCD Logo](assets/logo-horizontal.png)
```

#### In `docs/index.md`:
```markdown
<!-- Change this: -->
<!-- <img src="assets/logo-horizontal.png" alt="ChatrixCD Logo" width="400"> -->

<!-- To this: -->
<img src="assets/logo-horizontal.png" alt="ChatrixCD Logo" width="400">
```

### 6. Add Favicon to Documentation

Create a `docs/favicon.ico` by copying `assets/favicon.ico`:

```bash
cp assets/favicon.ico docs/
```

Then add to `docs/_config.yml`:

```yaml
# Add favicon
favicon_ico: "/ChatrixCD/favicon.ico"
```

### 7. Configure GitHub Social Preview

To set the social preview image on GitHub:

1. Go to repository Settings
2. Scroll to "Social preview"
3. Upload `assets/logo-social.png`
4. Save changes

### 8. Test and Commit

1. Test locally by viewing README.md and running Jekyll:
   ```bash
   cd docs
   jekyll serve
   # View at http://localhost:4000/ChatrixCD/
   ```

2. Verify all images display correctly

3. Commit the changes:
   ```bash
   git add assets/ docs/assets/ README.md docs/index.md
   git commit -m "Add logo images and update documentation"
   git push
   ```

## Color Specifications

When creating logo variations, use these exact colors:

- **ChatrixCD Green**: `#4A9B7F` (RGB: 74, 155, 127)
- **Dark Background**: `#2D3238` (RGB: 45, 50, 56)
- **White Text**: `#FFFFFF` (RGB: 255, 255, 255)

## File Checklist

After completing these steps, you should have:

- [ ] `assets/logo-horizontal.png` (800 × 250px)
- [ ] `assets/logo-icon.png` (512 × 512px)
- [ ] `assets/logo-stacked.png` (500 × 600px)
- [ ] `assets/logo-social.png` (1200 × 630px)
- [ ] `assets/favicon.ico` (32 × 32px)
- [ ] `docs/assets/logo-horizontal.png` (copy)
- [ ] `docs/assets/logo-icon.png` (copy)
- [ ] `docs/favicon.ico` (copy)
- [ ] Updated README.md with visible logo
- [ ] Updated docs/index.md with visible logo
- [ ] GitHub social preview configured

## Questions?

For questions about logo implementation, refer to:
- [BRANDING.md](../BRANDING.md) - Complete branding guidelines
- [assets/README.md](README.md) - Asset directory documentation

Or open a GitHub discussion for help.
