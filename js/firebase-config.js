// Firebase Configuration for JanSamadhan
// Project: jansamadhan-2c298

const firebaseConfig = {
    apiKey: "AIzaSyAMiVmijGEaxxDPO7elhlZYrj3Ok6cMoBI",
    authDomain: "jansamadhan-2c298.firebaseapp.com",
    projectId: "jansamadhan-2c298",
    storageBucket: "jansamadhan-2c298.firebasestorage.app",
    messagingSenderId: "3946894687",
    appId: "1:3946894687:web:dfea63a01dfaf696ced2ea",
    measurementId: "G-CTG88WT58R"
};

// Initialize Firebase (using compat SDKs for script-tag compatibility)
if (typeof firebase !== 'undefined') {
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }

    // Make Firebase services globally available on the window object
    window.auth = firebase.auth();
    window.db = firebase.firestore();
    window.storage = firebase.storage();

    // Enable Offline Persistence for Firestore
    window.db.enablePersistence({ synchronizeTabs: true })
        .catch((err) => {
            if (err.code === 'failed-precondition') {
                console.warn("Firestore Persistence: Multiple tabs open, persistence can only be enabled in one tab at a time.");
            } else if (err.code === 'unimplemented') {
                console.warn("Firestore Persistence: The current browser does not support all of the features required to enable persistence.");
            }
        });

    console.log("🔥 JanSamadhan: Firebase connected to jansamadhan-2c298");
} else {
    console.error("❌ Firebase SDK not loaded! Check your internet connection or script tags.");
}
