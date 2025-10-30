<script lang="ts">
	import type { PageData } from './$types';
	import type { SkillStatus } from '$lib/types';

	let { data }: { data: PageData } = $props();
	const { skill } = data;

	// Get status badge color
	function getStatusColor(status: SkillStatus): string {
		const colors: Record<SkillStatus, string> = {
			'proficient': 'bg-green-100 text-green-800',
			'learning': 'bg-blue-100 text-blue-800',
			'not_started': 'bg-gray-100 text-gray-800'
		};
		return colors[status];
	}

	// Get proficiency color
	function getProficiencyColor(proficiency?: string): string {
		if (!proficiency) return 'bg-gray-200';

		const colors: Record<string, string> = {
			'beginner': 'bg-red-200',
			'intermediate': 'bg-yellow-200',
			'advanced': 'bg-blue-200',
			'expert': 'bg-green-200'
		};
		return colors[proficiency] || 'bg-gray-200';
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-start">
				<div>
					<h1 class="text-3xl font-bold text-gray-900 mb-2">{skill.name}</h1>
					<div class="flex items-center gap-3 mb-2">
						<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStatusColor(skill.status)}">
							{skill.status}
						</span>
						<span class="text-sm text-gray-600">
							{skill.category.replace(/_/g, ' ')}
						</span>
					</div>
				</div>
				<a
					href="/skills"
					class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300"
				>
					← Back to Skills
				</a>
			</div>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main Column -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Evidence -->
				{#if skill.evidence && skill.evidence.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Evidence</h2>
						<ul class="space-y-2">
							{#each skill.evidence as item}
								<li class="flex items-start gap-2">
									<span class="text-green-600 mt-1">✓</span>
									<span class="text-gray-700">{item}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Relevance to Career -->
				{#if skill.relevanceToCareer}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Relevance to Career</h2>

						{#if skill.relevanceToCareer.primaryUseCase}
							<p class="text-gray-700 mb-4">{skill.relevanceToCareer.primaryUseCase}</p>
						{/if}

						{#if skill.relevanceToCareer.relevantToRoles && skill.relevanceToCareer.relevantToRoles.length > 0}
							<div class="mb-4">
								<h3 class="text-sm font-medium text-gray-900 mb-2">Relevant to Roles:</h3>
								<ul class="list-disc list-inside space-y-1">
									{#each skill.relevanceToCareer.relevantToRoles as role}
										<li class="text-sm text-gray-700">{role}</li>
									{/each}
								</ul>
							</div>
						{/if}

						{#if skill.relevanceToCareer.industryAdoption}
							<div>
								<h3 class="text-sm font-medium text-gray-900 mb-2">Industry Adoption:</h3>
								<p class="text-sm text-gray-700">{skill.relevanceToCareer.industryAdoption}</p>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Learning Resources -->
				{#if skill.resources && skill.resources.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Learning Resources</h2>
						<div class="space-y-3">
							{#each skill.resources as resource}
								<div class="border-l-4 border-blue-500 pl-4">
									<div class="flex items-start justify-between">
										<div>
											<h3 class="font-medium text-gray-900">{resource.title}</h3>
											<p class="text-sm text-gray-600">{resource.type}</p>
											{#if resource.url}
												<a href={resource.url} target="_blank" rel="noopener noreferrer" class="text-sm text-blue-600 hover:underline mt-1 inline-block">
													Open Resource →
												</a>
											{/if}
										</div>
										{#if resource.status}
											<span class="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
												{resource.status}
											</span>
										{/if}
									</div>
									{#if resource.notes}
										<p class="text-sm text-gray-600 mt-2">{resource.notes}</p>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Notes -->
				{#if skill.notes}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Notes</h2>
						<p class="text-gray-700 whitespace-pre-wrap">{skill.notes}</p>
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				<!-- Proficiency -->
				{#if skill.proficiency}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Proficiency Level</h2>
						<div class="text-center">
							<div class="text-3xl font-bold text-gray-900 mb-2">{skill.proficiency}</div>
							<div class="w-full bg-gray-200 rounded-full h-3">
								<div
									class="h-3 rounded-full {getProficiencyColor(skill.proficiency)}"
									style="width: {skill.proficiency === 'beginner' ? '25%' : skill.proficiency === 'intermediate' ? '50%' : skill.proficiency === 'advanced' ? '75%' : '100%'}"
								></div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Experience -->
				<div class="bg-white shadow rounded-lg p-6">
					<h2 class="text-lg font-semibold mb-4">Experience</h2>
					<div class="space-y-2 text-sm">
						{#if skill.yearsExperience}
							<div>
								<span class="text-gray-600">Years:</span>
								<span class="text-gray-900 font-medium">{skill.yearsExperience}</span>
							</div>
						{/if}
						{#if skill.lastUsed}
							<div>
								<span class="text-gray-600">Last Used:</span>
								<span class="text-gray-900 font-medium">{skill.lastUsed}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Related Skills -->
				{#if skill.relatedSkills && skill.relatedSkills.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Related Skills</h2>
						<div class="flex flex-wrap gap-2">
							{#each skill.relatedSkills as relatedSkill}
								<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-blue-50 text-blue-700">
									{relatedSkill}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Projects -->
				{#if skill.projects && skill.projects.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Related Projects</h2>
						<ul class="space-y-2">
							{#each skill.projects as project}
								<li class="text-sm text-blue-600 hover:underline">
									→ {project}
								</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		</div>
	</main>
</div>
