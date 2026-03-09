# Deployment Checklist

## First Deploy (Do Once)

### Netlify Setup
- [ ] Go to netlify.com and sign up
- [ ] Choose deployment method:
  - [ ] **Fast**: Drag & drop at app.netlify.com/drop
  - [ ] **Better**: Connect GitHub repo
- [ ] Site is live at random-name.netlify.app
- [ ] Add custom domain: topclanker.com in Site Settings

### DNS Configuration (Your Domain Registrar)
- [ ] Option A - Netlify DNS (Recommended):
  - [ ] Use Netlify nameservers in Site Settings
  - [ ] Update nameservers at your domain registrar
  
- [ ] Option B - Keep current DNS:
  - [ ] A record: @ → 75.2.60.5
  - [ ] CNAME: www → your-site.netlify.app

### SSL
- [ ] Netlify auto-provisions SSL (free)
- [ ] Check HTTPS is working
- [ ] Enable "Force HTTPS" in Site Settings

### Analytics & Ads
- [ ] Add Google Analytics code (optional)
- [ ] Set up Google AdSense account
- [ ] Get AdSense publisher ID
- [ ] Add AdSense code to index.html
- [ ] Replace ad placeholder divs with real ad units

## Regular Updates

### Update Rankings
1. Edit `data.json`
2. Update `lastUpdated` field
3. Add/modify agent entries
4. Commit and push (or re-drag folder)
5. Wait ~30 seconds for deploy

### Add Blog Post
1. Create HTML file or integrate CMS (future)
2. Link from blog section
3. Deploy

## Testing Locally

```bash
# In project directory
python3 -m http.server 8000

# Visit http://localhost:8000
```

## Emergency Rollback

If shit breaks:
- Netlify: Go to Deploys → Click previous deploy → "Publish deploy"
- Git: `git revert HEAD` and push

## Performance Monitoring

- [ ] Set up Netlify Analytics (paid but worth it)
- [ ] Or use Google Analytics (free)
- [ ] Monitor AdSense earnings
- [ ] Check site speed: pagespeed.web.dev

## Next Steps (After Launch)

- [ ] Submit to Google Search Console
- [ ] Add sitemap.xml
- [ ] Share on social media
- [ ] Post on relevant forums/communities
- [ ] Consider SEO optimization
- [ ] Add email signup for updates
