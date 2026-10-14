import { useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'
import type { MapPoints } from '../api/types'

interface Scene3DProps {
  points: MapPoints
  progressRef: React.MutableRefObject<{ value: number }>
}

const TERRAIN_WIDTH = 96
const TERRAIN_DEPTH = 60
const SEGMENTS_X = 120
const SEGMENTS_Z = 76

const DESTINO_COLORS: Record<string, string> = {
  Agropecuario: '#2f6b52',
  Habitacional: '#e8b44f',
  Comercial: '#f4efe6',
  Religioso: '#c97b4a',
  Institucional: '#c97b4a',
  Educativo: '#c97b4a',
  Cultural: '#c97b4a',
  Recreacional: '#8fa39a',
  'Minería hidrocarburos': '#8fa39a',
  'Lote urbanizado no construido': '#8fa39a',
}
const DEFAULT_COLOR = '#8fa39a'

function terrainHeight(x: number, z: number): number {
  return (
    Math.sin(x * 0.22) * Math.cos(z * 0.3) * 2.6 +
    Math.sin(x * 0.55 + 1.7) * 1.2 +
    Math.cos(z * 0.7 + 0.6) * 1.0 +
    Math.sin((x + z) * 0.12) * 1.8
  )
}

function Terrain() {
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(TERRAIN_WIDTH, TERRAIN_DEPTH, SEGMENTS_X, SEGMENTS_Z)
    geo.rotateX(-Math.PI / 2)
    const position = geo.attributes.position
    const colors = new Float32Array(position.count * 3)
    const low = new THREE.Color('#0d1a15')
    const high = new THREE.Color('#1e4d3b')
    const crest = new THREE.Color('#3d6b56')
    const color = new THREE.Color()
    for (let i = 0; i < position.count; i++) {
      const x = position.getX(i)
      const z = position.getZ(i)
      const h = terrainHeight(x, z)
      position.setY(i, h)
      const t = (h + 6) / 12
      color.copy(low).lerp(high, Math.min(Math.max(t, 0), 1))
      if (t > 0.62) color.lerp(crest, (t - 0.62) * 2.4)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geo.computeVertexNormals()
    return geo
  }, [])

  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial vertexColors flatShading />
    </mesh>
  )
}

function ParcelPoints({ points }: { points: MapPoints }) {
  const { positions, colors } = useMemo(() => {
    const usable = points.features.filter(
      (f) => Number.isFinite(f.geometry.coordinates[0]) && Number.isFinite(f.geometry.coordinates[1]),
    )
    const lonMin = -74.6
    const lonMax = -74.1
    const latMin = 5.3
    const latMax = 5.9
    const count = usable.length
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const color = new THREE.Color()
    usable.forEach((feature, i) => {
      const [lon, lat] = feature.geometry.coordinates
      const nx = ((Math.min(Math.max(lon, lonMin), lonMax) - lonMin) / (lonMax - lonMin)) * 2 - 1
      const nz = ((Math.min(Math.max(lat, latMin), latMax) - latMin) / (latMax - latMin)) * 2 - 1
      const x = nx * (TERRAIN_WIDTH / 2 - 4)
      const z = nz * (TERRAIN_DEPTH / 2 - 4)
      const y = terrainHeight(x, z) + 1.4
      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z
      color.set(DESTINO_COLORS[feature.properties.destino_economico ?? ''] ?? DEFAULT_COLOR)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
    })
    return { positions, colors }
  }, [points])

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.34} vertexColors sizeAttenuation depthWrite={false} />
    </points>
  )
}

function CameraRig({ progressRef }: { progressRef: React.MutableRefObject<{ value: number }> }) {
  const { camera } = useThree()
  const target = useRef(new THREE.Vector3())

  useFrame((_, delta) => {
    const progress = progressRef.current.value
    const t = Math.min(Math.max(progress, 0), 1)
    target.current.set(
      t * 6,
      40 - t * 26,
      42 - t * 18,
    )
    camera.position.lerp(target.current, Math.min(delta * 2.4, 1))
    camera.lookAt(0, 1.2, 0)
  })

  return null
}

export default function Scene3D({ points, progressRef }: Scene3DProps) {
  return (
    <Canvas
      camera={{ position: [0, 40, 42], fov: 46, near: 0.5, far: 300 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      style={{ position: 'absolute', inset: 0 }}
      aria-hidden="true"
    >
      <fogExp2 attach="fog" args={['#0b1613', 0.011]} />
      <ambientLight intensity={0.55} color="#dfe8e2" />
      <directionalLight position={[30, 50, 20]} intensity={1.4} color="#f4efe6" />
      <directionalLight position={[-25, 18, -18]} intensity={0.4} color="#c97b4a" />
      <Terrain />
      <ParcelPoints points={points} />
      <CameraRig progressRef={progressRef} />
    </Canvas>
  )
}
