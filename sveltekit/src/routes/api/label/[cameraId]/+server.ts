import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFirestoreAdmin } from '$lib/server/firebase';
import { uploadImage } from '$lib/server/storage';
import { GEMINI_API_KEY } from '$env/static/private';
import type { CameraLabel, LabelResponse } from '$lib/types';

interface GeminiResponse {
	fog_score: number;
	fog_level: string;
	confidence: number;
	reasoning: string;
	weather_conditions: string[];
}

interface LabelResult {
	geminiResponse: GeminiResponse;
	imageBuffer: ArrayBuffer;
}

/**
 * Get the most recent label for a camera
 */
async function getLatestLabel(cameraId: string, maxAgeMinutes: number = 30): Promise<CameraLabel | null> {
	const db = getFirestoreAdmin();
	const cutoffTime = new Date(Date.now() - maxAgeMinutes * 60 * 1000);

	const snapshot = await db.collection('labels')
		.where('camera_id', '==', cameraId)
		.where('timestamp', '>=', cutoffTime)
		.orderBy('timestamp', 'desc')
		.limit(1)
		.get();

	if (snapshot.empty) {
		return null;
	}

	const data = snapshot.docs[0].data();
	return {
		camera_id: data.camera_id,
		camera_name: data.camera_name,
		timestamp: data.timestamp.toDate(),
		image_url: data.image_url,
		fog_score: data.fog_score,
		fog_level: data.fog_level,
		confidence: data.confidence,
		reasoning: data.reasoning,
		weather_conditions: data.weather_conditions,
		latitude: data.latitude,
		longitude: data.longitude,
		source_environment: data.source_environment,
		labeler_name: data.labeler_name
	};
}

/**
 * Label an image with Gemini AI
 * Returns both the Gemini response and the image buffer for uploading to Cloud Storage
 */
async function labelImageWithGemini(imageUrl: string, cameraName: string): Promise<LabelResult | null> {
	try {
		// Parse URL and extract credentials if present
		let fetchUrl = imageUrl;
		let authHeader: { Authorization?: string } = {};

		try {
			const urlObj = new URL(imageUrl);

			// Extract HTTP basic auth credentials if present
			if (urlObj.username || urlObj.password) {
				console.log(`[API] Detected HTTP basic auth in URL for ${cameraName}`);

				// Create Authorization header
				const credentials = Buffer.from(`${urlObj.username}:${urlObj.password}`).toString('base64');
				authHeader.Authorization = `Basic ${credentials}`;

				// Remove credentials from URL
				urlObj.username = '';
				urlObj.password = '';
				fetchUrl = urlObj.toString();
			}
		} catch (e) {
			console.warn(`[API] Invalid image URL: ${imageUrl}`);
			return null;
		}

		// 1. Fetch image from URL with optional auth header
		const imageResponse = await fetch(fetchUrl, {
			headers: authHeader
		});

		if (!imageResponse.ok) {
			console.warn(`[API] Failed to fetch image: ${imageResponse.statusText}`);
			return null;
		}

		// 2. Convert to base64
		const imageBuffer = await imageResponse.arrayBuffer();
		const base64Image = Buffer.from(imageBuffer).toString('base64');

		// 3. Call Gemini API
		const apiResponse = await fetch(
			`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GEMINI_API_KEY}`,
			{
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					contents: [{
						parts: [
							{
								text: `Analyze this webcam image from ${cameraName} in San Francisco for fog conditions.

Return JSON with:
- fog_score: 0-100 (0=clear, 100=very heavy fog)
- fog_level: "Clear", "Light Fog", "Moderate Fog", "Heavy Fog", or "Very Heavy Fog"
- confidence: 0.0-1.0
- reasoning: Brief explanation
- weather_conditions: Array like ["fog", "overcast", "clear"]

Focus on visibility and atmospheric haze.`
							},
							{
								inline_data: {
									mime_type: 'image/jpeg',
									data: base64Image
								}
							}
						]
					}]
				})
			}
		);

		if (!apiResponse.ok) {
			const errorText = await apiResponse.text();
			console.warn(`[API] Gemini API error: ${apiResponse.statusText}`);
			return null;
		}

		const result = await apiResponse.json();
		const text = result.candidates[0].content.parts[0].text;

		// Extract JSON from response
		const jsonMatch = text.match(/\{[\s\S]*\}/);
		if (!jsonMatch) {
			console.warn(`[API] Failed to parse Gemini response`);
			return null;
		}

		const geminiResponse: GeminiResponse = JSON.parse(jsonMatch[0]);

		// Return both the Gemini response and the image buffer
		return {
			geminiResponse,
			imageBuffer
		};
	} catch (error) {
		console.warn(`[API] Error in labelImageWithGemini:`, error instanceof Error ? error.message : error);
		return null;
	}
}

/**
 * Save a label to Firestore
 */
async function saveLabel(label: CameraLabel): Promise<void> {
	const db = getFirestoreAdmin();

	await db.collection('labels').add({
		...label,
		labeled_at: new Date()
	});
}

/**
 * API Endpoint: GET /api/label/{cameraId}
 *
 * Returns a label for the camera, either from Firestore cache or freshly generated
 */
export const GET: RequestHandler = async ({ params }) => {
	const { cameraId } = params;

	try {
		console.log(`[API] Received label request for camera: ${cameraId}`);

		// Check for recent label
		const recentLabel = await getLatestLabel(cameraId, 30);
		if (recentLabel) {
			console.log(`[API] Found recent label in Firestore for ${cameraId}`);
			return json<LabelResponse>({
				source: 'firestore',
				label: recentLabel
			});
		}

		console.log(`[API] No recent label found, generating new label for ${cameraId}`);

		// No recent label - generate new one
		const db = getFirestoreAdmin();
		const webcamDoc = await db.collection('webcams').doc(cameraId).get();

		if (!webcamDoc.exists) {
			console.error(`[API] Camera not found: ${cameraId}`);
			return json({ error: 'Camera not found' }, { status: 404 });
		}

		const webcam = webcamDoc.data()!;
		console.log(`[API] Fetched webcam data for ${cameraId}: ${webcam.name}`);

		// Label image with Gemini
		console.log(`[API] Calling Gemini to label image for ${cameraId}`);
		const labelResult = await labelImageWithGemini(webcam.url, webcam.name);

		// If labeling failed (image unavailable, fetch error, etc.), return null label
		if (!labelResult) {
			console.warn(`[API] Unable to generate label for ${cameraId} - camera unavailable`);
			return json<LabelResponse>({
				source: 'unavailable',
				label: null
			});
		}

		const { geminiResponse, imageBuffer } = labelResult;
		console.log(`[API] Gemini result for ${cameraId}:`, geminiResponse);

		// Upload image to Cloud Storage
		const now = new Date();
		console.log(`[API] Uploading image to Cloud Storage for ${cameraId}`);
		const cloudStorageUrl = await uploadImage(imageBuffer, cameraId, now);
		console.log(`[API] Image uploaded to: ${cloudStorageUrl}`);

		// Create label with Cloud Storage URL
		const label: CameraLabel = {
			camera_id: cameraId,
			camera_name: webcam.name,
			timestamp: now,
			image_url: cloudStorageUrl, // Use Cloud Storage URL, not webcam URL
			fog_score: geminiResponse.fog_score,
			fog_level: geminiResponse.fog_level,
			confidence: geminiResponse.confidence,
			reasoning: geminiResponse.reasoning,
			weather_conditions: geminiResponse.weather_conditions,
			latitude: webcam.latitude,
			longitude: webcam.longitude,
			labeler_name: 'gemini-2.0-flash-exp',
			source_environment: 'on-demand'
		};

		// Save to Firestore
		console.log(`[API] Saving label to Firestore for ${cameraId}`);
		await saveLabel(label);

		console.log(`[API] Successfully generated and saved label for ${cameraId}`);
		return json<LabelResponse>({
			source: 'on-demand',
			label
		});
	} catch (error) {
		console.error(`[API] Unexpected error labeling image for ${cameraId}:`, error);
		return json(
			{ error: error instanceof Error ? error.message : 'Unknown error' },
			{ status: 500 }
		);
	}
};
