<script lang="ts">
	import type { PageData } from './$types';
	import type { ProjectStatus, ProjectCategory } from '$lib/types';

	let { data }: { data: PageData } = $props();
	const { project } = data;

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
			<div class="flex justify-between items-start">
				<div>
					<div class="flex items-center gap-3 mb-2">
						<span class="text-3xl">{getCategoryIcon(project.category)}</span>
						<h1 class="text-3xl font-bold text-gray-900">{project.name}</h1>
					</div>
					<p class="text-gray-600 mb-3">{project.summary}</p>
					<div class="flex items-center gap-3">
						<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStatusColor(project.status)}">
							{project.status}
						</span>
						{#if project.difficulty}
							<span class="text-sm text-gray-600">Difficulty: {project.difficulty}</span>
						{/if}
						{#if project.grade}
							<span class="text-sm text-gray-600">Grade: {project.grade}</span>
						{/if}
					</div>
				</div>
				<a
					href="/projects"
					class="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded border border-gray-300"
				>
					← Back to Projects
				</a>
			</div>
		</div>
	</div>

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main Column -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Description -->
				<div class="bg-white shadow rounded-lg p-6">
					<h2 class="text-xl font-semibold mb-4">Description</h2>
					<p class="text-gray-700 whitespace-pre-wrap">{project.description}</p>
				</div>

				<!-- Technical Highlights -->
				{#if project.technicalHighlights && project.technicalHighlights.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Technical Highlights</h2>
						<ul class="space-y-2">
							{#each project.technicalHighlights as highlight}
								<li class="flex items-start gap-2">
									<span class="text-blue-600 mt-1">✓</span>
									<span class="text-gray-700">{highlight}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Challenges -->
				{#if project.challenges && project.challenges.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Challenges</h2>
						<ul class="space-y-2">
							{#each project.challenges as challenge}
								<li class="flex items-start gap-2">
									<span class="text-yellow-600 mt-1">⚠</span>
									<span class="text-gray-700">{challenge}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Lessons Learned -->
				{#if project.lessonsLearned && project.lessonsLearned.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Lessons Learned</h2>
						<ul class="space-y-2">
							{#each project.lessonsLearned as lesson}
								<li class="flex items-start gap-2">
									<span class="text-green-600 mt-1">💡</span>
									<span class="text-gray-700">{lesson}</span>
								</li>
							{/each}
						</ul>
					</div>
				{/if}

				<!-- Relevance to Career -->
				{#if project.relevanceToCareer}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Relevance to Career</h2>
						<p class="text-gray-700 mb-4">{project.relevanceToCareer.primaryValue}</p>

						{#if project.relevanceToCareer.relevantToRoles && project.relevanceToCareer.relevantToRoles.length > 0}
							<div class="mb-4">
								<h3 class="text-sm font-medium text-gray-900 mb-2">Relevant to Roles:</h3>
								<ul class="list-disc list-inside space-y-1">
									{#each project.relevanceToCareer.relevantToRoles as role}
										<li class="text-sm text-gray-700">{role}</li>
									{/each}
								</ul>
							</div>
						{/if}

						{#if project.relevanceToCareer.transferableSkills && project.relevanceToCareer.transferableSkills.length > 0}
							<div>
								<h3 class="text-sm font-medium text-gray-900 mb-2">Transferable Skills:</h3>
								<ul class="list-disc list-inside space-y-1">
									{#each project.relevanceToCareer.transferableSkills as skill}
										<li class="text-sm text-gray-700">{skill}</li>
									{/each}
								</ul>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Notes -->
				{#if project.notes}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-xl font-semibold mb-4">Notes</h2>
						<p class="text-gray-700 whitespace-pre-wrap">{project.notes}</p>
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-6">
				<!-- Timeline -->
				<div class="bg-white shadow rounded-lg p-6">
					<h2 class="text-lg font-semibold mb-4">Timeline</h2>
					<div class="space-y-2 text-sm">
						{#if project.startDate}
							<div>
								<span class="text-gray-600">Started:</span>
								<span class="text-gray-900 font-medium">{project.startDate}</span>
							</div>
						{/if}
						{#if project.completedDate}
							<div>
								<span class="text-gray-600">Completed:</span>
								<span class="text-gray-900 font-medium">{project.completedDate}</span>
							</div>
						{/if}
						{#if project.reflectionDate}
							<div>
								<span class="text-gray-600">Reflected:</span>
								<span class="text-gray-900 font-medium">{project.reflectionDate}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Skills Demonstrated -->
				{#if project.skillsDemonstrated && project.skillsDemonstrated.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Skills Demonstrated</h2>
						<div class="flex flex-wrap gap-2">
							{#each project.skillsDemonstrated as skill}
								<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-blue-50 text-blue-700">
									{skill}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Links -->
				<div class="bg-white shadow rounded-lg p-6">
					<h2 class="text-lg font-semibold mb-4">Links</h2>
					<div class="space-y-2">
						{#if project.githubRepo}
							<a href={project.githubRepo} target="_blank" rel="noopener noreferrer" class="block text-blue-600 hover:underline">
								→ GitHub Repository
							</a>
						{/if}
						{#if project.demoUrl}
							<a href={project.demoUrl} target="_blank" rel="noopener noreferrer" class="block text-blue-600 hover:underline">
								→ Live Demo
							</a>
						{/if}
						{#if project.documentation}
							<a href={project.documentation} target="_blank" rel="noopener noreferrer" class="block text-blue-600 hover:underline">
								→ Documentation
							</a>
						{/if}
					</div>
				</div>

				<!-- Tags -->
				{#if project.tags && project.tags.length > 0}
					<div class="bg-white shadow rounded-lg p-6">
						<h2 class="text-lg font-semibold mb-4">Tags</h2>
						<div class="flex flex-wrap gap-2">
							{#each project.tags as tag}
								<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
									{tag}
								</span>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	</main>
</div>
