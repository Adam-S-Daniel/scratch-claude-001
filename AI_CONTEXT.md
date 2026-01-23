# AI Assistant Context for Retro Games Arcade

## Project Overview
This is a retro-themed arcade website hosting multiple browser-based games with a nostalgic aesthetic. The site features a landing page that serves as a game selection menu.

## Project Structure
```
/
├── index.html              # Landing page with game selection menu
├── astro-warrior.html      # Space shooter game
├── ham-hock.html          # Ham hock design simulation game
├── styles.css             # Shared stylesheet (if used)
├── test-scrolling.html    # Test suite for scrolling functionality
└── .github/
    └── workflows/
        └── deploy.yml     # GitHub Actions deployment workflow
```

## Design Philosophy

### Visual Style
- **Theme**: 1980s retro arcade aesthetic with neon colors
- **Color Palette**: Cyan (#0ff), Magenta (#f0f), Yellow (#ff0), Purple gradients
- **Typography**: Monospace fonts (Courier New)
- **Effects**: Glowing text, animated stars, hover animations

### Code Style
- Self-contained HTML files with embedded CSS and JavaScript
- No external dependencies or frameworks
- Mobile-responsive using CSS Grid and Flexbox
- Inline styles for simplicity and portability

## Critical Implementation Details

### Scrolling Behavior
**IMPORTANT**: The landing page (`index.html`) must allow scrolling:
- **DO NOT** use `overflow: hidden` on the body element
- **USE** `align-items: flex-start` (not `center`) to prevent content cutoff
- **USE** `min-height: 100vh` (not fixed `height`) to allow expansion
- **INCLUDE** padding on body for proper spacing

Example of correct body styles:
```css
body {
    display: flex;
    justify-content: center;
    align-items: flex-start;  /* NOT center */
    min-height: 100vh;
    padding: 40px 20px;
    /* overflow: hidden; <- NEVER add this */
}
```

### Game Pages
- Individual game HTML files are self-contained
- Each game may have `overflow: hidden` on body if needed (for game canvas)
- Games should include mobile touch controls where applicable

## Testing

### Test Files
- `test-scrolling.html`: Automated tests for scrolling functionality
  - Verifies absence of `overflow: hidden` on body
  - Checks for proper flexbox alignment
  - Tests scrolling behavior
  - Can be opened directly in a browser

### Running Tests
1. Open `test-scrolling.html` in a web browser
2. Review automated test results
3. Manually verify scrolling in the embedded iframe

## Deployment

### GitHub Actions
- Workflow: `.github/workflows/deploy.yml`
- Triggers: On every push to any branch
- Target: GitHub Pages
- Build: No build step, deploys static files directly

### GitHub Pages
- URL: https://adam-s-daniel.github.io/scratch-claude-001/
- Serves all HTML files directly from repository root
- Deployment takes ~1-2 minutes after push

## Development Workflow

### Making Changes
1. Edit files locally
2. Test changes locally by opening HTML files in browser
3. Commit changes with descriptive messages
4. Push to feature branch (format: `claude/*` or similar)
5. Verify GitHub Actions deployment succeeds
6. Test on live GitHub Pages site

### Branch Naming
- Feature branches should start with `claude/` for AI assistant work
- Example: `claude/enable-landing-scroll-VllP7`

## Common Tasks

### Adding a New Game
1. Create new HTML file (e.g., `new-game.html`)
2. Add game card to `index.html` in the `.games-grid` section
3. Follow existing game card pattern with icon, title, description, tags
4. Test scrolling still works on landing page
5. Ensure mobile responsiveness

### Modifying Styles
- Keep inline styles within each HTML file for portability
- Maintain consistent color palette and retro aesthetic
- Test on mobile viewports (check `@media` queries)
- Verify animations work smoothly

### Debugging Layout Issues
1. Check browser console for errors
2. Verify CSS doesn't have conflicting overflow properties
3. Test in multiple browsers (Chrome, Firefox, Safari)
4. Check mobile viewport using browser dev tools
5. Run `test-scrolling.html` to verify expected behavior

## Key Principles for AI Assistants

1. **Preserve Scrolling**: Never add `overflow: hidden` to body of `index.html`
2. **Test After Changes**: Always test both locally and on GitHub Pages
3. **Maintain Aesthetic**: Keep retro/neon theme consistent
4. **Self-Contained Files**: Avoid external dependencies
5. **Mobile-First**: Ensure all features work on touch devices
6. **Document Tests**: Add new tests when adding new features
7. **Multiple Iterations**: Expect push-test cycles; iterate until correct

## Resources

- GitHub Repository: https://github.com/Adam-S-Daniel/scratch-claude-001
- Live Site: https://adam-s-daniel.github.io/scratch-claude-001/
- Actions: https://github.com/Adam-S-Daniel/scratch-claude-001/actions

## Recent Changes

### 2026-01-23: Enable Landing Page Scrolling
- **Problem**: Landing page had `overflow: hidden` preventing scrolling
- **Solution**: Removed `overflow: hidden`, changed to `align-items: flex-start`, added padding
- **Files Modified**: `index.html`
- **Tests Added**: `test-scrolling.html`
- **Commit**: a96e901cf7e06f7f839f7eeac0256d0c8d316b48
