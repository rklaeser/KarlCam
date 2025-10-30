import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const communities = await getAllDocuments('communities');

		return json({
			communities: communities,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading communities:', error);
		return json({ error: 'Failed to load communities', communities: [] }, { status: 500 });
	}
};
