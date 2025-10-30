import { initializeApp, cert, getApps, type App } from 'firebase-admin/app';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';
import { env } from '$env/dynamic/private';

let app: App;
let db: Firestore;

/**
 * Initialize Firebase Admin SDK
 * Uses singleton pattern to avoid re-initializing
 */
export function initializeFirebase(): Firestore {
	if (db) {
		return db;
	}

	// Check if already initialized
	if (getApps().length === 0) {
		if (!env.FIREBASE_PROJECT_ID || !env.FIREBASE_CLIENT_EMAIL || !env.FIREBASE_PRIVATE_KEY) {
			throw new Error('Firebase environment variables are not configured');
		}

		app = initializeApp({
			credential: cert({
				projectId: env.FIREBASE_PROJECT_ID,
				clientEmail: env.FIREBASE_CLIENT_EMAIL,
				// Replace literal \n with actual newlines
				privateKey: env.FIREBASE_PRIVATE_KEY.replace(/\\n/gm, '\n')
			})
		});
	} else {
		app = getApps()[0];
	}

	// Connect to karlcam-firestore database
	db = getFirestore(app, 'karlcam-firestore');
	return db;
}

/**
 * Get Firestore instance
 */
export function getDB(): Firestore {
	if (!db) {
		return initializeFirebase();
	}
	return db;
}

/**
 * Alias for getDB - for compatibility with API routes
 */
export function getFirestoreAdmin(): Firestore {
	return getDB();
}
