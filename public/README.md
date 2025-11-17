# TopClanker - AI Agent Rankings

No-bullshit rankings of AI agents. Built scrappy, not crappy.

## Quick Start

### 1. Deploy to Netlify (5 minutes)

**Option A: Drag & Drop (Fastest)**
1. Go to [Netlify Drop](https://app.netlify.com/drop)
2. Drag the entire `topclanker` folder onto the page
3. Done. You'll get a URL like `random-name-123.netlify.app`
4. Go to Site Settings → Domain Management → Add custom domain → `topclanker.com`

**Option B: Git Deploy (Better for updates)**
1. Create a new repo on GitHub
2. Push this code:
   ```bash
   cd topclanker
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```
3. Go to [Netlify](https://app.netlify.com)
4. New site from Git → Choose your repo
5. Build settings: Leave blank (it's static HTML)
6. Deploy

### 2. Point Your Domain

In your domain registrar (where you bought topclanker.com):

**DNS Settings:**
- Add A record: `@` → `75.2.60.5`
- Add CNAME: `www` → `your-site.netlify.app`

OR use Netlify DNS (easier):
- Netlify dashboard → Domain Settings → Use Netlify DNS
- Copy the nameservers
- Update nameservers in your domain registrar
- Add custom domain in Netlify

**Note:** DNS changes take 1-24 hours to propagate.

## Updating Rankings

### The Fast Way (Manual)
Edit `data.json` and push/redeploy:

```json
{
  "lastUpdated": "2024-11-16",
  "agents": [
    {
      "rank": 1,
      "name": "Agent Name",
      "category": "reasoning",  // reasoning, math, research, learning
      "type": "open-source",    // open-source or closed
      "privacy": "high",        // high, medium, low
      "score": 98,
      "link": "https://example.com",
      "description": "Short description"
    }
  ]
}
```

If using Netlify Git deploy: Just commit and push. Auto-deploys in ~30 seconds.

If using Netlify Drop: Re-drag the folder to redeploy.

## Cursor Setup for This Project

You're already using Cursor Pro - perfect. Here's how to maximize it:

### Current Setup (v1 - Static Site)
- Works perfectly as-is
- No special Cursor config needed
- Just edit files and deploy

### Future Setup (When Scaling)

**When you want a CMS/Database:**
1. Create `.cursorrules` file in project root:
```
This is TopClanker - AI agent rankings site.

Stack:
- Frontend: HTML/CSS/JS (considering React/Next.js)
- Backend: TBD (considering Supabase or Firebase)
- Deploy: Netlify

Code standards:
- No code smells
- Modular, composable functions
- DevOps best practices
- Clean commits

When suggesting changes:
- Maintain current architecture
- Prioritize speed and simplicity
- Keep data.json as source of truth until we migrate to DB
```

2. Enable Cursor Features:
   - Cmd/Ctrl + K for inline editing
   - Cmd/Ctrl + L for chat with codebase context
   - Use Composer (Cmd/Ctrl + I) for multi-file edits

**Recommended Cursor Extensions (when you need them):**
- ESLint (code quality)
- Prettier (formatting)
- Tailwind CSS IntelliSense (when coding)

### IDE Workflow Tips
```bash
# In Cursor terminal:
# Test locally
python3 -m http.server 8000
# Visit http://localhost:8000

# When ready to deploy
git add .
git commit -m "Update rankings"
git push
```

## Adding Google AdSense

1. Sign up at [Google AdSense](https://www.google.com/adsense)
2. Get your publisher ID
3. Add this to `<head>` in `index.html`:
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"
     crossorigin="anonymous"></script>
```
4. Replace the ad placeholder divs with actual ad units from AdSense dashboard

## Project Structure

```
topclanker/
├── index.html      # Main page structure
├── style.css       # Custom styles
├── app.js          # All JavaScript logic
├── data.json       # Rankings data (edit this to update)
└── README.md       # This file
```

## Roadmap / Future Features

### Phase 1 (Current) ✓
- Static site with manual rankings
- Basic filtering
- Responsive design

### Phase 2 (Next)
- Add blog section (consider Markdown files or headless CMS)
- Detailed agent pages
- Performance charts/graphs
- User submissions form

### Phase 3 (Later)
- Database backend (Supabase recommended)
- Admin panel for easy updates
- API for rankings data
- Automated benchmarking (if feasible)
- User voting/reviews

### Phase 4 (Future)
- Native app? (probably not needed)
- Community features
- Whatever makes money

## Tech Stack

**Current:**
- Pure HTML/CSS/JS
- Tailwind CSS (CDN)
- Netlify hosting

**Why this stack:**
- Zero build time
- Zero dependencies
- Instant deploys
- Cheap AF ($0 for now)
- Fast as hell

**When to upgrade:**
- Need CMS → Add Netlify CMS or Sanity.io
- Need database → Add Supabase
- Need complex interactions → Switch to React/Next.js
- Need API → Add serverless functions (Netlify Functions)

## Performance

Current setup is already optimized:
- Static files = instant load
- Tailwind via CDN = no build needed
- Minimal JS = fast interactivity

Future optimizations:
- Move Tailwind to build process (smaller CSS)
- Image optimization (when adding images)
- Service worker for offline (probably overkill)

## Maintenance

### Weekly
- Update `data.json` with new rankings
- Check AdSense performance
- Monitor analytics (add Google Analytics)

### Monthly
- Review and update blog content
- Check for broken links
- Review agent submissions (if you add a form)

### As Needed
- Add new categories
- Update design/styling
- Respond to user feedback

## Questions?

You know what you're doing. This is intentionally simple so you can scale it as needed without technical debt.

Built with zero bullshit. 🚀
