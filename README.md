# GitHub Pages Automated Deployment

This repository contains a modern, responsive website with automated deployment to GitHub Pages using GitHub Actions.

## Features

- **Automated Deployment**: Push to your branch and GitHub Actions automatically deploys to GitHub Pages
- **Responsive Design**: Mobile-friendly layout that works on all devices
- **Modern UI**: Clean, professional design with gradient backgrounds and smooth animations
- **Easy to Customize**: Simple HTML and CSS structure ready for your content

## Quick Start

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on **Settings** > **Pages**
3. Under "Build and deployment":
   - Source: Select **GitHub Actions**
4. Save the settings

### 2. Make Changes

Edit the files to customize your site:

- `index.html` - Main content and structure
- `styles.css` - Styling and appearance
- Add more pages as needed

### 3. Deploy

Simply push your changes to the branch:

```bash
git add .
git commit -m "Update website content"
git push
```

The GitHub Actions workflow will automatically build and deploy your site.

### 4. View Your Site

After deployment completes (usually 1-2 minutes), visit:
```
https://[your-username].github.io/[repository-name]/
```

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── index.html                  # Main HTML file
├── styles.css                  # CSS styles
└── README.md                   # This file
```

## GitHub Actions Workflow

The workflow (`.github/workflows/deploy.yml`) automatically:

1. Triggers on push to main, master, or the current branch
2. Checks out your code
3. Configures GitHub Pages
4. Uploads the site as an artifact
5. Deploys to GitHub Pages

You can also trigger deployment manually from the Actions tab.

## Customization Guide

### Changing Colors

Edit the CSS variables in `styles.css`:

```css
:root {
    --primary-color: #6366f1;
    --secondary-color: #8b5cf6;
    --text-color: #1f2937;
    /* ... more variables */
}
```

### Adding New Pages

1. Create a new HTML file (e.g., `about.html`)
2. Link to it from `index.html`:
   ```html
   <a href="about.html">About</a>
   ```

### Adding Images

1. Create an `images` folder
2. Add your images
3. Reference them in HTML:
   ```html
   <img src="images/your-image.jpg" alt="Description">
   ```

## Troubleshooting

### Site not updating?

- Check the Actions tab for workflow run status
- Ensure GitHub Pages is enabled in repository settings
- Clear your browser cache

### 404 Error?

- Verify the GitHub Pages source is set to "GitHub Actions"
- Check that `index.html` exists in the repository root
- Wait a few minutes for DNS propagation

## Resources

- [GitHub Pages Documentation](https://docs.github.com/pages)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [HTML Reference](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [CSS Reference](https://developer.mozilla.org/en-US/docs/Web/CSS)

## License

This project is open source and available under the MIT License.
