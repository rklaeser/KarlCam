<script lang="ts">
	import type { PageData } from './$types';
	import type { ProjectStatus, ProjectCategory } from '$lib/types';

	let { data }: { data: PageData } = $props();

	let activeTab = $state<'all' | ProjectStatus>('all');

	// Filter projects based on active tab
	let filteredProjects = $derived(() => {
		if (activeTab === 'all') return data.projects;
		return data.projects.filter(project => project.status === activeTab);
	});

	// Get status badge color
	function getStatusColor(status: ProjectStatus): string {
		const colors: Record<ProjectStatus, string> = {
			'planned': 'bg-gray-100 text-gray-800',
			'in_progress': 'bg-blue-100 text-blue-800',
			'completed': 'bg-green-100 text-green-800',
			'on_hold': 'bg-yellow-100 text-yellow-800',
			'cancelled': 'bg-red-100 text-red-800'
		};
		return colors[status];
	}

	// Get category icon
	function getCategoryIcon(category: ProjectCategory): string {
		const icons: Record<ProjectCategory, string> = {
			'robotics': '🤖',
			'computer-vision': '👁️',
			'attention-tech': '🧘',
			'embedded-systems': '💾',
			'web-dev': '🌐',
			'other': '📦'
		};
		return icons[category];
	}
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Projects</h1>
					<p class="text-sm text-gray-600 mt-1">
						{filteredProjects().length} projects
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

	<!-- Tabs -->
	<div class="bg-white border-b">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<nav class="-mb-px flex space-x-8">
				<button
					onclick={() => (activeTab = 'all')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'all'}
					class:text-blue-600={activeTab === 'all'}
					class:border-transparent={activeTab !== 'all'}
					class:text-gray-500={activeTab !== 'all'}
				>
					All
				</button>
				<button
					onclick={() => (activeTab = 'completed')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'completed'}
					class:text-blue-600={activeTab === 'completed'}
					class:border-transparent={activeTab !== 'completed'}
					class:text-gray-500={activeTab !== 'completed'}
				>
					Completed
				</button>
				<button
					onclick={() => (activeTab = 'in_progress')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'in_progress'}
					class:text-blue-600={activeTab === 'in_progress'}
					class:border-transparent={activeTab !== 'in_progress'}
					class:text-gray-500={activeTab !== 'in_progress'}
				>
					In Progress
				</button>
				<button
					onclick={() => (activeTab = 'planned')}
					class="px-1 py-4 text-sm font-medium border-b-2 transition-colors"
					class:border-blue-600={activeTab === 'planned'}
					class:text-blue-600={activeTab === 'planned'}
					class:border-transparent={activeTab !== 'planned'}
					class:text-gray-500={activeTab !== 'planned'}
				>
					Planned
				</button>
			</nav>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each filteredProjects() as project}
				<a
					href="/projects/{project.id}"
					class="bg-white shadow rounded-lg p-6 hover:shadow-lg transition-shadow group"
				>
					<div class="flex items-start justify-between mb-3">
						<div class="flex items-center gap-2">
							<span class="text-2xl">{getCategoryIcon(project.category)}</span>
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(project.status)}">
								{project.status}
							</span>
						</div>
					</div>

					<h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 mb-2">
						{project.name}
					</h3>

					<p class="text-sm text-gray-600 mb-4 line-clamp-2">
						{project.summary}
					</p>

					<div class="flex flex-wrap gap-1 mb-3">
						{#if project.skillsDemonstrated}
							{#each project.skillsDemonstrated.slice(0, 3) as skill}
								<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
									{skill}
								</span>
							{/each}
							{#if project.skillsDemonstrated.length > 3}
								<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
									+{project.skillsDemonstrated.length - 3} more
								</span>
							{/if}
						{/if}
					</div>

					{#if project.difficulty || project.grade}
						<div class="flex gap-4 text-xs text-gray-500">
							{#if project.difficulty}
								<span>Difficulty: {project.difficulty}</span>
							{/if}
							{#if project.grade}
								<span>Grade: {project.grade}</span>
							{/if}
						</div>
					{/if}
				</a>
			{/each}
		</div>

		{#if filteredProjects().length === 0}
			<div class="bg-white shadow rounded-lg p-8 text-center text-gray-500">
				No projects found for this filter
			</div>
		{/if}
	</main>
</div>
