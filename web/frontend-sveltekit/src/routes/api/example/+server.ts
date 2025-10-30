import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { requireAuth } from '$lib/server/auth';
import { getAllDocuments } from '$lib/server/db';

/**
 * Example API endpoint demonstrating:
 * - Authentication middleware
 * - Firestore integration
 * - Type safety
 */

export const GET: RequestHandler = async (event) => {
	// Verify authentication
	const decodedToken = await requireAuth(event);
	if (decodedToken instanceof Response) {
		return decodedToken; // Return 401 if not authenticated
	}

	// Example: Get all documents from a collection
	// Replace 'your-collection' with your actual collection name
	try {
		const documents = await getAllDocuments('your-collection');

		return json({
			success: true,
			user: {
				uid: decodedToken.uid,
				email: decodedToken.email
			},
			data: documents
		});
	} catch (error) {
		console.error('Error fetching documents:', error);
		return json({ error: 'Failed to fetch data' }, { status: 500 });
	}
};

export const POST: RequestHandler = async (event) => {
	// Verify authentication
	const decodedToken = await requireAuth(event);
	if (decodedToken instanceof Response) {
		return decodedToken;
	}

	try {
		const body = await event.request.json();

		// Your POST logic here
		// Example: Create a new document
		// await setDocument('your-collection', 'doc-id', body);

		return json({
			success: true,
			message: 'Document created',
			data: body
		});
	} catch (error) {
		console.error('Error creating document:', error);
		return json({ error: 'Failed to create document' }, { status: 500 });
	}
};
