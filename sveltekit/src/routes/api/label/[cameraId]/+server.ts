import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { getFirestoreAdmin } from '$lib/server/firebase';
import { env } from '$env/dynamic/private';
import type { CameraLabel, LabelResponse } from '$lib/types';

interface GeminiResponse {
	fog_score: number;
	fog_level: string;
	confidence: number;
	reasoning: string;
	weather_conditions: string[];
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
 */
async function labelImageWithGemini(imageUrl: string, cameraName: string): Promise<GeminiResponse> {
	// 1. Fetch image from URL
	const imageResponse = await fetch(imageUrl);
	if (!imageResponse.ok) {
		throw new Error(`Failed to fetch image: ${imageResponse.statusText}`);
	}

	// 2. Convert to base64
	const imageBuffer = await imageResponse.arrayBuffer();
	const base64Image = Buffer.from(imageBuffer).toString('base64');

	// 3. Call Gemini API
	const geminiResponse = await fetch(
		`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${env.GEMINI_API_KEY}`,
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

	if (!geminiResponse.ok) {
		const errorText = await geminiResponse.text();
		throw new Error(`Gemini API error: ${geminiResponse.statusText} - ${errorText}`);
	}

	const result = await geminiResponse.json();
	const text = result.candidates[0].content.parts[0].text;

	// Extract JSON from response
	const jsonMatch = text.match(/\{[\s\S]*\}/);
	if (!jsonMatch) {
		throw new Error('Failed to parse Gemini response');
	}

	return JSON.parse(jsonMatch[0]);
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
		// Check for recent label
		const recentLabel = await getLatestLabel(cameraId, 30);
		if (recentLabel) {
			return json<LabelResponse>({
				source: 'firestore',
				label: recentLabel
			});
		}

		// No recent label - generate new one
		const db = getFirestoreAdmin();
		const webcamDoc = await db.collection('webcams').doc(cameraId).get();

		if (!webcamDoc.exists) {
			return json({ error: 'Camera not found' }, { status: 404 });
		}

		const webcam = webcamDoc.data()!;

		// Label image with Gemini
		const geminiResult = await labelImageWithGemini(webcam.url, webcam.name);

		// Create label
		const now = new Date();
		const label: CameraLabel = {
			camera_id: cameraId,
			camera_name: webcam.name,
			timestamp: now,
			image_url: webcam.url,
			fog_score: geminiResult.fog_score,
			fog_level: geminiResult.fog_level,
			confidence: geminiResult.confidence,
			reasoning: geminiResult.reasoning,
			weather_conditions: geminiResult.weather_conditions,
			latitude: webcam.latitude,
			longitude: webcam.longitude,
			labeler_name: 'gemini-2.0-flash-exp',
			source_environment: 'on-demand'
		};

		// Save to Firestore
		await saveLabel(label);

		return json<LabelResponse>({
			source: 'on-demand',
			label
		});
	} catch (error) {
		console.error('Error labeling image:', error);
		return json(
			{ error: error instanceof Error ? error.message : 'Unknown error' },
			{ status: 500 }
		);
	}
};
