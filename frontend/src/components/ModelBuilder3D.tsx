'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Grid, TransformControls, Text, Line } from '@react-three/drei'
import * as THREE from 'three'

interface Node {
  id: string
  x: number
  y: number
  z: number
  selected?: boolean
}

interface Element {
  id: string
  nodeIds: [string, string]
  type: 'beam' | 'column' | 'brace'
  sectionId?: string
  materialId?: string
  selected?: boolean
}

interface Load {
  id: string
  nodeId?: string
  elementId?: string
  type: 'point' | 'distributed' | 'moment'
  fx: number
  fy: number
  fz: number
  mx?: number
  my?: number
  mz?: number
}

interface ModelBuilder3DProps {
  nodes: Node[]
  elements: Element[]
  loads: Load[]
  onNodesChange: (nodes: Node[]) => void
  onElementsChange: (elements: Element[]) => void
  onLoadsChange: (loads: Load[]) => void
  gridSize?: number
  snapToGrid?: boolean
  showGrid?: boolean
  showLoads?: boolean
}

// Node component
function NodeComponent({ node, onSelect, onMove, selected }: {
  node: Node
  onSelect: (id: string) => void
  onMove: (id: string, position: [number, number, number]) => void
  selected: boolean
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  return (
    <group position={[node.x, node.y, node.z]}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation()
          onSelect(node.id)
        }}
      >
        <sphereGeometry args={[0.1, 16, 16]} />
        <meshStandardMaterial 
          color={selected ? '#ff6b6b' : '#4ecdc4'} 
          transparent
          opacity={0.8}
        />
      </mesh>
      <Text
        position={[0, 0.3, 0]}
        fontSize={0.1}
        color="black"
        anchorX="center"
        anchorY="middle"
      >
        {node.id}
      </Text>
    </group>
  )
}

// Element component
function ElementComponent({ element, nodes, onSelect, selected }: {
  element: Element
  nodes: Node[]
  onSelect: (id: string) => void
  selected: boolean
}) {
  const startNode = nodes.find(n => n.id === element.nodeIds[0])
  const endNode = nodes.find(n => n.id === element.nodeIds[1])
  
  if (!startNode || !endNode) return null
  
  const points = [
    new THREE.Vector3(startNode.x, startNode.y, startNode.z),
    new THREE.Vector3(endNode.x, endNode.y, endNode.z)
  ]
  
  const getElementColor = (type: string) => {
    switch (type) {
      case 'beam': return '#2ecc71'
      case 'column': return '#e74c3c'
      case 'brace': return '#f39c12'
      default: return '#95a5a6'
    }
  }
  
  return (
    <Line
      points={points}
      color={selected ? '#ff6b6b' : getElementColor(element.type)}
      lineWidth={selected ? 4 : 2}
      onClick={(e) => {
        e.stopPropagation()
        onSelect(element.id)
      }}
    />
  )
}

// Load component
function LoadComponent({ load, nodes, elements }: {
  load: Load
  nodes: Node[]
  elements: Element[]
}) {
  let position: [number, number, number] = [0, 0, 0]
  
  if (load.nodeId) {
    const node = nodes.find(n => n.id === load.nodeId)
    if (node) position = [node.x, node.y, node.z]
  } else if (load.elementId) {
    const element = elements.find(e => e.id === load.elementId)
    if (element) {
      const startNode = nodes.find(n => n.id === element.nodeIds[0])
      const endNode = nodes.find(n => n.id === element.nodeIds[1])
      if (startNode && endNode) {
        position = [
          (startNode.x + endNode.x) / 2,
          (startNode.y + endNode.y) / 2,
          (startNode.z + endNode.z) / 2
        ]
      }
    }
  }
  
  const magnitude = Math.sqrt(load.fx ** 2 + load.fy ** 2 + load.fz ** 2)
  const scale = Math.max(0.5, magnitude / 1000) // Scale based on magnitude
  
  return (
    <group position={position}>
      {/* Force vector */}
      <Line
        points={[
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(load.fx * scale, load.fy * scale, load.fz * scale)
        ]}
        color="#e74c3c"
        lineWidth={3}
      />
      {/* Arrow head */}
      <mesh position={[load.fx * scale, load.fy * scale, load.fz * scale]}>
        <coneGeometry args={[0.05, 0.2, 8]} />
        <meshStandardMaterial color="#e74c3c" />
      </mesh>
      {/* Load label */}
      <Text
        position={[load.fx * scale + 0.2, load.fy * scale + 0.2, load.fz * scale]}
        fontSize={0.08}
        color="#e74c3c"
        anchorX="center"
        anchorY="middle"
      >
        {`${magnitude.toFixed(1)}N`}
      </Text>
    </group>
  )
}

// Grid levels component
function GridLevels({ levels }: { levels: number[] }) {
  return (
    <>
      {levels.map((level, index) => (
        <group key={index} position={[0, level, 0]}>
          <Grid
            args={[20, 20]}
            cellSize={1}
            cellThickness={0.5}
            cellColor="#6f6f6f"
            sectionSize={5}
            sectionThickness={1}
            sectionColor="#9d4b4b"
            fadeDistance={30}
            fadeStrength={1}
            followCamera={false}
            infiniteGrid={true}
          />
          <Text
            position={[10, 0, 0]}
            fontSize={0.3}
            color="#333"
            anchorX="left"
            anchorY="middle"
          >
            Level {index + 1} (Y={level}m)
          </Text>
        </group>
      ))}
    </>
  )
}

// Main scene component
function Scene({ 
  nodes, 
  elements, 
  loads, 
  onNodesChange, 
  onElementsChange,
  selectedNodeId,
  selectedElementId,
  setSelectedNodeId,
  setSelectedElementId,
  snapToGrid,
  gridSize,
  showLoads,
  gridLevels
}: {
  nodes: Node[]
  elements: Element[]
  loads: Load[]
  onNodesChange: (nodes: Node[]) => void
  onElementsChange: (elements: Element[]) => void
  selectedNodeId: string | null
  selectedElementId: string | null
  setSelectedNodeId: (id: string | null) => void
  setSelectedElementId: (id: string | null) => void
  snapToGrid: boolean
  gridSize: number
  showLoads: boolean
  gridLevels: number[]
}) {
  const { camera } = useThree()
  
  const handleNodeSelect = useCallback((id: string) => {
    setSelectedNodeId(selectedNodeId === id ? null : id)
    setSelectedElementId(null)
  }, [selectedNodeId, setSelectedNodeId, setSelectedElementId])
  
  const handleElementSelect = useCallback((id: string) => {
    setSelectedElementId(selectedElementId === id ? null : id)
    setSelectedNodeId(null)
  }, [selectedElementId, setSelectedElementId, setSelectedNodeId])
  
  const handleNodeMove = useCallback((id: string, position: [number, number, number]) => {
    const newNodes = nodes.map(node => 
      node.id === id 
        ? { 
            ...node, 
            x: snapToGrid ? Math.round(position[0] / gridSize) * gridSize : position[0],
            y: snapToGrid ? Math.round(position[1] / gridSize) * gridSize : position[1],
            z: snapToGrid ? Math.round(position[2] / gridSize) * gridSize : position[2]
          }
        : node
    )
    onNodesChange(newNodes)
  }, [nodes, onNodesChange, snapToGrid, gridSize])
  
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 10, 5]} intensity={0.8} />
      
      {/* Grid levels */}
      <GridLevels levels={gridLevels} />
      
      {/* Nodes */}
      {nodes.map(node => (
        <NodeComponent
          key={node.id}
          node={node}
          onSelect={handleNodeSelect}
          onMove={handleNodeMove}
          selected={selectedNodeId === node.id}
        />
      ))}
      
      {/* Elements */}
      {elements.map(element => (
        <ElementComponent
          key={element.id}
          element={element}
          nodes={nodes}
          onSelect={handleElementSelect}
          selected={selectedElementId === element.id}
        />
      ))}
      
      {/* Loads */}
      {showLoads && loads.map(load => (
        <LoadComponent
          key={load.id}
          load={load}
          nodes={nodes}
          elements={elements}
        />
      ))}
      
      {/* Transform controls for selected node */}
      {selectedNodeId && (
        <TransformControls
          object={nodes.find(n => n.id === selectedNodeId)}
          mode="translate"
          onObjectChange={(e) => {
            if (e && e.target && e.target.object) {
              const position = e.target.object.position
              handleNodeMove(selectedNodeId, [position.x, position.y, position.z])
            }
          }}
        />
      )}
      
      <OrbitControls enablePan enableZoom enableRotate />
    </>
  )
}

// Main component
export default function ModelBuilder3D({
  nodes,
  elements,
  loads,
  onNodesChange,
  onElementsChange,
  onLoadsChange,
  gridSize = 1,
  snapToGrid = true,
  showGrid = true,
  showLoads = true
}: ModelBuilder3DProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null)
  const [mode, setMode] = useState<'select' | 'addNode' | 'addElement' | 'addLoad'>('select')
  const [gridLevels, setGridLevels] = useState<number[]>([0, 3, 6, 9, 12, 15, 18, 21, 24, 27]) // 10 stories
  const [pendingElementStart, setPendingElementStart] = useState<string | null>(null)
  
  const handleCanvasClick = useCallback((event: any) => {
    if (mode === 'addNode') {
      const point = event.point
      const newNode: Node = {
        id: `N${nodes.length + 1}`,
        x: snapToGrid ? Math.round(point.x / gridSize) * gridSize : point.x,
        y: snapToGrid ? Math.round(point.y / gridSize) * gridSize : point.y,
        z: snapToGrid ? Math.round(point.z / gridSize) * gridSize : point.z
      }
      onNodesChange([...nodes, newNode])
    }
  }, [mode, nodes, onNodesChange, snapToGrid, gridSize])
  
  const handleNodeClick = useCallback((nodeId: string) => {
    if (mode === 'addElement') {
      if (!pendingElementStart) {
        setPendingElementStart(nodeId)
      } else if (pendingElementStart !== nodeId) {
        const newElement: Element = {
          id: `E${elements.length + 1}`,
          nodeIds: [pendingElementStart, nodeId],
          type: 'beam'
        }
        onElementsChange([...elements, newElement])
        setPendingElementStart(null)
      }
    }
  }, [mode, pendingElementStart, elements, onElementsChange])
  
  const addGridLevel = useCallback(() => {
    const maxLevel = Math.max(...gridLevels)
    setGridLevels([...gridLevels, maxLevel + 3])
  }, [gridLevels])
  
  const removeGridLevel = useCallback(() => {
    if (gridLevels.length > 1) {
      setGridLevels(gridLevels.slice(0, -1))
    }
  }, [gridLevels])
  
  return (
    <div className="w-full h-full relative">
      {/* Toolbar */}
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-lg">
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <button
              className={`px-3 py-1 rounded ${mode === 'select' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              onClick={() => setMode('select')}
            >
              Select
            </button>
            <button
              className={`px-3 py-1 rounded ${mode === 'addNode' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              onClick={() => setMode('addNode')}
            >
              Add Node
            </button>
            <button
              className={`px-3 py-1 rounded ${mode === 'addElement' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              onClick={() => setMode('addElement')}
            >
              Add Element
            </button>
            <button
              className={`px-3 py-1 rounded ${mode === 'addLoad' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
              onClick={() => setMode('addLoad')}
            >
              Add Load
            </button>
          </div>
          
          <div className="flex gap-2 items-center">
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={snapToGrid}
                onChange={(e) => {}}
              />
              Snap to Grid
            </label>
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={showLoads}
                onChange={(e) => {}}
              />
              Show Loads
            </label>
          </div>
          
          <div className="flex gap-2">
            <button
              className="px-2 py-1 bg-green-500 text-white rounded text-sm"
              onClick={addGridLevel}
            >
              + Level
            </button>
            <button
              className="px-2 py-1 bg-red-500 text-white rounded text-sm"
              onClick={removeGridLevel}
            >
              - Level
            </button>
            <span className="text-sm">Levels: {gridLevels.length}</span>
          </div>
        </div>
      </div>
      
      {/* Properties panel */}
      {(selectedNodeId || selectedElementId) && (
        <div className="absolute top-4 right-4 z-10 bg-white p-4 rounded-lg shadow-lg w-64">
          <h3 className="font-bold mb-2">Properties</h3>
          {selectedNodeId && (
            <div>
              <h4 className="font-semibold">Node {selectedNodeId}</h4>
              {/* Node properties form would go here */}
            </div>
          )}
          {selectedElementId && (
            <div>
              <h4 className="font-semibold">Element {selectedElementId}</h4>
              {/* Element properties form would go here */}
            </div>
          )}
        </div>
      )}
      
      {/* Status bar */}
      <div className="absolute bottom-4 left-4 z-10 bg-white p-2 rounded shadow">
        <div className="text-sm">
          Mode: {mode} | Nodes: {nodes.length} | Elements: {elements.length} | Loads: {loads.length}
          {pendingElementStart && ` | Connecting from ${pendingElementStart}`}
        </div>
      </div>
      
      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [10, 10, 10], fov: 60 }}
        onClick={handleCanvasClick}
        className="w-full h-full"
      >
        <Scene
          nodes={nodes}
          elements={elements}
          loads={loads}
          onNodesChange={onNodesChange}
          onElementsChange={onElementsChange}
          selectedNodeId={selectedNodeId}
          selectedElementId={selectedElementId}
          setSelectedNodeId={setSelectedNodeId}
          setSelectedElementId={setSelectedElementId}
          snapToGrid={snapToGrid}
          gridSize={gridSize}
          showLoads={showLoads}
          gridLevels={gridLevels}
        />
      </Canvas>
    </div>
  )
}