#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import admin from 'firebase-admin';
import { config } from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables from .env file in the mcp-server directory
config({ path: join(__dirname, '..', '.env') });

// Initialize Firebase Admin
if (!admin.apps.length) {
  const serviceAccount = {
    projectId: process.env.FIREBASE_PROJECT_ID,
    clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
    privateKey: process.env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n')
  };

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount as admin.ServiceAccount)
  });
}

const db = admin.firestore();

/**
 * Generic MCP Server for Firestore CRUD operations
 *
 * This is a starter template. Extend it with your own tools and collections.
 *
 * Example tools included:
 * - list_documents: List all documents in a collection
 * - get_document: Get a specific document by ID
 * - create_document: Create a new document
 * - update_document: Update an existing document
 * - delete_document: Delete a document
 */

const server = new Server(
  {
    name: 'firestore-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List all available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'list_documents',
        description: 'List all documents in a Firestore collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The collection name',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of documents to return (default: 10)',
              default: 10,
            },
          },
          required: ['collection'],
        },
      },
      {
        name: 'get_document',
        description: 'Get a specific document by ID from a Firestore collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The collection name',
            },
            id: {
              type: 'string',
              description: 'The document ID',
            },
          },
          required: ['collection', 'id'],
        },
      },
      {
        name: 'create_document',
        description: 'Create a new document in a Firestore collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The collection name',
            },
            id: {
              type: 'string',
              description: 'The document ID (optional - will auto-generate if not provided)',
            },
            data: {
              type: 'object',
              description: 'The document data',
            },
          },
          required: ['collection', 'data'],
        },
      },
      {
        name: 'update_document',
        description: 'Update an existing document in a Firestore collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The collection name',
            },
            id: {
              type: 'string',
              description: 'The document ID',
            },
            data: {
              type: 'object',
              description: 'The data to update',
            },
          },
          required: ['collection', 'id', 'data'],
        },
      },
      {
        name: 'delete_document',
        description: 'Delete a document from a Firestore collection',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The collection name',
            },
            id: {
              type: 'string',
              description: 'The document ID',
            },
          },
          required: ['collection', 'id'],
        },
      },
      {
        name: 'bulk_upload',
        description: 'Upload multiple documents to a Firestore collection from JSON data. Pass an array of objects to upload.',
        inputSchema: {
          type: 'object',
          properties: {
            collection: {
              type: 'string',
              description: 'The Firestore collection name to upload to',
            },
            documents: {
              type: 'array',
              description: 'Array of document objects to upload',
              items: {
                type: 'object',
              },
            },
            idField: {
              type: 'string',
              description: 'The field name to use as the document ID (e.g., "id" or "name"). If not specified, Firestore will auto-generate IDs.',
            },
          },
          required: ['collection', 'documents'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'list_documents': {
        const { collection, limit = 10 } = args as { collection: string; limit?: number };
        const snapshot = await db.collection(collection).limit(limit).get();
        const documents = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ collection, count: documents.length, documents }, null, 2),
            },
          ],
        };
      }

      case 'get_document': {
        const { collection, id } = args as { collection: string; id: string };
        const doc = await db.collection(collection).doc(id).get();

        if (!doc.exists) {
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify({ error: 'Document not found' }),
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ id: doc.id, ...doc.data() }, null, 2),
            },
          ],
        };
      }

      case 'create_document': {
        const { collection, id, data } = args as { collection: string; id?: string; data: any };
        const docRef = id
          ? db.collection(collection).doc(id)
          : db.collection(collection).doc();

        await docRef.set(data);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ id: docRef.id, ...data }, null, 2),
            },
          ],
        };
      }

      case 'update_document': {
        const { collection, id, data } = args as { collection: string; id: string; data: any };
        await db.collection(collection).doc(id).update(data);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ id, updated: true }, null, 2),
            },
          ],
        };
      }

      case 'delete_document': {
        const { collection, id } = args as { collection: string; id: string };
        await db.collection(collection).doc(id).delete();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({ id, deleted: true }, null, 2),
            },
          ],
        };
      }

      case 'bulk_upload': {
        const { collection, documents, idField } = args as {
          collection: string;
          documents: any[];
          idField?: string;
        };

        if (!Array.isArray(documents)) {
          throw new Error('documents must be an array');
        }

        const batch = db.batch();
        const uploadedIds: string[] = [];

        for (const doc of documents) {
          let docId: string;

          if (idField && doc[idField]) {
            // Use specified field as document ID
            docId = String(doc[idField]);
          } else {
            // Auto-generate ID
            docId = db.collection(collection).doc().id;
          }

          const docRef = db.collection(collection).doc(docId);
          batch.set(docRef, doc);
          uploadedIds.push(docId);
        }

        await batch.commit();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                collection,
                uploaded: documents.length,
                documentIds: uploadedIds
              }, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ error: error.message }),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Firestore MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error in main():', error);
  process.exit(1);
});
