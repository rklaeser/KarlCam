<script lang="ts">
	interface DashboardCard {
		title: string;
		description: string;
		href: string;
		icon: string;
	}

	const sections: DashboardCard[] = [
		{
			title: 'Companies',
			description: 'Track companies of interest and job application status',
			href: '/companies',
			icon: '🏢'
		},
		{
			title: 'Projects',
			description: 'Personal projects demonstrating skills and commitment',
			href: '/projects',
			icon: '🚀'
		},
		{
			title: 'Skills',
			description: 'Current skills and learning roadmap',
			href: '/skills',
			icon: '💡'
		},
		{
			title: 'Career Narrative',
			description: 'Background, transition story, and career goals',
			href: '/career-narrative',
			icon: '📖'
		},
		{
			title: 'Values & Criteria',
			description: 'Company evaluation criteria and domain preferences',
			href: '/values',
			icon: '⭐'
		},
		{
			title: 'Networking',
			description: 'Conferences, meetups, and networking opportunities',
			href: '/networking',
			icon: '🤝'
		},
		{
			title: 'Communities',
			description: 'Hackerspaces and technical communities',
			href: '/communities',
			icon: '👥'
		}
	];
</script>

<!-- Main Content -->
<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<div class="mb-8">
		<h2 class="text-3xl font-bold text-gray-900 mb-2">Dashboard</h2>
		<p class="text-gray-600">
			Career planning and job search tracking system
		</p>
	</div>

	<!-- Dashboard Cards -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
		{#each sections as section}
			<a
				href={section.href}
				class="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 group"
			>
				<div class="flex items-start gap-4">
					<div class="text-4xl">{section.icon}</div>
					<div class="flex-1">
						<h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 mb-2">
							{section.title}
						</h3>
						<p class="text-sm text-gray-600">
							{section.description}
						</p>
					</div>
				</div>
			</a>
		{/each}
	</div>
</main>
