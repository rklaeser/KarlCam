<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<div class="min-h-screen bg-gray-50">
	<!-- Header -->
	<div class="bg-white shadow">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex justify-between items-center">
				<div>
					<h1 class="text-3xl font-bold text-gray-900">Career Narrative</h1>
					<p class="text-sm text-gray-600 mt-1">
						{data.description}
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

	<!-- Content -->
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="space-y-8">
			<!-- Background -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-2xl font-semibold mb-4">Background</h2>
				<p class="text-gray-700 mb-6">{data.background.summary}</p>

				<h3 class="text-lg font-semibold mb-3">Previous Roles</h3>
				<div class="space-y-6">
					{#each data.background.previousRoles as role}
						<div class="border-l-4 border-blue-500 pl-6">
							<h4 class="font-medium text-gray-900">{role.title} at {role.company}</h4>
							<p class="text-sm text-gray-600 mb-3">{role.duration}{role.endDate ? ` • Ended ${role.endDate}` : ''}</p>

							<div class="mb-3">
								<p class="text-sm font-medium text-gray-900 mb-1">Key Accomplishments:</p>
								<ul class="list-disc list-inside space-y-1">
									{#each role.keyAccomplishments as accomplishment}
										<li class="text-sm text-gray-700">{accomplishment}</li>
									{/each}
								</ul>
							</div>

							<div>
								<p class="text-sm font-medium text-gray-900 mb-1">Technical Environment:</p>
								<div class="flex flex-wrap gap-2">
									{#each role.technicalEnvironment as tech}
										<span class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">
											{tech}
										</span>
									{/each}
								</div>
							</div>
						</div>
					{/each}
				</div>

				<h3 class="text-lg font-semibold mb-3 mt-6">Core Strengths</h3>
				<ul class="list-disc list-inside space-y-1">
					{#each data.background.coreStrengths as strength}
						<li class="text-gray-700">{strength}</li>
					{/each}
				</ul>
			</div>

			<!-- Transition -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-2xl font-semibold mb-4">Career Transition</h2>

				<div class="mb-6">
					<h3 class="text-lg font-semibold mb-3">Target Field</h3>
					<p class="text-xl text-blue-600 font-medium">{data.transition.targetField}</p>
				</div>

				<div class="mb-6">
					<h3 class="text-lg font-semibold mb-3">Target Roles</h3>
					<div class="space-y-3">
						{#each data.transition.targetRoles as role}
							<div class="p-4 bg-gray-50 rounded-lg">
								<div class="flex items-start justify-between mb-2">
									<h4 class="font-medium text-gray-900">{role.title}</h4>
									<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
										class:bg-red-100={role.priority === 'high'}
										class:text-red-800={role.priority === 'high'}
										class:bg-yellow-100={role.priority === 'medium'}
										class:text-yellow-800={role.priority === 'medium'}
										class:bg-gray-100={role.priority === 'low'}
										class:text-gray-800={role.priority === 'low'}
									>
										{role.priority} priority
									</span>
								</div>
								<p class="text-sm text-gray-700">{role.reasoning}</p>
							</div>
						{/each}
					</div>
				</div>

				<div class="mb-6">
					<h3 class="text-lg font-semibold mb-3">Motivation</h3>
					<p class="text-gray-700 mb-3"><strong>Primary:</strong> {data.transition.motivation.primary}</p>

					<p class="text-sm font-medium text-gray-900 mb-2">Specific Drivers:</p>
					<ul class="list-disc list-inside space-y-1">
						{#each data.transition.motivation.specificDrivers as driver}
							<li class="text-sm text-gray-700">{driver}</li>
						{/each}
					</ul>

					<p class="text-sm text-gray-700 mt-3">
						<strong>Pivot Rationale:</strong> {data.transition.motivation.pivotRationale}
					</p>
				</div>

				<div>
					<h3 class="text-lg font-semibold mb-3">Commitment</h3>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div class="p-4 bg-blue-50 rounded-lg">
							<p class="text-sm font-medium text-gray-900 mb-1">Level</p>
							<p class="text-sm text-gray-700">{data.transition.commitment.level}</p>
						</div>
						<div class="p-4 bg-blue-50 rounded-lg">
							<p class="text-sm font-medium text-gray-900 mb-1">Evidence</p>
							<p class="text-sm text-gray-700">{data.transition.commitment.evidence}</p>
						</div>
						<div class="p-4 bg-blue-50 rounded-lg">
							<p class="text-sm font-medium text-gray-900 mb-1">Time Invested</p>
							<p class="text-sm text-gray-700">{data.transition.commitment.timeInvested}</p>
						</div>
						<div class="p-4 bg-blue-50 rounded-lg">
							<p class="text-sm font-medium text-gray-900 mb-1">Willingness to Invest</p>
							<p class="text-sm text-gray-700">{data.transition.commitment.willingnessToInvest}</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Preparation -->
			<div class="bg-white shadow rounded-lg p-6">
				<h2 class="text-2xl font-semibold mb-4">Preparation</h2>
				<p class="text-gray-700">{data.preparation.overview}</p>
			</div>
		</div>
	</main>
</div>
