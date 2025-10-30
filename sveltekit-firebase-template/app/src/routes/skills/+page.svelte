<script lang="ts">
	import type { PageData } from './$types';
	import type { SkillStatus, SkillCategory } from '$lib/types';

	let { data }: { data: PageData } = $props();

	let activeTab = $state<'all' | SkillStatus>('all');
	let selectedCategory = $state<SkillCategory | 'all'>('all');

	// Get unique categories
	const categories = $derived(() => {
		const cats = new Set(data.skills.map(s => s.category));
		return Array.from(cats).sort();
	});

	// Filter skills
	let filteredSkills = $derived(() => {
		let result = data.skills;

		if (activeTab !== 'all') {
			result = result.filter(skill => skill.status === activeTab);
		}

		if (selectedCategory !== 'all') {
			result = result.filter(skill => skill.category === selectedCategory);
		}

		return result;
	});

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
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Skills</h1>
					<p class="text-sm text-gray-600 mt-1">
						{filteredSkills().length} skills
						{#if data.lastUpdated}
							• Last updated: {data.lastUpdated}
						{/if}
					</p>
				</div>
				<a
					href="/"
					class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300"
				>
					← Dashboard
				</a>
			</div>
		</div>
	</div>

	<!-- Filters -->
	<div class="bg-white border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<!-- Status Tabs -->
			<nav class="-mb-px flex space-x-8 mb-4">
				<button
					onclick={() => (activeTab = 'all')}
					class="px-1 py-2 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'all'}
					class:text-blue-600={activeTab === 'all'}
					class:border-transparent={activeTab !== 'all'}
					class:text-gray-500={activeTab !== 'all'}
				>
					All
				</button>
				<button
					onclick={() => (activeTab = 'proficient')}
					class="px-1 py-2 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'proficient'}
					class:text-blue-600={activeTab === 'proficient'}
					class:border-transparent={activeTab !== 'proficient'}
					class:text-gray-500={activeTab !== 'proficient'}
				>
					Proficient
				</button>
				<button
					onclick={() => (activeTab = 'learning')}
					class="px-1 py-2 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'learning'}
					class:text-blue-600={activeTab === 'learning'}
					class:border-transparent={activeTab !== 'learning'}
					class:text-gray-500={activeTab !== 'learning'}
				>
					Learning
				</button>
			</nav>

			<!-- Category Filter -->
			<div class="flex items-center gap-2">
				<label for="category" class="text-sm font-medium text-gray-700">Category:</label>
				<select
					id="category"
					bind:value={selectedCategory}
					class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All Categories</option>
					{#each categories() as category}
						<option value={category}>{category.replace(/_/g, ' ')}</option>
					{/each}
				</select>
			</div>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each filteredSkills() as skill}
				<a
					href="/skills/{skill.id}"
					class="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow group"
				>
					<div class="flex items-start justify-between mb-3">
						<h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600">
							{skill.name}
						</h3>
						<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(skill.status)}">
							{skill.status}
						</span>
					</div>

					<div class="mb-3">
						<span class="text-xs text-gray-600 uppercase tracking-wide">
							{skill.category.replace(/_/g, ' ')}
						</span>
					</div>

					{#if skill.proficiency}
						<div class="mb-3">
							<div class="flex items-center justify-between text-xs mb-1">
								<span class="text-gray-600">Proficiency</span>
								<span class="font-medium text-gray-900">{skill.proficiency}</span>
							</div>
							<div class="w-full bg-gray-200 rounded-full h-2">
								<div
									class="h-2 rounded-full {getProficiencyColor(skill.proficiency)}"
									style="width: {skill.proficiency === 'beginner' ? '25%' : skill.proficiency === 'intermediate' ? '50%' : skill.proficiency === 'advanced' ? '75%' : '100%'}"
								></div>
							</div>
						</div>
					{/if}

					{#if skill.yearsExperience}
						<p class="text-sm text-gray-600 mb-2">
							{skill.yearsExperience} {skill.yearsExperience === 1 ? 'year' : 'years'} experience
						</p>
					{/if}

					{#if skill.relevanceToCareer?.primaryUseCase}
						<p class="text-sm text-gray-600 line-clamp-2">
							{skill.relevanceToCareer.primaryUseCase}
						</p>
					{/if}
				</a>
			{/each}
		</div>

		{#if filteredSkills().length === 0}
			<div class="bg-white shadow rounded-lg p-8 text-center text-gray-500">
				No skills found for this filter
			</div>
		{/if}
	</main>
</div>
