<script lang="ts">
	import '../app.css';
	import { authStore } from '$lib/stores/auth.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import Navigation from '$lib/components/Navigation.svelte';

	let { children } = $props();

	// Check authentication and redirect if needed
	onMount(() => {
		// Wait for auth to initialize
		const checkAuth = setInterval(() => {
			if (!authStore.loading) {
				clearInterval(checkAuth);

				// Get current path
				const currentPath = window.location.pathname;

				// If not authenticated and not on login page, redirect to login
				if (!authStore.user && currentPath !== '/login') {
					goto('/login');
				}

				// If authenticated and on login page, redirect to home
				if (authStore.user && currentPath === '/login') {
					goto('/');
				}
			}
		}, 100);

		// Cleanup
		return () => clearInterval(checkAuth);
	});

	// Show navigation on all pages except login
	let showNavigation = $derived($page.url.pathname !== '/login' && authStore.user);
</script>

{#if authStore.loading}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<h1 class="text-2xl font-bold mb-4">Loading...</h1>
			<p class="text-gray-600">Please wait</p>
		</div>
	</div>
{:else}
	<div class="min-h-screen bg-gray-50">
		{#if showNavigation}
			<Navigation />
		{/if}
		{@render children?.()}
	</div>
{/if}
