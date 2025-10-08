# GitHub Pages Setup Instructions

This guide explains how to enable and configure GitHub Pages for ChatrixCD.

## Prerequisites

- Repository must be public (or GitHub Pro/Team for private repos)
- Admin access to the repository

## Enable GitHub Pages

### Step 1: Configure GitHub Pages Settings

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar under "Code and automation")
4. Under **Source**, select:
   - Source: **GitHub Actions**

That's it! The workflow is already configured.

### Step 2: Verify Workflow

1. Go to **Actions** tab in your repository
2. You should see "Deploy GitHub Pages" workflow
3. If not triggered automatically, you can manually trigger it:
   - Click on "Deploy GitHub Pages" workflow
   - Click "Run workflow" button
   - Select the `main` branch
   - Click "Run workflow"

### Step 3: Wait for Deployment

1. The workflow will:
   - Build the documentation with Jekyll
   - Deploy to GitHub Pages
   - This takes about 1-2 minutes

2. Once completed, your documentation will be available at:
   ```
   https://cjfweatherhead.github.io/ChatrixCD/
   ```

## Automatic Updates

The documentation will automatically update when:
- Changes are pushed to `main` branch
- Changes are made to any file in the `docs/` directory
- Changes are made to `.github/workflows/pages.yml`

You can also manually trigger deployment:
- Go to Actions → Deploy GitHub Pages
- Click "Run workflow"

## Workflow Configuration

The workflow file is located at: `.github/workflows/pages.yml`

Key features:
- **Automatic deployment** on push to main
- **Manual triggering** via workflow_dispatch
- **Jekyll build** with Just the Docs theme
- **Artifact upload** for Pages deployment
- **Concurrency control** to prevent conflicting deployments

## Theme and Customization

The site uses:
- **Primary Theme**: Just the Docs (modern, searchable documentation theme)
- **Fallback Theme**: Cayman (GitHub's native theme)
- **Configuration**: `docs/_config.yml`

### Customize Theme

Edit `docs/_config.yml` to customize:
- Site title and description
- Color scheme (light/dark)
- Search functionality
- Navigation
- Footer content

### Customize Content

Add or edit markdown files in `docs/`:
1. Create new `.md` file
2. Add front matter:
   ```yaml
   ---
   layout: default
   title: Page Title
   nav_order: 10
   ---
   ```
3. Write content in Markdown
4. Commit and push

## Troubleshooting

### Pages Not Deploying

1. **Check workflow status**: Actions tab → Deploy GitHub Pages
2. **Check workflow logs**: Click on failed workflow → View logs
3. **Verify Pages settings**: Settings → Pages → Source = "GitHub Actions"
4. **Check permissions**: Workflow needs `pages: write` and `id-token: write`

### 404 Error on Pages

1. **Wait a few minutes**: Deployment can take time
2. **Check URL format**: Should be `https://username.github.io/repository/`
3. **Verify baseurl**: In `_config.yml`, check `baseurl: /ChatrixCD`

### Workflow Fails

Common issues:
1. **Permissions**: Ensure Actions have correct permissions
2. **Branch protection**: Check if branch protection blocks deployments
3. **Jekyll errors**: Check syntax in markdown files
4. **Invalid YAML**: Verify `_config.yml` syntax

### Custom Domain (Optional)

To use a custom domain:
1. Add a `CNAME` file in `docs/` directory:
   ```
   docs.example.com
   ```
2. Configure DNS:
   - Add CNAME record pointing to `cjfweatherhead.github.io`
3. In Settings → Pages:
   - Enter custom domain
   - Wait for DNS check
   - Enable HTTPS

## Security Notes

- Pages are public by default (even for private repos)
- Don't include sensitive information in docs
- All commits are visible in repository history
- Use separate branch for sensitive documentation if needed

## Support

If you encounter issues:
- Check [GitHub Pages documentation](https://docs.github.com/en/pages)
- Review [Actions documentation](https://docs.github.com/en/actions)
- Open an issue in the repository
- Check workflow logs for specific errors

## Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Just the Docs Theme](https://just-the-docs.github.io/just-the-docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
