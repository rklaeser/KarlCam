import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getDocumentById } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		// Career narrative is stored as a single document
		const narrative = await getDocumentById('career-narrative', 'narrative');

		return json(narrative || {});
	} catch (error) {
		console.error('Error loading career narrative:', error);
		return json({ error: 'Failed to load career narrative' }, { status: 500 });
	}
};
