import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getAllDocuments } from '$lib/server/db';

export const GET: RequestHandler = async () => {
	try {
		const companies = await getAllDocuments('companies');

		return json({
			companies: companies,
			lastUpdated: new Date().toISOString().split('T')[0]
		});
	} catch (error) {
		console.error('Error loading companies:', error);
		return json({ error: 'Failed to load companies', companies: [] }, { status: 500 });
	}
};
