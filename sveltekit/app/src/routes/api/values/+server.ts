import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const values = await getAllDocuments('values');

		return json({
			values: values,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading values:', error);
		return json({ error: 'Failed to load values', values: [] }, { status: 500 });
	}
};
