<script lang="ts">
	import type { PageData } from './$types';
	import type { JobInteractionStatus } from '$lib/types';

	let { data }: { data: PageData } = $props();
	const { company } = data;

	// Get status badge color
	function getStatusColor(status: JobInteractionStatus): string {
		const colors: Record<JobInteractionStatus, string> = {
			'not_started': 'bg-gray-100 text-gray-800',
			'considering': 'bg-yellow-100 text-yellow-800',
			'applying': 'bg-blue-100 text-blue-800',
			'interviewing': 'bg-purple-100 text-purple-800',
			'offer': 'bg-green-100 text-green-800',
			'accepted': 'bg-green-200 text-green-900',
			'declined': 'bg-red-100 text-red-800',
			'rejected': 'bg-gray-200 text-gray-700'
		};
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	// Get fit badge color
	function getFitColor(fit?: 'excellent' | 'good' | 'moderate' | 'poor'): string {
		if (!fit) return 'bg-gray-100 text-gray-600';

		const colors = {
			'excellent': 'bg-green-100 text-green-800',
			'good': 'bg-blue-100 text-blue-800',
			'moderate': 'bg-yellow-100 text-yellow-800',
			'poor': 'bg-red-100 text-red-800'
		};
		return colors[fit];
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">{company.name}</h1>
					{#if company.mission}
						<p class="text-gray-600 mt-2">{company.mission}</p>
					{/if}
					<div class="flex gap-2 mt-3">
						{#if company.location}
							<span class="text-sm text-gray-500">📍 {company.location}</span>
						{/if}
						{#if company.website}
							<a href={company.website} target="_blank" rel="noopener noreferrer" class="text-sm text-blue-600 hover:underline">
								🔗 Website
							</a>
						{/if}
					</div>
				</div>
				<a
					href="/companies"
					class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300"
				>
					← Back to Companies
				</a>
			</div>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main Column -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Job Interaction Status -->
				{#if company.jobInteraction}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Application Status</h2>
						<div class="flex items-center gap-3 mb-4">
							<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStatusColor(company.jobInteraction.status)}">
								{company.jobInteraction.status}
							</span>
						</div>
						{#if company.jobInteraction.notes}
							<p class="text-gray-700">{company.jobInteraction.notes}</p>
						{/if}
						{#if company.jobInteraction.appliedDate}
							<p class="text-sm text-gray-500 mt-2">Applied: {company.jobInteraction.appliedDate}</p>
						{/if}
					</div>
				{/if}

				<!-- Roles -->
				{#if company.roles && company.roles.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Open Roles</h2>
						<div class="space-y-4">
							{#each company.roles as role}
								<div class="border-l-4 border-blue-500 pl-4">
									<div class="flex items-start justify-between">
										<h3 class="font-medium text-gray-900">{role.title}</h3>
										{#if role.match}
											<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {getFitColor(role.match)}">
												{role.match}
											</span>
										{/if}
									</div>
									{#if role.description}
										<p class="text-sm text-gray-600 mt-1">{role.description}</p>
									{/if}
									{#if role.link}
										<a href={role.link} target="_blank" rel="noopener noreferrer" class="text-sm text-blue-600 hover:underline mt-1 inline-block">
											View Posting →
										</a>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Technical Methods -->
				{#if company.technicalMethods && company.technicalMethods.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Technical Methods</h2>
						<div class="flex flex-wrap gap-2">
							{#each company.technicalMethods as method}
								<span class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-50 text-blue-700">
									{method}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Categories -->
				{#if company.categories && company.categories.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Categories</h2>
						<div class="flex flex-wrap gap-2">
							{#each company.categories as category}
								<span class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700">
									{category}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Personal Resonance -->
				{#if company.personalResonance}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Personal Resonance</h2>
						<p class="text-gray-700">{company.personalResonance}</p>
					</div>
				{/if}

				<!-- Notes -->
				{#if company.notes}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Notes</h2>
						<p class="text-gray-700 whitespace-pre-wrap">{company.notes}</p>
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				<!-- Fit Scores -->
				{#if company.fit}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Fit Assessment</h2>
						<div class="space-y-3">
							{#if company.fit.domain}
								<div>
									<div class="text-sm text-gray-600 mb-1">Domain Fit</div>
									<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getFitColor(company.fit.domain)}">
										{company.fit.domain}
									</span>
								</div>
							{/if}
							{#if company.fit.mission}
								<div>
									<div class="text-sm text-gray-600 mb-1">Mission Fit</div>
									<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getFitColor(company.fit.mission)}">
										{company.fit.mission}
									</span>
								</div>
							{/if}
							{#if company.fit.overall !== undefined}
								<div>
									<div class="text-sm text-gray-600 mb-1">Overall Fit</div>
									<div class="text-2xl font-bold text-gray-900">{company.fit.overall}/10</div>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Physical Work Product -->
				{#if company.physicalWorkProduct}
					<div class="bg-green-50 border border-green-200 rounded-lg p-4">
						<div class="flex items-center gap-2">
							<span class="text-2xl">🔧</span>
							<span class="text-sm font-medium text-green-800">Physical Work Product</span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</main>
</div>
