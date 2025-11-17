# TopClanker - QUICK START (5 Minutes to Live)

## Option 1: Netlify Drop (FASTEST - 2 minutes)

1. **Download the `topclanker` folder to your computer**

2. **Go to**: https://app.netlify.com/drop

3. **Drag the entire `topclanker` folder** onto the page

4. **Done!** Your site is live at a random URL like `epic-tesla-123.netlify.app`

5. **Add your domain**:
   - Click "Domain settings"
   - Click "Add custom domain"
   - Enter: `topclanker.com`
   - Follow instructions to point your DNS

## Option 2: Git Deploy (BETTER - 10 minutes)

### In Cursor Terminal:

```bash
# Navigate to the project
cd /path/to/topclanker

# Initialize git
git init
git add .
git commit -m "Launch TopClanker"

# Create repo on GitHub, then:
git remote add origin https://github.com/yourusername/topclanker.git
git branch -M main
git push -u origin main
```

### On Netlify:

1. Go to https://app.netlify.com
2. Click "New site from Git"
3. Choose GitHub → Select your repo
4. Build settings: **Leave everything blank**
5. Click "Deploy site"
6. Add custom domain in settings

## DNS Setup (At Your Domain Registrar)

**Easiest:** Use Netlify DNS
- In Netlify: Domain Settings → Use Netlify DNS
- Copy the 4 nameservers
- Go to your domain registrar (where you bought topclanker.com)
- Replace nameservers with Netlify's
- Wait 1-24 hours

**Alternative:** Point to Netlify
- Add A record: `@` → `75.2.60.5`
- Add CNAME: `www` → `your-site-name.netlify.app`
- Wait 1-24 hours

## Update Rankings (Anytime)

1. Edit `data.json`
2. Change the rankings, scores, agents
3. If using Git: `git add . && git commit -m "Update rankings" && git push`
4. If using Drop: Just re-drag the folder
5. Live in ~30 seconds

## Add Google AdSense (For $$)

1. Sign up: https://www.google.com/adsense
2. Get your publisher ID (looks like `ca-pub-1234567890123456`)
3. Open `index.html`
4. Add before `</head>`:
```html
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR-ID-HERE"
     crossorigin="anonymous"></script>
```
5. Replace ad placeholder divs with real ad units from AdSense
6. Deploy

## Test Locally First (Optional)

```bash
cd topclanker
python3 -m http.server 8000
```

Visit: http://localhost:8000

## Files You'll Edit Most

- `data.json` - All the rankings data
- `index.html` - Page content and structure
- `style.css` - Colors and styling

## That's It

You're live. Now go make that passive income.

Questions? Check README.md for details.
