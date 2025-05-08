# Gemini PC Control Documentation Site

This directory contains the source files for the Gemini PC Control documentation site, 
which is built and hosted using GitHub Pages.

## Overview

The documentation site uses:
- GitHub Pages with the Jekyll static site generator
- Material Design styling with custom CSS
- SVG graphics for illustrations

## File Structure

- `index.html` - Main landing page
- `getting-started.html` - Getting started guide
- `assets/` - Contains CSS, JavaScript, and favicons
- `images/` - Contains SVG illustrations and diagrams
- `_config.yml` - Jekyll configuration file
- `CNAME` - Custom domain configuration

## Local Development

To run this site locally for development:

1. Install Jekyll and its dependencies:
   ```
   gem install jekyll bundler
   ```

2. Navigate to the `docs` directory:
   ```
   cd docs
   ```

3. Install dependencies:
   ```
   bundle install
   ```

4. Start the Jekyll server:
   ```
   bundle exec jekyll serve
   ```

5. Visit `http://localhost:4000` in your browser

## Adding Content

- Add new pages as HTML files in the root of the `docs` directory
- Add new assets to the appropriate subdirectories
- Update the navigation links in the header and footer of all pages

## Deployment

The site is automatically deployed when changes are pushed to the `master` branch.
GitHub Pages is configured to use the `/docs` folder on the `master` branch as the publishing source.

## Notes for Contributors

- Keep the Material Design styling consistent
- Use SVG for graphics where possible
- Test all changes locally before pushing to the repository
- Ensure all links work correctly
- Keep content up-to-date with the main application 