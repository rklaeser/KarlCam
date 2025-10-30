# Detailed Setup Guide

This guide walks you through setting up the SvelteKit + Firebase template from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Firebase Setup](#firebase-setup)
3. [Local Development](#local-development)
4. [MCP Server Setup](#mcp-server-setup-optional)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Node.js 18+** and npm
  ```bash
  node --version  # Should be v18.0.0 or higher
  npm --version
  ```

- **Git** (for version control)
  ```bash
  git --version
  ```

### Accounts Needed

1. **Firebase Account** - Free tier available
   - Visit https://console.firebase.google.com/
   - Sign in with Google account

2. **Vercel Account** (for deployment) - Free tier available
   - Visit https://vercel.com/
   - Sign up with GitHub/GitLab/Bitbucket

## Firebase Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or "Create a project"
3. Enter project name (e.g., "my-app")
4. Choose whether to enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Authentication

1. In Firebase Console, go to **Authentication**
2. Click "Get started"
3. Go to **Sign-in method** tab

#### Enable Email/Password:
- Click "Email/Password"
- Toggle "Enable"
- Click "Save"

#### Enable Google Sign-in:
- Click "Google"
- Toggle "Enable"
- Enter project support email
- Click "Save"

### 3. Create Firestore Database

1. In Firebase Console, go to **Firestore Database**
2. Click "Create database"
3. Choose **Production mode** (we use server-side auth)
4. Select a location (choose one closest to your users)
5. Click "Enable"

### 4. Get Firebase Client Credentials

1. Go to **Project Settings** (gear icon)
2. Scroll to "Your apps"
3. Click the web icon (`</>`)
4. Register app with a nickname (e.g., "web-app")
5. **Don't** set up Firebase Hosting
6. Copy the config values:
   ```javascript
   {
     apiKey: "...",              // PUBLIC_FIREBASE_API_KEY
     authDomain: "...",          // PUBLIC_FIREBASE_AUTH_DOMAIN
     projectId: "..."            // PUBLIC_FIREBASE_PROJECT_ID
   }
   ```

### 5. Generate Service Account

1. Go to **Project Settings** > **Service Accounts**
2. Click "Generate new private key"
3. Click "Generate key"
4. **Save the JSON file securely** (never commit to git!)
5. Extract these values:
   ```json
   {
     "project_id": "...",        // FIREBASE_PROJECT_ID
     "client_email": "...",      // FIREBASE_CLIENT_EMAIL
     "private_key": "..."        // FIREBASE_PRIVATE_KEY
   }
   ```

## Local Development

### 1. Clone Template

```bash
# Clone your repository
git clone <your-repo-url>
cd sveltekit-firebase-template
```

### 2. Install Dependencies

```bash
# Install app dependencies
cd app
npm install

# Install MCP server dependencies (optional)
cd ../mcp-server
npm install
```

### 3. Configure Environment Variables

#### App Environment

Create `app/.env`:

```bash
cd app
cp .env.example .env
```

Edit `app/.env` with your Firebase credentials:

```env
# From service account JSON
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...your private key...
-----END PRIVATE KEY-----
"

# From Firebase web app config
PUBLIC_FIREBASE_API_KEY=AIza...
PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
PUBLIC_FIREBASE_PROJECT_ID=your-project-id

# Add authorized user emails (comma-separated)
AUTHORIZED_EMAILS=your-email@gmail.com,teammate@example.com
```

**Important Notes:**
- The private key must include the literal `\n` characters or actual newlines
- Keep quotes around the private key
- Never commit `.env` to git (it's in `.gitignore`)

#### MCP Server Environment (Optional)

If using the MCP server:

```bash
cd mcp-server
cp .env.example .env
```

Edit `mcp-server/.env` with same Firebase credentials (server-side only).

### 4. Add Your Email to Firebase Auth

Since we use email whitelisting, you need to:

1. Add your email to `AUTHORIZED_EMAILS` in `app/.env`
2. Create a user account in Firebase:
   - Go to Firebase Console > Authentication > Users
   - Click "Add user"
   - Enter your email and a password
   - Click "Add user"

Alternatively, use Google sign-in if your Google account email is in the whitelist.

### 5. Run Development Server

```bash
cd app
npm run dev
```

Visit http://localhost:5173

You should see:
- Login page if not authenticated
- Redirect to home page after successful login
- Your email displayed in the header

### 6. Test Authentication

1. Navigate to http://localhost:5173
2. You should be redirected to `/login`
3. Try logging in with:
   - Email/password you created in Firebase
   - Google sign-in (if your Google email is whitelisted)
4. After successful login, you should see the home page

## MCP Server Setup (Optional)

The MCP server enables Claude Code to interact with your Firestore database.

### 1. Build MCP Server

```bash
cd mcp-server
npm run build
```

This creates `mcp-server/build/index.js`

### 2. Configure MCP

Create or edit `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "my-app-firestore": {
      "command": "node",
      "args": [
        "/absolute/path/to/sveltekit-firebase-template/mcp-server/build/index.js"
      ],
      "env": {
        "FIREBASE_PROJECT_ID": "your-project-id",
        "FIREBASE_CLIENT_EMAIL": "firebase-adminsdk-xxxxx@...",
        "FIREBASE_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
      }
    }
  }
}
```

**Important:** Use double backslashes (`\\n`) in the JSON for newlines.

### 3. Test MCP Server

In Claude Code, you should see MCP tools available:
- `list_documents`
- `get_document`
- `create_document`
- `update_document`
- `delete_document`

## Troubleshooting

### Firebase Auth Not Working

**Problem:** "Unauthorized" errors when signing in

**Solutions:**
1. Check `AUTHORIZED_EMAILS` includes your email
2. Verify email/Google sign-in is enabled in Firebase Console
3. Check Firebase credentials in `.env` are correct
4. Ensure you created a user in Firebase Authentication

### Private Key Format Errors

**Problem:** "Invalid private key" or certificate errors

**Solutions:**
1. Ensure private key has proper newlines:
   ```env
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
   MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
   ...
   -----END PRIVATE KEY-----
   "
   ```
2. Or use literal `\n`:
   ```env
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----\n"
   ```

### Port Already in Use

**Problem:** "Port 5173 is already in use"

**Solutions:**
1. Kill existing process:
   ```bash
   lsof -ti:5173 | xargs kill
   ```
2. Or use a different port:
   ```bash
   npm run dev -- --port 5174
   ```

### Module Not Found Errors

**Problem:** Import errors or missing modules

**Solutions:**
1. Delete `node_modules` and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```
2. Clear SvelteKit cache:
   ```bash
   rm -rf .svelte-kit
   npm run dev
   ```

### MCP Server Not Connecting

**Problem:** MCP tools not showing in Claude Code

**Solutions:**
1. Check MCP server is built:
   ```bash
   ls mcp-server/build/index.js
   ```
2. Verify `mcp.json` has absolute paths
3. Check environment variables in `mcp.json`
4. Restart Claude Code

### Firestore Permission Denied

**Problem:** Permission denied when accessing Firestore

**Solutions:**
1. We use **server-side only** access via Firebase Admin SDK
2. Client-side access is blocked by security rules
3. Always access Firestore from API routes, not client code
4. Check service account credentials are correct

## Next Steps

Once setup is complete:

1. **Customize the app** - Change branding, add your domain logic
2. **Add your data models** - Define types and collections
3. **Create API routes** - Add endpoints for your data
4. **Deploy to Vercel** - See [DEPLOYMENT.md](./DEPLOYMENT.md)

## Getting Help

- Check the main [README.md](./README.md)
- Review [SvelteKit docs](https://kit.svelte.dev/docs)
- Review [Firebase docs](https://firebase.google.com/docs)
- Check [Vercel docs](https://vercel.com/docs)
