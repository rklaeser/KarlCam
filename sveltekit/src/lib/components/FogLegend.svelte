<script lang="ts">
</script>

<div
	class="absolute bottom-6 left-6 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-gray-200"
	style="z-index: 1000"
>
	<h4 class="font-semibold text-gray-800 mb-3 flex items-center text-sm">
		Visibility
		<a
			href="/measuring-fog"
			class="ml-2 w-4 h-4 bg-blue-100 text-blue-600 rounded-full text-xs font-bold hover:bg-blue-200 transition-colors inline-flex items-center justify-center"
			title="View fog intensity examples"
		>
			?
		</a>
	</h4>
	<div class="space-y-2">
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #6c757d"></div>
			<span class="text-xs">No Data</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #28a745"></div>
			<span class="text-xs">Clear (0-20)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #ffc107"></div>
			<span class="text-xs">Light Fog (20-40)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #fd7e14"></div>
			<span class="text-xs">Moderate Fog (40-60)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #dc3545"></div>
			<span class="text-xs">Heavy Fog (60-80)</span>
		</div>
		<div class="flex items-center gap-2">
			<div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #6f42c1"></div>
			<span class="text-xs">Very Heavy Fog (80+)</span>
		</div>
	</div>
</div>
