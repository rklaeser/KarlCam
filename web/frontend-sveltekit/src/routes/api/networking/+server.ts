import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const networking = await getAllDocuments('networking');

		return json({
			networking: networking,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading networking opportunities:', error);
		return json({ error: 'Failed to load networking opportunities', networking: [] }, { status: 500 });
	}
};
