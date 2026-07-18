import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useEffect, useRef, useState } from 'react';

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  return reduced;
}

function DemandTicker({ reducedMotion }) {
  const invalidate = useThree((state) => state.invalidate);

  useEffect(() => {
    invalidate();
    if (reducedMotion) return undefined;
    const timer = window.setInterval(invalidate, 80);
    return () => window.clearInterval(timer);
  }, [invalidate, reducedMotion]);

  return null;
}

function SolarPanel({ position }) {
  const cells = Array.from({ length: 18 }, (_, index) => {
    const column = index % 6;
    const row = Math.floor(index / 6);
    return (
      <mesh key={index} position={[-1.45 + column * 0.58, -0.55 + row * 0.55, 0.035]}>
        <boxGeometry args={[0.49, 0.45, 0.025]} />
        <meshStandardMaterial color="#162e3d" metalness={0.35} roughness={0.32} />
      </mesh>
    );
  });

  return (
    <group position={position} rotation={[Math.PI / 2, 0, 0]}>
      <mesh>
        <boxGeometry args={[3.65, 1.85, 0.08]} />
        <meshStandardMaterial color="#d88419" metalness={0.45} roughness={0.4} />
      </mesh>
      {cells}
    </group>
  );
}

function Camera({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.4, 0]}>
        <cylinderGeometry args={[0.29, 0.34, 0.85, 20]} />
        <meshStandardMaterial color="#e6d3a9" metalness={0.62} roughness={0.28} />
      </mesh>
      <mesh position={[0, 0.86, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 0.08, 20]} />
        <meshStandardMaterial color="#17100b" metalness={0.25} roughness={0.18} />
      </mesh>
      <mesh position={[0, 0.91, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.22, 20]} />
        <meshStandardMaterial color="#ff9f24" emissive="#7b2e00" emissiveIntensity={0.45} />
      </mesh>
    </group>
  );
}

function Observatory({ reducedMotion }) {
  const craft = useRef(null);

  useFrame(({ clock }) => {
    if (!craft.current || reducedMotion) return;
    const t = clock.getElapsedTime();
    craft.current.rotation.y = -0.62 + Math.sin(t * 0.28) * 0.12;
    craft.current.rotation.x = 0.2 + Math.cos(t * 0.22) * 0.035;
    craft.current.position.y = Math.sin(t * 0.5) * 0.09;
  });

  return (
    <group ref={craft} rotation={[0.2, -0.62, -0.08]} scale={0.78}>
      <SolarPanel position={[-3.18, 0, 0]} />
      <SolarPanel position={[3.18, 0, 0]} />
      <mesh>
        <boxGeometry args={[2.45, 2.05, 2.3]} />
        <meshStandardMaterial color="#d7b46e" metalness={0.58} roughness={0.4} />
      </mesh>
      <mesh position={[0, 1.08, 0]}>
        <boxGeometry args={[2.05, 0.16, 1.9]} />
        <meshStandardMaterial color="#2a2116" metalness={0.6} roughness={0.35} />
      </mesh>
      <Camera position={[-0.62, 1.18, -0.52]} />
      <Camera position={[0.62, 1.18, -0.52]} />
      <Camera position={[-0.62, 1.18, 0.52]} />
      <Camera position={[0.62, 1.18, 0.52]} />
      <mesh position={[0, -1.4, 0]}>
        <cylinderGeometry args={[0.36, 0.52, 0.86, 16]} />
        <meshStandardMaterial color="#3b3328" metalness={0.68} roughness={0.3} />
      </mesh>
    </group>
  );
}

function Scene({ reducedMotion }) {
  return (
    <>
      <color attach="background" args={["#160d08"]} />
      <ambientLight intensity={0.75} />
      <directionalLight position={[4, 6, 5]} intensity={3.4} color="#ffbd62" />
      <pointLight position={[-5, -2, -2]} intensity={16} distance={12} color="#f97316" />
      <Observatory reducedMotion={reducedMotion} />
      <mesh rotation={[Math.PI / 2.7, 0.15, -0.2]}>
        <torusGeometry args={[4.1, 0.012, 6, 96]} />
        <meshBasicMaterial color="#f6a33b" transparent opacity={0.52} />
      </mesh>
      <mesh position={[-3.8, 2.35, -1.5]}>
        <sphereGeometry args={[0.13, 12, 12]} />
        <meshBasicMaterial color="#fff1c7" />
      </mesh>
      <points rotation={[0.2, 0.4, 0]}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[new Float32Array([
              -4.5, -2.2, -2.4, -3.7, 2.4, -2.1, -1.8, -2.8, -3.1,
              1.6, 2.8, -2.7, 3.8, -1.8, -2.2, 4.4, 2.1, -3.2,
            ]), 3]}
          />
        </bufferGeometry>
        <pointsMaterial color="#ffd79a" size={0.065} sizeAttenuation />
      </points>
      <DemandTicker reducedMotion={reducedMotion} />
    </>
  );
}

export default function TessHero() {
  const reducedMotion = useReducedMotion();

  return (
    <figure className="relative h-full w-full">
      <Canvas
        camera={{ position: [0, 1.1, 8.3], fov: 42 }}
        dpr={[1, 1.5]}
        frameloop="demand"
        gl={{ antialias: false, powerPreference: 'low-power' }}
      >
        <Scene reducedMotion={reducedMotion} />
      </Canvas>
      <figcaption className="pointer-events-none absolute bottom-0 left-0 border-r border-t border-orange-500/30 bg-stone-950/85 px-3 py-2 font-mono text-[0.62rem] uppercase tracking-[0.12em] text-orange-100">
        Stylized illustration, not flight data
      </figcaption>
    </figure>
  );
}
