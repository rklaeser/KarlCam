# SvelteKit + Firebase + Vercel Template

A production-ready full-stack template featuring:

- **SvelteKit 2** - Modern, fast, and type-safe web framework
- **Firebase Auth** - Secure authentication with Google OAuth
- **Firestore** - NoSQL database with real-time capabilities
- **TailwindCSS** - Utility-first CSS framework with PostCSS
- **Vercel** - Zero-config deployment
- **MCP Server** - Model Context Protocol server for Firestore operations (optional)
- **TypeScript** - Full type safety across the stack

## Features

### Authentication
- Email/password authentication
- Google OAuth sign-in
- Server-side token verification
- Protected API routes
- Email whitelist authorization

### Database
- Firebase Admin SDK integration
- Generic CRUD utilities
- Type-safe Firestore operations
- Server-side data access

### MCP Server (Optional)
- Generic Firestore operations via MCP
- List, get, create, update, delete documents
- Configurable for Claude Code integration

### UI/UX
- Responsive design with TailwindCSS
- Forms plugin for better form styling
- Typography plugin for content
- Loading states and error handling

## Quick Start

### 1. Prerequisites
- Node.js 18+ and npm
- Firebase project ([Create one](https://console.firebase.google.com/))
- Vercel account (for deployment)

### 2. Setup

```bash
# Clone the template
git clone <your-repo-url>
cd sveltekit-firebase-template

# Install dependencies
cd app && npm install
cd ../mcp-server && npm install  # Optional: only if using MCP
```

### 3. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Authentication:
   - Go to Authentication > Sign-in method
   - Enable Email/Password
   - Enable Google
4. Generate service account:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file securely

### 4. Environment Variables

Create `app/.env`:

```bash
cp app/.env.example app/.env
```

Fill in your Firebase credentials in `app/.env`:

```env
# Server-side (from service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n..."

# Client-side (from Firebase console > Project Settings > Your apps)
PUBLIC_FIREBASE_API_KEY=your-api-key
PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
PUBLIC_FIREBASE_PROJECT_ID=your-project-id

# Authorized emails (comma-separated)
AUTHORIZED_EMAILS=user1@example.com,user2@example.com
```

### 5. Run Locally

```bash
cd app
npm run dev
```

Visit http://localhost:5173

## Project Structure

```
sveltekit-firebase-template/
├── app/                          # SvelteKit application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── server/
│   │   │   │   ├── firebase.ts   # Firebase Admin SDK
│   │   │   │   ├── auth.ts       # Auth middleware
│   │   │   │   └── db.ts         # Database utilities
│   │   │   ├── stores/
│   │   │   │   └── auth.svelte.ts # Auth store
│   │   │   ├── firebase.ts       # Firebase client
│   │   │   └── utils.ts          # Utility functions
│   │   ├── routes/
│   │   │   ├── api/
│   │   │   │   └── example/      # Example API route
│   │   │   ├── login/            # Login page
│   │   │   ├── +layout.svelte    # Root layout
│   │   │   └── +page.svelte      # Home page
│   │   ├── app.css               # Tailwind imports
│   │   └── app.d.ts              # Type definitions
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env.example
│
├── mcp-server/                   # Optional MCP server
│   ├── src/
│   │   └── index.ts              # Generic CRUD operations
│   ├── package.json
│   └── .env.example
│
├── firebase.json                 # Firebase config
├── firestore.rules               # Security rules
├── firestore.indexes.json        # Database indexes
├── vercel.json                   # Vercel deployment
└── README.md
```

## Development

### Adding a New Collection

1. Define your type in `app/src/lib/types/index.ts`:

```typescript
export interface MyData {
  id: string;
  name: string;
  createdAt: Date;
}
```

2. Use generic DB utilities in `app/src/lib/server/db.ts`:

```typescript
import { getAllDocuments, getDocumentById, setDocument } from '$lib/server/db';

// Get all documents
const items = await getAllDocuments<MyData>('my-collection');

// Get one document
const item = await getDocumentById<MyData>('my-collection', 'doc-id');

// Create/update document
await setDocument('my-collection', 'doc-id', { name: 'Example' });
```

3. Create an API route in `app/src/routes/api/my-data/+server.ts`:

```typescript
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { requireAuth } from '$lib/server/auth';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async (event) => {
  const auth = await requireAuth(event);
  if (auth instanceof Response) return auth;

  const data = await getAllDocuments('my-collection');
  return json({ data });
};
```

### Protected Routes

All API routes should use the `requireAuth` middleware:

```typescript
import { requireAuth } from '$lib/server/auth';

export const GET: RequestHandler = async (event) => {
  // This returns 401 if not authenticated
  const decodedToken = await requireAuth(event);
  if (decodedToken instanceof Response) return decodedToken;

  // User is authenticated, proceed
  // decodedToken.email, decodedToken.uid available
};
```

## Deployment

### Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

3. Add environment variables in Vercel dashboard:
   - Go to Project Settings > Environment Variables
   - Add all variables from `.env`

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

## MCP Server Setup (Optional)

The MCP server allows Claude Code to interact with your Firestore database.

1. Build the MCP server:
```bash
cd mcp-server
npm run build
```

2. Configure MCP (create `~/.config/claude-code/mcp.json` or project-local `mcp.json`):
```json
{
  "mcpServers": {
    "firestore": {
      "command": "node",
      "args": ["/path/to/mcp-server/build/index.js"],
      "env": {
        "FIREBASE_PROJECT_ID": "your-project-id",
        "FIREBASE_CLIENT_EMAIL": "your-client-email",
        "FIREBASE_PRIVATE_KEY": "your-private-key"
      }
    }
  }
}
```

3. Available MCP tools:
   - `list_documents` - List all documents in a collection
   - `get_document` - Get a specific document
   - `create_document` - Create a new document
   - `update_document` - Update an existing document
   - `delete_document` - Delete a document

## Customization

### Change App Name
1. Update `app/src/routes/+page.svelte` - Change "My App" header
2. Update `app/src/routes/login/+page.svelte` - Change "My App" title
3. Update `app/package.json` - Change "name" field
4. Update `mcp-server/package.json` - Change "name" field

### Add Email Authorization
Edit `app/.env` and add authorized emails:
```env
AUTHORIZED_EMAILS=user1@example.com,user2@example.com,user3@example.com
```

### Styling
- Tailwind config: `app/tailwind.config.js`
- Global styles: `app/src/app.css`
- Extend Tailwind theme as needed

## Tech Stack Details

- **SvelteKit 2**: Latest version with Svelte 5 runes
- **Firebase 12**: Latest Firebase SDK
- **Tailwind 3**: With forms and typography plugins
- **TypeScript 5**: Full type safety
- **Vite 7**: Fast build tool
- **Vercel**: Serverless deployment

## Security

- Firebase Auth tokens verified server-side
- Email whitelist for authorized users
- Firestore rules deny all client access (server-only)
- Environment variables for sensitive data
- HTTPS enforced in production

## License

MIT

## Support

For issues or questions:
1. Check existing documentation
2. Review Firebase/SvelteKit docs
3. Create an issue in the repository

---

Built with ❤️ using SvelteKit, Firebase, and Vercel
