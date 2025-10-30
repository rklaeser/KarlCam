import { initializeApp, cert, getApps, type App } from 'firebase-admin/app';
import { getFirestore, type Firestore } from 'firebase-admin/firestore';
import {
	FIREBASE_PROJECT_ID,
	FIREBASE_CLIENT_EMAIL,
	FIREBASE_PRIVATE_KEY
} from '$env/static/private';

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
		app = initializeApp({
			credential: cert({
				projectId: FIREBASE_PROJECT_ID,
				clientEmail: FIREBASE_CLIENT_EMAIL,
				// Replace literal \n with actual newlines
				privateKey: FIREBASE_PRIVATE_KEY.replace(/\\n/gm, '\n')
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
