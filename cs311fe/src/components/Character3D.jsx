import React, { Suspense, useEffect, useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF, useAnimations } from '@react-three/drei'

function Model() {
  const group = useRef()
  const { scene, animations } = useGLTF('/src/model/man/source/man_sitting.glb')
  const { actions } = useAnimations(animations, group)

  useEffect(() => {
    // Log the scene graph to the console to inspect its structure
    console.log(scene);

    // Traverse the scene to find and hide static meshes
    scene.traverse((object) => {
      // This will hide any mesh that is not a rigged character (SkinnedMesh)
      if (object.isMesh && !object.isSkinnedMesh) {
        object.visible = false;
      }
    });
  }, [scene]);

  useEffect(() => {
    if (actions && Object.keys(actions).length > 0) {
      // Play the first available animation
      const animationName = Object.keys(actions)[0]
      actions[animationName].play()
    }
  }, [actions])

  return <primitive ref={group} object={scene} scale={1.5} position={[0, -1.5, 0]} />
}

const Character3D = () => {
  return (
    <Canvas camera={{ position: [0, -0.2, 3], fov: 40 }}>
      <ambientLight intensity={0.2} />
      <directionalLight position={[10, 10, 5]} intensity={1.5} />
      <Suspense fallback={null}>
        <Model />
      </Suspense>
      <OrbitControls 
        enableZoom={false} 
        enablePan={false} 
        minPolarAngle={Math.PI / 2.5}
        maxPolarAngle={Math.PI / 2.2}
        minAzimuthAngle={-Math.PI / 8}
        maxAzimuthAngle={Math.PI / 8}
      />
    </Canvas>
  )
}

export default Character3D
