import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('JanSamadhan Hero: Initializing...');
    init();
});

function init() {
    const container = document.getElementById('hero-canvas');
    if (!container) return;

    const isMobile = window.innerWidth < 768;

    // 1. Scene & Camera Setup
    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 10000);
    camera.position.set(0, 0, 1000);

    // 2. Renderer Setup
    const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(renderer.domElement);

    // 3. Objects & Interaction
    const mouse = new THREE.Vector2();
    const raycaster = new THREE.Raycaster();
    let hoveredState = null;

    const mapGroup = new THREE.Group();
    scene.add(mapGroup);

    // 4. Load Data
    console.log('JanSamadhan Hero: Loading map data...');
    fetch('js/india.json')
        .then(res => {
            if (!res.ok) throw new Error('HTTP error ' + res.status);
            return res.json();
        })
        .then(data => {
            console.log('JanSamadhan Hero: Map data fetched, processing features...');
            data.features.forEach(f => {
                const name = f.properties.name;
                const coordsArr = f.geometry.coordinates;
                if (f.geometry.type === 'Polygon') {
                    createShape(coordsArr[0], name);
                } else if (f.geometry.type === 'MultiPolygon') {
                    coordsArr.forEach(p => createShape(p[0], name));
                }
            });

            // 5. Scaling & Centering Logic
            const box = new THREE.Box3().setFromObject(mapGroup);
            const size = box.getSize(new THREE.Vector3());
            console.log('JanSamadhan Hero: Original map dimensions:', size.x, size.y);

            const targetWidth = isMobile ? 350 : 450;
            const scale = targetWidth / Math.max(size.x, size.y);
            mapGroup.scale.set(scale, scale, scale);

            // Re-center based on scaled dimensions
            const scaledBox = new THREE.Box3().setFromObject(mapGroup);
            const center = scaledBox.getCenter(new THREE.Vector3());
            mapGroup.position.x = -center.x;
            mapGroup.position.y = -center.y;

            // Positioning: Shift map to the right on desktop (but not too far)
            if (!isMobile) {
                mapGroup.position.x += 40; 
            } else {
                mapGroup.position.y -= 20; // Lower slightly on mobile
            }

            console.log('JanSamadhan Hero: Map initialized successfully.');
        })
        .catch(err => {
            console.error('JanSamadhan Hero: Failed to load map.', err);
            // Fallback: Add a simple glowing orb if map fails
            const fallbackGeo = new THREE.IcosahedronGeometry(100, 2);
            const fallbackMat = new THREE.MeshBasicMaterial({ color: 0x00eaff, wireframe: true, transparent: true, opacity: 0.2 });
            scene.add(new THREE.Mesh(fallbackGeo, fallbackMat));
        });

    function createShape(coords, stateName) {
        if (!coords || coords.length < 3) return;
        
        const shape = new THREE.Shape();
        shape.moveTo(coords[0][0], coords[0][1]);
        for (let i = 1; i < coords.length; i++) {
            shape.lineTo(coords[i][0], coords[i][1]);
        }

        const extrudeSettings = {
            depth: 6,
            bevelEnabled: true,
            bevelSegments: 1,
            bevelSize: 0.3,
            bevelThickness: 0.3
        };

        const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);

        const wireMat = new THREE.MeshBasicMaterial({
            color: 0x00eaff,
            wireframe: true,
            transparent: true,
            opacity: 0.2,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        const faceMat = new THREE.MeshBasicMaterial({
            color: 0x007cf0,
            transparent: true,
            opacity: 0.1,
            blending: THREE.AdditiveBlending,
            side: THREE.DoubleSide,
            depthWrite: false
        });

        const mesh = new THREE.Mesh(geometry, [faceMat, wireMat]);
        mesh.userData = { stateName, isState: true, originalOpacity: 0.1 };
        mapGroup.add(mesh);
    }

    // 6. Particle Field
    const particleCount = isMobile ? 80 : 200;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 2000;
        positions[i + 1] = (Math.random() - 0.5) * 1500;
        positions[i + 2] = (Math.random() - 0.5) * 1000;
    }
    const particleGeo = new THREE.BufferGeometry();
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const particleMat = new THREE.PointsMaterial({
        color: 0x00eaff,
        size: 1.5,
        transparent: true,
        opacity: 0.3,
        blending: THREE.AdditiveBlending
    });
    const points = new THREE.Points(particleGeo, particleMat);
    scene.add(points);

    // 7. Post-processing (Bloom)
    let composer;
    if (!isMobile) {
        composer = new EffectComposer(renderer);
        composer.addPass(new RenderPass(scene, camera));
        const bloom = new UnrealBloomPass(
            new THREE.Vector2(container.clientWidth, container.clientHeight),
            0.5, 0.4, 0.85
        );
        composer.addPass(bloom);
    }

    // 8. Animation & Interaction
    function onMouseMove(event) {
        const rect = container.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    }
    container.addEventListener('mousemove', onMouseMove);

    const clock = new THREE.Clock();
    function animate() {
        requestAnimationFrame(animate);
        const elapsed = clock.getElapsedTime();

        // Subtle motion
        mapGroup.rotation.y = Math.sin(elapsed * 0.4) * 0.1;
        mapGroup.rotation.x = Math.cos(elapsed * 0.3) * 0.05;
        mapGroup.position.y += Math.sin(elapsed * 1.5) * 0.05; // Extra smooth float

        // Particle rotation
        points.rotation.y += 0.0002;

        // Interaction (Raycasting)
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(mapGroup.children, true);
        if (intersects.length > 0) {
            const obj = intersects[0].object;
            if (obj.userData.isState && hoveredState !== obj) {
                if (hoveredState) resetState(hoveredState);
                hoveredState = obj;
                highlightState(hoveredState);
            }
        } else {
            if (hoveredState) resetState(hoveredState);
            hoveredState = null;
        }

        if (composer) composer.render();
        else renderer.render(scene, camera);
    }

    function highlightState(state) {
        const mats = Array.isArray(state.material) ? state.material : [state.material];
        mats[0].opacity = 0.4;
        mats[0].color.setHex(0x00eaff);
        document.body.style.cursor = 'pointer';
    }

    function resetState(state) {
        const mats = Array.isArray(state.material) ? state.material : [state.material];
        mats[0].opacity = state.userData.originalOpacity;
        mats[0].color.setHex(0x007cf0);
        document.body.style.cursor = 'default';
    }

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
        if (composer) composer.setSize(container.clientWidth, container.clientHeight);
    });
}