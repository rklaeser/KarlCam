# MCP Server Debugging Guide

Based on real debugging sessions getting MCP servers working with Claude Code and Firebase.

## ⚠️ CRITICAL: Don't Use mcp.json Files!

**DO NOT create `mcp.json` files in your project directories - they are not read by Claude Code!**

Many tutorials and examples show creating `mcp.json` files, but Claude Code does NOT read these files. Instead:

- **✅ CORRECT:** Use the `claude mcp add` CLI command
- **✅ CORRECT:** Configuration is stored in `~/.claude.json`
- **❌ WRONG:** Creating `mcp.json` or `mcp_config.json` files in your project
- **❌ WRONG:** Manually editing config files

**If you have old `mcp.json` files:**
- They can be safely deleted (they're not being used)
- Or keep them as documentation/reference only

See **Section 6** for the correct way to add MCP servers.

---

## 1. Check Import Statements for ESM Compatibility

**Problem:** `TypeError: Cannot read properties of undefined (reading 'length')` at `admin.apps.length`

**Fix:**
```typescript
// ❌ Wrong - doesn't work with Firebase Admin SDK
import * as admin from 'firebase-admin';

// ✅ Correct - use default import
import admin from 'firebase-admin';
```

**Tip:** When using external SDKs, check their docs for proper ESM import patterns. Not all packages export the same way.

## 2. Handle Path Resolution for Environment Files

**Problem:** Environment variables not loading because `dotenv.config()` couldn't find `.env` file

**Fix:**
```typescript
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ✅ Specify exact path relative to the compiled output
config({ path: join(__dirname, '..', '.env') });
```

**Why this happens:** When MCP runs your server, the working directory is often different from where your `.env` file lives. Always use absolute paths.

## 3. Rebuild After Every Code Change

**Critical step:**
```bash
cd mcp-server
npm run build
```

**Why:** Claude Code runs the compiled JavaScript from `build/`, not your TypeScript source. If you forget to rebuild, you're debugging old code!

**Tip:** Consider adding a watch mode:
```json
// package.json
"scripts": {
  "build": "tsc && chmod +x build/index.js",
  "watch": "tsc --watch"
}
```

## 4. Test MCP Tools Individually

After reconnecting the MCP server, test each tool:

```
"Can you list all documents in the companies collection?"
"Try creating a test document"
"Get document with ID xyz"
```

This helps isolate whether the problem is:
- The entire server (nothing works)
- Specific tools (some work, some don't)
- Data validation (tools run but return errors)

## 5. Add Console Logging for Debugging

During development, add logs:

```typescript
console.error('Environment check:', {
  projectId: process.env.FIREBASE_PROJECT_ID ? '✓' : '✗',
  clientEmail: process.env.FIREBASE_CLIENT_EMAIL ? '✓' : '✗',
  privateKey: process.env.FIREBASE_PRIVATE_KEY ? '✓' : '✗'
});

console.error('Firebase initialized:', admin.apps.length > 0);
```

**View logs:** The MCP server output appears in the Claude Code logs/errors when tools fail.

## 6. Add MCP Server Using CLI (THE CORRECT WAY)

**⚠️ IMPORTANT:** Do NOT create `mcp.json` files in your project - they are not read by Claude Code!

Use the `claude mcp add` command to properly register your MCP server:

```bash
# Basic syntax
claude mcp add --transport stdio <server-name> \
  --env KEY1=value1 \
  --env KEY2=value2 \
  -- <command> [args...]

# Real example for Firebase MCP server
claude mcp add --transport stdio my-firestore-server \
  --env FIREBASE_PROJECT_ID="your-project-id" \
  --env FIREBASE_CLIENT_EMAIL="your-service-account@project.iam.gserviceaccount.com" \
  --env FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgk...
-----END PRIVATE KEY-----
" \
  -- node /absolute/path/to/your-project/mcp-server/build/index.js
```

**Where configuration is stored:**
- All MCP servers are registered in `~/.claude.json`
- This is a user-level configuration file
- You can verify it was added: `cat ~/.claude.json | grep "your-server-name"`

**Common mistakes:**
- Creating `mcp.json` files (they don't work!)
- Using relative paths instead of absolute paths
- Forgetting to escape newlines in private keys
- Missing required environment variables

## 7. Verify Server Was Added Successfully

After running `claude mcp add`, verify it was registered:

```bash
# Check the configuration file
cat ~/.claude.json | grep -A 5 "your-server-name"

# Or restart Claude Code and run:
/mcp
```

If you see your server name in the `/mcp` list, it's properly registered!

## 8. Check TypeScript Compilation Errors

```bash
npm run build
```

Look for:
- Type errors that got ignored
- Missing dependencies
- Module resolution issues

**Fix:** Make sure your `tsconfig.json` is correct:
```json
{
  "compilerOptions": {
    "module": "ESNext",
    "target": "ES2020",
    "moduleResolution": "node",
    "esModuleInterop": true
  }
}
```

## 9. Reconnect MCP After Changes

In Claude Code:
1. Make changes to your MCP server code
2. Run `npm run build`
3. Tell Claude: "I've rebuilt the MCP server, please reconnect"
4. Test the tools

**Why:** Claude Code caches the MCP connection. Reconnecting ensures it loads the new code.

## 10. Common Error Patterns

| Error Message | Likely Cause | Fix |
|--------------|--------------|-----|
| Cannot read properties of undefined | Wrong import pattern | Check default vs named imports |
| ENOENT: no such file or directory | Path resolution issue | Use absolute paths with join() |
| Service account object must contain... | Env vars not loading | Fix dotenv path resolution or check env vars in `claude mcp add` |
| Tool returns no data | Forgot to rebuild | Run npm run build |
| Server won't start | Syntax error in compiled JS | Check build output for errors |
| Server not appearing in /mcp list | Not added with CLI command | Use `claude mcp add` command (see section 6) |
| Server not appearing after `claude mcp add` | Didn't restart Claude Code | Command+Q and reopen |

## 11. Quick Debug Checklist

When your MCP server isn't working:

```bash
# 1. Rebuild
cd mcp-server && npm run build

# 2. Check for build errors
echo $?  # Should be 0

# 3. Verify compiled output exists
ls -la build/index.js

# 4. Check if env file exists
ls -la .env

# 5. Test running server directly (for stdio-based servers)
node build/index.js

# 6. Reconnect in Claude Code
# Tell Claude: "Reconnect the MCP server"
```

## 12. Test Server Manually with Environment Variables

**Before** using `claude mcp add`, test that your server actually works:

```bash
# Test with the exact env vars you'll pass to claude mcp add
FIREBASE_PROJECT_ID="your-project" \
FIREBASE_CLIENT_EMAIL="your-email@project.iam.gserviceaccount.com" \
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
..." \
node /path/to/build/index.js
```

**Expected output:**
```
Firestore MCP Server running on stdio
```

**If it errors:** Fix the server code before trying to add it to Claude Code.

## 13. Private Key Formatting

When passing private keys to `claude mcp add`, you can use actual newlines (not `\n` escape sequences):

```bash
claude mcp add --transport stdio my-server \
  --env FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQE...
-----END PRIVATE KEY-----
" \
  -- node /path/to/build/index.js
```

Your TypeScript code should handle the conversion:

```typescript
privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n')
```

This ensures compatibility whether the key has literal `\n` strings or actual newlines.

## Complete Debug Workflow

Here's the full workflow for setting up a new MCP server:

```bash
# 1. Build your server
cd mcp-server && npm run build

# 2. Test server works with env vars
FIREBASE_PROJECT_ID="your-project-id" \
FIREBASE_CLIENT_EMAIL="service-account@project.iam.gserviceaccount.com" \
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
" \
node build/index.js

# 3. Verify you see "Server running on stdio"
# (Press Ctrl+C to exit)

# 4. Add server to Claude Code using CLI
claude mcp add --transport stdio your-server-name \
  --env FIREBASE_PROJECT_ID="your-project-id" \
  --env FIREBASE_CLIENT_EMAIL="service-account@project.iam.gserviceaccount.com" \
  --env FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----
" \
  -- node /absolute/path/to/your-project/mcp-server/build/index.js

# 5. Verify it was added
cat ~/.claude.json | grep "your-server-name"

# 6. Restart Claude Code completely
# Command+Q, then reopen

# 7. Check server loaded
# Type: /mcp

# 8. Test a simple tool
# Ask Claude: "List documents in the test collection"
```

## Real Example from Debugging Sessions

The actual debugging flow we used:

1. ❌ Server failed to connect with `admin.apps.length` error
2. 🔍 Identified it was an import issue
3. ✅ Changed to `import admin from 'firebase-admin'`
4. 🔨 Rebuilt with `npm run build`
5. 🔌 Reconnected MCP server
6. ❌ Still failed - env vars not loading
7. 🔍 Added path resolution for `.env` file
8. 🔨 Rebuilt again
9. 🔌 Reconnected again
10. ✅ Success! Tools started working

**Key takeaway:** MCP debugging is iterative - change, rebuild, reconnect, test, repeat!

## Tips for Development

1. **Use watch mode during development:**
   ```bash
   npm run watch
   ```
   This auto-rebuilds on changes, though you still need to reconnect in Claude Code.

2. **Test tools from simple to complex:**
   - Start with `list_documents` (read-only, no parameters)
   - Then try `get_document` (read-only, with parameters)
   - Finally test `create_document` (write operations)

3. **Keep a test collection:**
   Create a `test` collection in Firestore for safe experimentation without affecting real data.

4. **Document your setup:**
   Keep a README or setup script that shows the `claude mcp add` command with dummy credentials as a reference for team members.

## Resources

- [MCP TypeScript SDK Documentation](https://modelcontextprotocol.io/docs/sdk/typescript)
- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Claude Code MCP Documentation](https://docs.claude.com/en/docs/claude-code/model-context-protocol)
