import { Storage } from '@google-cloud/storage';
import { env } from '$env/dynamic/private';

let storage: Storage | null = null;

/**
 * Get bucket name from environment variable, defaulting to production bucket
 * (consolidated single bucket for all environments)
 */
function getBucketName(): string {
	return env.BUCKET_NAME || 'karlcam-production-data';
}

/**
 * Get or create Cloud Storage client
 */
function getStorageClient(): Storage {
	if (!storage) {
		// Firebase Admin SDK credentials work for Cloud Storage too
		if (env.FIREBASE_PROJECT_ID && env.FIREBASE_CLIENT_EMAIL && env.FIREBASE_PRIVATE_KEY) {
			storage = new Storage({
				projectId: env.FIREBASE_PROJECT_ID,
				credentials: {
					client_email: env.FIREBASE_CLIENT_EMAIL,
					private_key: env.FIREBASE_PRIVATE_KEY.replace(/\\n/gm, '\n')
				}
			});
		} else {
			throw new Error('Cloud Storage credentials not configured');
		}
	}
	return storage;
}

/**
 * Upload image buffer to Cloud Storage
 * @returns Public URL of uploaded image
 */
export async function uploadImage(
	imageBuffer: ArrayBuffer,
	cameraId: string,
	timestamp: Date
): Promise<string> {
	const storage = getStorageClient();
	const bucketName = getBucketName();
	const bucket = storage.bucket(bucketName);

	// Create filename: cameraId_timestamp.jpg
	const isoTimestamp = timestamp.toISOString().replace(/[:.]/g, '-').replace('Z', '');
	const filename = `${cameraId}_${isoTimestamp}.jpg`;
	const filepath = `raw_images/${filename}`;

	// Upload to Cloud Storage
	const file = bucket.file(filepath);
	await file.save(Buffer.from(imageBuffer), {
		metadata: {
			contentType: 'image/jpeg',
			cacheControl: 'public, max-age=3600'
		}
	});

	// Don't call makePublic() - bucket has uniform bucket-level access enabled
	// which means public access is controlled at the bucket level, not per-file

	// Return the public URL
	return `https://storage.googleapis.com/${bucketName}/${filepath}`;
}
