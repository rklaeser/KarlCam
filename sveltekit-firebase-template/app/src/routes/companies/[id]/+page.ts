import type { PageLoad } from './$types';
import type { CompaniesData, CareerCompany } from '$lib/types';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params, fetch }) => {
	const response = await fetch('/api/companies');
	const data: CompaniesData = await response.json();

	const company = data.companies.find(c => c.id === params.id);

	if (!company) {
		throw error(404, 'Company not found');
	}

	return {
		company
	};
};
