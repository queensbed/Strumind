'use client'

import React, { useRef, useState, useCallback, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Line } from '@react-three/drei'
import * as THREE from 'three'

interface AnalysisResult {
  nodeId: string
  displacement: {
    x: number
    y: number
    z: number
    magnitude: number
  }
  reaction: {
    fx: number
    fy: number
    fz: number
    mx: number
    my: number
    mz: number
  }
}

interface ElementResult {
  elementId: string
  forces: {
    axial: number
    shearY: number
    shearZ: number
    momentY: number
    momentZ: number
    torsion: number
  }
  stress: {
    max: number
    min: number
    vonMises: number
  }
}

interface ModeShape {
  modeNumber: number
  frequency: number
  displacements: {
    nodeId: string
    x: number
    y: number
    z: number
  }[]
}

interface Node {
  id: string
  x: number
  y: number
  z: number
}

interface Element {
  id: string
  nodeIds: [string, string]
  type: 'beam' | 'column' | 'brace'
}

interface ResultVisualizationProps {
  nodes: Node[]
  elements: Element[]
  analysisResults?: AnalysisResult[]
  elementResults?: ElementResult[]
  modeShapes?: ModeShape[]
  visualizationType: 'displacement' | 'stress' | 'forces' | 'modeShape'
  selectedMode?: number
  deformationScale?: number
  showOriginal?: boolean
  animate?: boolean
}

// Color mapping utilities
const getColorFromValue = (value: number, min: number, max: number): string => {
  const normalized = Math.max(0, Math.min(1, (value - min) / (max - min)))
  
  // Blue to red color scale
  if (normalized < 0.5) {
    const t = normalized * 2
    return `rgb(${Math.round(255 * t)}, ${Math.round(255 * t)}, 255)`
  } else {
    const t = (normalized - 0.5) * 2
    return `rgb(255, ${Math.round(255 * (1 - t))}, ${Math.round(255 * (1 - t))})`
  }
}

// Displacement visualization component
function DisplacementVisualization({ 
  nodes, 
  elements, 
  results, 
  scale, 
  showOriginal,
  animate 
}: {
  nodes: Node[]
  elements: Element[]
  results: AnalysisResult[]
  scale: number
  showOriginal: boolean
  animate: boolean
}) {
  const groupRef = useRef<THREE.Group>(null)
  const [animationTime, setAnimationTime] = useState(0)
  
  useFrame((state, delta) => {
    if (animate) {
      setAnimationTime(prev => prev + delta)
    }
  })
  
  const animationFactor = animate ? Math.sin(animationTime * 2) : 1
  
  const displacedNodes = useMemo(() => {
    return nodes.map(node => {
      const result = results.find(r => r.nodeId === node.id)
      if (!result) return node
      
      return {
        ...node,
        x: node.x + result.displacement.x * scale * animationFactor,
        y: node.y + result.displacement.y * scale * animationFactor,
        z: node.z + result.displacement.z * scale * animationFactor
      }
    })
  }, [nodes, results, scale, animationFactor])
  
  const maxDisplacement = useMemo(() => {
    return Math.max(...results.map(r => r.displacement.magnitude))
  }, [results])
  
  return (
    <group ref={groupRef}>
      {/* Original structure (if enabled) */}
      {showOriginal && (
        <group>
          {elements.map(element => {
            const startNode = nodes.find(n => n.id === element.nodeIds[0])
            const endNode = nodes.find(n => n.id === element.nodeIds[1])
            if (!startNode || !endNode) return null
            
            return (
              <Line
                key={`original-${element.id}`}
                points={[
                  new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                  new THREE.Vector3(endNode.x, endNode.y, endNode.z)
                ]}
                color="#cccccc"
                lineWidth={1}
                transparent
                opacity={0.3}
              />
            )
          })}
        </group>
      )}
      
      {/* Deformed structure */}
      <group>
        {/* Displaced nodes with color coding */}
        {displacedNodes.map(node => {
          const result = results.find(r => r.nodeId === node.id)
          const displacement = result?.displacement.magnitude || 0
          const color = getColorFromValue(displacement, 0, maxDisplacement)
          
          return (
            <group key={node.id} position={[node.x, node.y, node.z]}>
              <mesh>
                <sphereGeometry args={[0.05, 8, 8]} />
                <meshStandardMaterial color={color} />
              </mesh>
              <Text
                position={[0, 0.2, 0]}
                fontSize={0.05}
                color="black"
                anchorX="center"
                anchorY="middle"
              >
                {displacement.toFixed(3)}
              </Text>
            </group>
          )
        })}
        
        {/* Deformed elements */}
        {elements.map(element => {
          const startNode = displacedNodes.find(n => n.id === element.nodeIds[0])
          const endNode = displacedNodes.find(n => n.id === element.nodeIds[1])
          if (!startNode || !endNode) return null
          
          return (
            <Line
              key={element.id}
              points={[
                new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                new THREE.Vector3(endNode.x, endNode.y, endNode.z)
              ]}
              color="#2ecc71"
              lineWidth={2}
            />
          )
        })}
      </group>
    </group>
  )
}

// Stress visualization component
function StressVisualization({ 
  nodes, 
  elements, 
  elementResults 
}: {
  nodes: Node[]
  elements: Element[]
  elementResults: ElementResult[]
}) {
  const maxStress = useMemo(() => {
    return Math.max(...elementResults.map(r => r.stress.vonMises))
  }, [elementResults])
  
  const minStress = useMemo(() => {
    return Math.min(...elementResults.map(r => r.stress.vonMises))
  }, [elementResults])
  
  return (
    <group>
      {elements.map(element => {
        const startNode = nodes.find(n => n.id === element.nodeIds[0])
        const endNode = nodes.find(n => n.id === element.nodeIds[1])
        const result = elementResults.find(r => r.elementId === element.id)
        
        if (!startNode || !endNode || !result) return null
        
        const stress = result.stress.vonMises
        const color = getColorFromValue(stress, minStress, maxStress)
        const lineWidth = Math.max(1, Math.min(8, (stress / maxStress) * 6))
        
        const midPoint = new THREE.Vector3(
          (startNode.x + endNode.x) / 2,
          (startNode.y + endNode.y) / 2,
          (startNode.z + endNode.z) / 2
        )
        
        return (
          <group key={element.id}>
            <Line
              points={[
                new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                new THREE.Vector3(endNode.x, endNode.y, endNode.z)
              ]}
              color={color}
              lineWidth={lineWidth}
            />
            <Text
              position={[midPoint.x, midPoint.y + 0.2, midPoint.z]}
              fontSize={0.06}
              color="black"
              anchorX="center"
              anchorY="middle"
            >
              {stress.toFixed(1)} MPa
            </Text>
          </group>
        )
      })}
    </group>
  )
}

// Force diagram component
function ForceVisualization({ 
  nodes, 
  elements, 
  elementResults 
}: {
  nodes: Node[]
  elements: Element[]
  elementResults: ElementResult[]
}) {
  const maxForce = useMemo(() => {
    return Math.max(...elementResults.map(r => Math.abs(r.forces.axial)))
  }, [elementResults])
  
  return (
    <group>
      {elements.map(element => {
        const startNode = nodes.find(n => n.id === element.nodeIds[0])
        const endNode = nodes.find(n => n.id === element.nodeIds[1])
        const result = elementResults.find(r => r.elementId === element.id)
        
        if (!startNode || !endNode || !result) return null
        
        const axialForce = result.forces.axial
        const isCompression = axialForce < 0
        const color = isCompression ? '#e74c3c' : '#2ecc71'
        const lineWidth = Math.max(1, Math.min(8, (Math.abs(axialForce) / maxForce) * 6))
        
        const midPoint = new THREE.Vector3(
          (startNode.x + endNode.x) / 2,
          (startNode.y + endNode.y) / 2,
          (startNode.z + endNode.z) / 2
        )
        
        return (
          <group key={element.id}>
            <Line
              points={[
                new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                new THREE.Vector3(endNode.x, endNode.y, endNode.z)
              ]}
              color={color}
              lineWidth={lineWidth}
            />
            <Text
              position={[midPoint.x, midPoint.y + 0.2, midPoint.z]}
              fontSize={0.06}
              color="black"
              anchorX="center"
              anchorY="middle"
            >
              {axialForce.toFixed(1)} kN
            </Text>
            <Text
              position={[midPoint.x, midPoint.y - 0.2, midPoint.z]}
              fontSize={0.04}
              color={color}
              anchorX="center"
              anchorY="middle"
            >
              {isCompression ? 'C' : 'T'}
            </Text>
          </group>
        )
      })}
    </group>
  )
}

// Mode shape visualization component
function ModeShapeVisualization({ 
  nodes, 
  elements, 
  modeShape, 
  scale,
  animate 
}: {
  nodes: Node[]
  elements: Element[]
  modeShape: ModeShape
  scale: number
  animate: boolean
}) {
  const groupRef = useRef<THREE.Group>(null)
  const [animationTime, setAnimationTime] = useState(0)
  
  useFrame((state, delta) => {
    if (animate) {
      setAnimationTime(prev => prev + delta)
    }
  })
  
  const animationFactor = animate ? Math.sin(animationTime * modeShape.frequency * 0.1) : 1
  
  const displacedNodes = useMemo(() => {
    return nodes.map(node => {
      const displacement = modeShape.displacements.find(d => d.nodeId === node.id)
      if (!displacement) return node
      
      return {
        ...node,
        x: node.x + displacement.x * scale * animationFactor,
        y: node.y + displacement.y * scale * animationFactor,
        z: node.z + displacement.z * scale * animationFactor
      }
    })
  }, [nodes, modeShape, scale, animationFactor])
  
  return (
    <group ref={groupRef}>
      {/* Original structure */}
      <group>
        {elements.map(element => {
          const startNode = nodes.find(n => n.id === element.nodeIds[0])
          const endNode = nodes.find(n => n.id === element.nodeIds[1])
          if (!startNode || !endNode) return null
          
          return (
            <Line
              key={`original-${element.id}`}
              points={[
                new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                new THREE.Vector3(endNode.x, endNode.y, endNode.z)
              ]}
              color="#cccccc"
              lineWidth={1}
              transparent
              opacity={0.3}
            />
          )
        })}
      </group>
      
      {/* Mode shape */}
      <group>
        {elements.map(element => {
          const startNode = displacedNodes.find(n => n.id === element.nodeIds[0])
          const endNode = displacedNodes.find(n => n.id === element.nodeIds[1])
          if (!startNode || !endNode) return null
          
          return (
            <Line
              key={element.id}
              points={[
                new THREE.Vector3(startNode.x, startNode.y, startNode.z),
                new THREE.Vector3(endNode.x, endNode.y, endNode.z)
              ]}
              color="#9b59b6"
              lineWidth={3}
            />
          )
        })}
      </group>
      
      {/* Mode info */}
      <Text
        position={[0, 15, 0]}
        fontSize={0.5}
        color="#9b59b6"
        anchorX="center"
        anchorY="middle"
      >
        Mode {modeShape.modeNumber}: {modeShape.frequency.toFixed(3)} Hz
      </Text>
    </group>
  )
}

// Color legend component
function ColorLegend({ 
  min, 
  max, 
  unit, 
  position 
}: {
  min: number
  max: number
  unit: string
  position: [number, number, number]
}) {
  const steps = 10
  const stepSize = (max - min) / steps
  
  return (
    <group position={position}>
      {Array.from({ length: steps + 1 }, (_, i) => {
        const value = min + i * stepSize
        const color = getColorFromValue(value, min, max)
        const y = i * 0.2
        
        return (
          <group key={i} position={[0, y, 0]}>
            <mesh position={[-0.2, 0, 0]}>
              <boxGeometry args={[0.1, 0.15, 0.02]} />
              <meshStandardMaterial color={color} />
            </mesh>
            <Text
              position={[0.2, 0, 0]}
              fontSize={0.08}
              color="black"
              anchorX="left"
              anchorY="middle"
            >
              {value.toFixed(2)} {unit}
            </Text>
          </group>
        )
      })}
    </group>
  )
}

// Main component
export default function ResultVisualization({
  nodes,
  elements,
  analysisResults = [],
  elementResults = [],
  modeShapes = [],
  visualizationType,
  selectedMode = 0,
  deformationScale = 100,
  showOriginal = true,
  animate = false
}: ResultVisualizationProps) {
  const [currentScale, setCurrentScale] = useState(deformationScale)
  const [isAnimating, setIsAnimating] = useState(animate)
  
  const renderVisualization = () => {
    switch (visualizationType) {
      case 'displacement':
        return (
          <DisplacementVisualization
            nodes={nodes}
            elements={elements}
            results={analysisResults}
            scale={currentScale}
            showOriginal={showOriginal}
            animate={isAnimating}
          />
        )
      case 'stress':
        return (
          <StressVisualization
            nodes={nodes}
            elements={elements}
            elementResults={elementResults}
          />
        )
      case 'forces':
        return (
          <ForceVisualization
            nodes={nodes}
            elements={elements}
            elementResults={elementResults}
          />
        )
      case 'modeShape':
        const modeShape = modeShapes[selectedMode]
        if (!modeShape) return null
        return (
          <ModeShapeVisualization
            nodes={nodes}
            elements={elements}
            modeShape={modeShape}
            scale={currentScale}
            animate={isAnimating}
          />
        )
      default:
        return null
    }
  }
  
  const getLegendProps = () => {
    switch (visualizationType) {
      case 'displacement':
        const maxDisp = Math.max(...analysisResults.map(r => r.displacement.magnitude))
        return { min: 0, max: maxDisp, unit: 'mm' }
      case 'stress':
        const maxStress = Math.max(...elementResults.map(r => r.stress.vonMises))
        const minStress = Math.min(...elementResults.map(r => r.stress.vonMises))
        return { min: minStress, max: maxStress, unit: 'MPa' }
      case 'forces':
        const maxForce = Math.max(...elementResults.map(r => Math.abs(r.forces.axial)))
        return { min: -maxForce, max: maxForce, unit: 'kN' }
      default:
        return null
    }
  }
  
  const legendProps = getLegendProps()
  
  return (
    <div className="w-full h-full relative">
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-lg">
        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-sm font-medium mb-1">
              Deformation Scale: {currentScale}x
            </label>
            <input
              type="range"
              min="1"
              max="1000"
              value={currentScale}
              onChange={(e) => setCurrentScale(Number(e.target.value))}
              className="w-full"
            />
          </div>
          
          {visualizationType === 'modeShape' && modeShapes.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-1">
                Mode Shape: {selectedMode + 1}
              </label>
              <select
                value={selectedMode}
                onChange={(e) => {}}
                className="w-full p-1 border rounded"
              >
                {modeShapes.map((mode, index) => (
                  <option key={index} value={index}>
                    Mode {mode.modeNumber}: {mode.frequency.toFixed(3)} Hz
                  </option>
                ))}
              </select>
            </div>
          )}
          
          <div className="flex gap-2">
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={showOriginal}
                onChange={(e) => {}}
              />
              Show Original
            </label>
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={isAnimating}
                onChange={(e) => setIsAnimating(e.target.checked)}
              />
              Animate
            </label>
          </div>
        </div>
      </div>
      
      {/* Visualization type selector */}
      <div className="absolute top-4 right-4 z-10 bg-white p-4 rounded-lg shadow-lg">
        <div className="flex flex-col gap-2">
          <h3 className="font-bold">Visualization</h3>
          <div className="flex flex-col gap-1">
            {['displacement', 'stress', 'forces', 'modeShape'].map(type => (
              <label key={type} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="visualizationType"
                  value={type}
                  checked={visualizationType === type}
                  onChange={() => {}}
                />
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </label>
            ))}
          </div>
        </div>
      </div>
      
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [15, 15, 15], fov: 60 }}
        className="w-full h-full"
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[10, 10, 5]} intensity={0.8} />
        
        {renderVisualization()}
        
        {/* Color legend */}
        {legendProps && (
          <ColorLegend
            min={legendProps.min}
            max={legendProps.max}
            unit={legendProps.unit}
            position={[12, 0, 0]}
          />
        )}
        
        <OrbitControls enablePan enableZoom enableRotate />
      </Canvas>
    </div>
  )
}