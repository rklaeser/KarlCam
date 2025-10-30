# Deployment Guide

This guide covers deploying your SvelteKit + Firebase app to production.

## Table of Contents

1. [Vercel Deployment](#vercel-deployment)
2. [Environment Variables](#environment-variables)
3. [Custom Domain](#custom-domain-optional)
4. [Post-Deployment](#post-deployment)
5. [Troubleshooting](#troubleshooting)

## Vercel Deployment

Vercel provides zero-config deployment for SvelteKit apps with excellent performance.

### Prerequisites

- Git repository (GitHub, GitLab, or Bitbucket)
- Vercel account (free tier available)
- Firebase project fully configured

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push your code to Git**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to https://vercel.com/new
   - Click "Import Git Repository"
   - Select your repository
   - Configure project:
     - **Framework Preset:** SvelteKit
     - **Root Directory:** Leave blank (we'll use vercel.json)
     - **Build Command:** Uses vercel.json config
     - **Output Directory:** Uses vercel.json config

3. **Add Environment Variables** (see [Environment Variables](#environment-variables))

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Your app is live!

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   # From project root
   vercel

   # Follow prompts:
   # - Set up and deploy? Yes
   # - Which scope? (select your account)
   # - Link to existing project? No
   # - Project name? (enter name)
   # - Directory? ./
   # - Override settings? No
   ```

4. **Add environment variables** (see below)

5. **Deploy to production**
   ```bash
   vercel --prod
   ```

## Environment Variables

You must configure these in Vercel for production:

### 1. Add Variables via Dashboard

1. Go to your project in Vercel
2. Click **Settings** > **Environment Variables**
3. Add each variable:

#### Server-Side Variables

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...your private key...
-----END PRIVATE KEY-----
"
AUTHORIZED_EMAILS=user1@example.com,user2@example.com
```

#### Client-Side Variables

```env
PUBLIC_FIREBASE_API_KEY=AIza...
PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
PUBLIC_FIREBASE_PROJECT_ID=your-project-id
```

**Important Notes:**
- For `FIREBASE_PRIVATE_KEY`, use the **raw** private key with actual newlines
- Vercel handles newlines properly - just paste the entire key including headers
- Mark sensitive variables (everything except PUBLIC_*) as **Production** only
- PUBLIC_* variables are exposed to the client

### 2. Add Variables via CLI

```bash
# Add production environment variables
vercel env add FIREBASE_PROJECT_ID production
# Paste value when prompted

vercel env add FIREBASE_CLIENT_EMAIL production
# Paste value when prompted

vercel env add FIREBASE_PRIVATE_KEY production
# Paste entire private key including -----BEGIN/END----- lines

vercel env add AUTHORIZED_EMAILS production
# Paste comma-separated emails

vercel env add PUBLIC_FIREBASE_API_KEY production
vercel env add PUBLIC_FIREBASE_AUTH_DOMAIN production
vercel env add PUBLIC_FIREBASE_PROJECT_ID production
```

### 3. Redeploy

After adding environment variables, redeploy:

**Via Dashboard:**
- Go to Deployments
- Click "..." on latest deployment
- Click "Redeploy"

**Via CLI:**
```bash
vercel --prod
```

## Custom Domain (Optional)

### Add a Custom Domain

1. **Purchase a domain** (from Namecheap, Google Domains, etc.)

2. **Add domain in Vercel**
   - Go to your project > **Settings** > **Domains**
   - Enter your domain (e.g., `myapp.com`)
   - Click "Add"

3. **Configure DNS**

   Vercel will show DNS records to add. Two options:

   **Option A: Use Vercel nameservers** (recommended)
   - Update nameservers at your domain registrar
   - Point to Vercel's nameservers (shown in dashboard)
   - Vercel handles everything automatically

   **Option B: Add DNS records manually**
   - Add A record: `76.76.21.21`
   - Add CNAME record for `www`: `cname.vercel-dns.com`

4. **Wait for DNS propagation**
   - Usually takes 5-30 minutes
   - Can take up to 48 hours in rare cases
   - Check status in Vercel dashboard

### HTTPS / SSL

- Vercel automatically provisions SSL certificates
- HTTPS is enforced by default
- Certificates auto-renew

## Post-Deployment

### 1. Update Firebase Auth Domain

Add your Vercel domain to Firebase authorized domains:

1. Go to Firebase Console > **Authentication** > **Settings**
2. Click **Authorized domains** tab
3. Click "Add domain"
4. Add your Vercel domain (e.g., `your-app.vercel.app`)
5. Add custom domain if you have one (e.g., `myapp.com`)

### 2. Test Production Deployment

1. Visit your deployed URL
2. Test authentication:
   - Email/password login
   - Google sign-in
3. Test API routes
4. Check browser console for errors
5. Test on mobile devices

### 3. Monitor Deployment

**Vercel Dashboard:**
- Go to your project > **Deployments**
- View build logs
- Check function logs
- Monitor performance

**Vercel Analytics (Optional):**
- Go to project > **Analytics**
- Enable Web Analytics
- View real-time traffic and performance

## Continuous Deployment

### Automatic Deployments

Vercel automatically deploys when you push to Git:

- **Production:** Pushes to `main` branch → Production deployment
- **Preview:** Pushes to other branches → Preview deployment
- **Pull Requests:** Each PR gets a preview URL

### Configure Branches

1. Go to project > **Settings** > **Git**
2. Set **Production Branch** (default: `main`)
3. Enable/disable preview deployments
4. Configure deployment protection

## Deployment Checklist

Before deploying to production:

- [ ] All environment variables configured in Vercel
- [ ] Firebase project in production mode
- [ ] Authorized emails list updated
- [ ] Firebase authorized domains include Vercel domain
- [ ] Test authentication locally
- [ ] Test API routes locally
- [ ] Review security rules
- [ ] Check `vercel.json` configuration
- [ ] Remove any console.logs or debug code
- [ ] Test build locally: `npm run build`

## Troubleshooting

### Build Failures

**Problem:** Build fails on Vercel

**Check:**
1. Build output logs in Vercel dashboard
2. Run `npm run build` locally to reproduce
3. Check all dependencies are in `package.json`
4. Verify `vercel.json` paths are correct

**Common Issues:**
- Missing environment variables
- TypeScript errors
- Missing dependencies
- Wrong Node.js version

### Authentication Errors

**Problem:** Auth works locally but not in production

**Solutions:**
1. Verify all environment variables are set in Vercel
2. Check Firebase authorized domains include Vercel domain
3. Verify `AUTHORIZED_EMAILS` includes your test users
4. Check private key formatting (should have actual newlines in Vercel)

### API Route 401 Errors

**Problem:** API routes return 401 Unauthorized

**Solutions:**
1. Check `AUTHORIZED_EMAILS` environment variable
2. Verify Firebase Admin credentials in Vercel
3. Test `getIdToken()` in browser console
4. Check Authorization header in network tab
5. Review server-side auth logs

### Private Key Format Issues

**Problem:** "Invalid private key" in production

**Solutions:**
1. In Vercel, paste the **entire private key** with actual newlines:
   ```
   -----BEGIN PRIVATE KEY-----
   MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
   ...
   -----END PRIVATE KEY-----
   ```
2. Don't escape newlines in Vercel (it handles them)
3. Verify no extra spaces or characters

### Domain Not Working

**Problem:** Custom domain shows errors

**Solutions:**
1. Check DNS propagation: https://dnschecker.org/
2. Verify DNS records match Vercel instructions
3. Wait up to 48 hours for DNS propagation
4. Check domain is verified in Vercel
5. Ensure domain is not used elsewhere

### Firestore Connection Errors

**Problem:** Can't connect to Firestore in production

**Solutions:**
1. Verify service account credentials are correct
2. Check Firebase project ID matches
3. Ensure Firestore database is created
4. Review Firestore rules (should deny client access)
5. Check service account has correct permissions

## Scaling & Performance

### Vercel Pro Features (Optional)

- **Faster builds** - Priority build queue
- **More bandwidth** - 1TB vs 100GB on free tier
- **Analytics** - Detailed performance insights
- **Password protection** - Protect preview deployments

### Optimizations

1. **Enable SvelteKit prerendering** for static pages
2. **Use edge functions** for globally distributed API routes
3. **Optimize images** with SvelteKit's image optimization
4. **Enable caching** headers for static assets
5. **Monitor Core Web Vitals** in Vercel Analytics

## Rollbacks

If a deployment has issues:

1. Go to **Deployments** in Vercel
2. Find a previous working deployment
3. Click "..." > "Promote to Production"
4. Previous deployment is now live

## Getting Help

- [Vercel Documentation](https://vercel.com/docs)
- [SvelteKit Deployment Docs](https://kit.svelte.dev/docs/adapter-vercel)
- [Vercel Support](https://vercel.com/support)
- Check deployment logs in Vercel dashboard
