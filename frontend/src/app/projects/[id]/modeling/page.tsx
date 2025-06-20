'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'next/navigation'
import ModelBuilder3D from '@/components/ModelBuilder3D'
import ResultVisualization from '@/components/ResultVisualization'

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

export default function ModelingPage() {
  const params = useParams()
  const projectId = params.id as string
  
  // Model state
  const [nodes, setNodes] = useState<Node[]>([])
  const [elements, setElements] = useState<Element[]>([])
  const [loads, setLoads] = useState<Load[]>([])
  
  // Analysis results
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([])
  const [elementResults, setElementResults] = useState<ElementResult[]>([])
  
  // UI state
  const [activeTab, setActiveTab] = useState<'modeling' | 'analysis' | 'results' | 'collaboration'>('modeling')
  const [isAnalysisRunning, setIsAnalysisRunning] = useState(false)
  const [visualizationType, setVisualizationType] = useState<'displacement' | 'stress' | 'forces' | 'modeShape'>('displacement')
  
  // Collaboration state
  const [projectMembers, setProjectMembers] = useState([])
  const [onlineUsers, setOnlineUsers] = useState([])
  const [activityLog, setActivityLog] = useState([])
  
  // Initialize with sample 10-story building data
  useEffect(() => {
    initializeSampleBuilding()
  }, [])
  
  const initializeSampleBuilding = useCallback(() => {
    // Create nodes for 10-story building (4 columns per floor)
    const sampleNodes: Node[] = []
    const sampleElements: Element[] = []
    const sampleLoads: Load[] = []
    
    const gridSpacing = 6 // 6m grid
    const storyHeight = 3 // 3m per story
    
    // Create nodes
    let nodeId = 1
    for (let story = 0; story <= 10; story++) {
      for (let x = 0; x <= 3; x++) {
        for (let y = 0; y <= 3; y++) {
          sampleNodes.push({
            id: `N${nodeId}`,
            x: x * gridSpacing,
            y: y * gridSpacing,
            z: story * storyHeight
          })
          nodeId++
        }
      }
    }
    
    // Create columns (vertical elements)
    let elementId = 1
    for (let story = 0; story < 10; story++) {
      for (let x = 0; x <= 3; x++) {
        for (let y = 0; y <= 3; y++) {
          const bottomNodeIndex = story * 16 + x * 4 + y
          const topNodeIndex = (story + 1) * 16 + x * 4 + y
          
          sampleElements.push({
            id: `C${elementId}`,
            nodeIds: [sampleNodes[bottomNodeIndex].id, sampleNodes[topNodeIndex].id],
            type: 'column'
          })
          elementId++
        }
      }
    }
    
    // Create beams (horizontal elements)
    for (let story = 1; story <= 10; story++) {
      for (let x = 0; x <= 3; x++) {
        for (let y = 0; y < 3; y++) {
          const node1Index = story * 16 + x * 4 + y
          const node2Index = story * 16 + x * 4 + (y + 1)
          
          sampleElements.push({
            id: `B${elementId}`,
            nodeIds: [sampleNodes[node1Index].id, sampleNodes[node2Index].id],
            type: 'beam'
          })
          elementId++
        }
      }
      
      for (let x = 0; x < 3; x++) {
        for (let y = 0; y <= 3; y++) {
          const node1Index = story * 16 + x * 4 + y
          const node2Index = story * 16 + (x + 1) * 4 + y
          
          sampleElements.push({
            id: `B${elementId}`,
            nodeIds: [sampleNodes[node1Index].id, sampleNodes[node2Index].id],
            type: 'beam'
          })
          elementId++
        }
      }
    }
    
    // Create sample loads (dead load on beams)
    let loadId = 1
    sampleElements.forEach(element => {
      if (element.type === 'beam') {
        sampleLoads.push({
          id: `L${loadId}`,
          elementId: element.id,
          type: 'distributed',
          fx: 0,
          fy: 0,
          fz: -25, // 25 kN/m downward
        })
        loadId++
      }
    })
    
    setNodes(sampleNodes)
    setElements(sampleElements)
    setLoads(sampleLoads)
    
    // Generate sample analysis results
    generateSampleResults(sampleNodes, sampleElements)
  }, [])
  
  const generateSampleResults = (nodes: Node[], elements: Element[]) => {
    // Generate sample displacement results
    const sampleAnalysisResults: AnalysisResult[] = nodes.map(node => {
      // Simulate larger displacements at higher levels
      const heightFactor = node.z / 30 // Max height is 30m
      const lateralDisp = heightFactor * 10 * (Math.random() - 0.5) // ±5mm at top
      const verticalDisp = -heightFactor * 5 * Math.random() // Up to 2.5mm downward
      
      return {
        nodeId: node.id,
        displacement: {
          x: lateralDisp,
          y: lateralDisp * 0.8,
          z: verticalDisp,
          magnitude: Math.sqrt(lateralDisp**2 + (lateralDisp * 0.8)**2 + verticalDisp**2)
        },
        reaction: {
          fx: node.z === 0 ? (Math.random() - 0.5) * 100 : 0, // Reactions only at base
          fy: node.z === 0 ? (Math.random() - 0.5) * 100 : 0,
          fz: node.z === 0 ? -Math.random() * 500 : 0, // Compression at base
          mx: 0,
          my: 0,
          mz: 0
        }
      }
    })
    
    // Generate sample element results
    const sampleElementResults: ElementResult[] = elements.map(element => {
      const isColumn = element.type === 'column'
      const isBeam = element.type === 'beam'
      
      return {
        elementId: element.id,
        forces: {
          axial: isColumn ? -Math.random() * 1000 : Math.random() * 200, // Compression in columns
          shearY: (Math.random() - 0.5) * 100,
          shearZ: (Math.random() - 0.5) * 100,
          momentY: (Math.random() - 0.5) * 500,
          momentZ: (Math.random() - 0.5) * 500,
          torsion: (Math.random() - 0.5) * 50
        },
        stress: {
          max: Math.random() * 20, // MPa
          min: -Math.random() * 15,
          vonMises: Math.random() * 18
        }
      }
    })
    
    setAnalysisResults(sampleAnalysisResults)
    setElementResults(sampleElementResults)
  }
  
  const runAnalysis = async () => {
    setIsAnalysisRunning(true)
    
    try {
      // Simulate analysis API call
      await new Promise(resolve => setTimeout(resolve, 3000))
      
      // Regenerate results with some variation
      generateSampleResults(nodes, elements)
      
      // Add to activity log
      const newActivity = {
        id: Date.now().toString(),
        action: 'ANALYSIS_COMPLETED',
        user: 'Current User',
        timestamp: new Date().toISOString(),
        details: 'Linear static analysis completed successfully'
      }
      setActivityLog(prev => [newActivity, ...prev])
      
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalysisRunning(false)
    }
  }
  
  const exportDrawings = async () => {
    try {
      // Simulate drawing export
      const response = await fetch(`/api/v1/files/${projectId}/export/drawings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drawing_types: ['plan', 'elevation', 'section', 'reinforcement'],
          format: 'pdf'
        })
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectId}_drawings.pdf`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Export failed:', error)
    }
  }
  
  const exportIFC = async () => {
    try {
      const response = await fetch(`/api/v1/files/${projectId}/export/ifc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          format: 'ifc4',
          target_software: 'revit'
        })
      })
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${projectId}_model.ifc`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('IFC export failed:', error)
    }
  }
  
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">10-Story Building Model</h1>
            <p className="text-sm text-gray-600">Project ID: {projectId}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={runAnalysis}
              disabled={isAnalysisRunning}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isAnalysisRunning ? 'Running Analysis...' : 'Run Analysis'}
            </button>
            
            <button
              onClick={exportDrawings}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Export Drawings
            </button>
            
            <button
              onClick={exportIFC}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              Export IFC
            </button>
          </div>
        </div>
      </div>
      
      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="px-6">
          <nav className="flex space-x-8">
            {[
              { id: 'modeling', label: '3D Modeling', icon: '🏗️' },
              { id: 'analysis', label: 'Analysis', icon: '⚡' },
              { id: 'results', label: 'Results', icon: '📊' },
              { id: 'collaboration', label: 'Collaboration', icon: '👥' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex">
        {/* 3D Viewport */}
        <div className="flex-1">
          {activeTab === 'modeling' && (
            <ModelBuilder3D
              nodes={nodes}
              elements={elements}
              loads={loads}
              onNodesChange={setNodes}
              onElementsChange={setElements}
              onLoadsChange={setLoads}
              gridSize={1}
              snapToGrid={true}
              showGrid={true}
              showLoads={true}
            />
          )}
          
          {(activeTab === 'analysis' || activeTab === 'results') && (
            <ResultVisualization
              nodes={nodes}
              elements={elements}
              analysisResults={analysisResults}
              elementResults={elementResults}
              visualizationType={visualizationType}
              deformationScale={100}
              showOriginal={true}
              animate={false}
            />
          )}
          
          {activeTab === 'collaboration' && (
            <div className="h-full flex items-center justify-center bg-gray-100">
              <div className="text-center">
                <div className="text-6xl mb-4">👥</div>
                <h3 className="text-xl font-semibold mb-2">Team Collaboration</h3>
                <p className="text-gray-600 mb-4">Real-time collaboration features</p>
                <div className="space-y-2">
                  <div className="bg-white p-3 rounded-lg shadow">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      <span>John Doe (Engineer) - Currently editing</span>
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      <span>Jane Smith (Designer) - Viewing results</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Side Panel */}
        <div className="w-80 bg-white border-l overflow-y-auto">
          {activeTab === 'modeling' && (
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Model Properties</h3>
              
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Model Statistics</h4>
                  <div className="text-sm space-y-1">
                    <div>Nodes: {nodes.length}</div>
                    <div>Elements: {elements.length}</div>
                    <div>Loads: {loads.length}</div>
                    <div>Stories: 10</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Building Info</h4>
                  <div className="text-sm space-y-1">
                    <div>Height: 30m</div>
                    <div>Grid: 6m × 6m</div>
                    <div>Story Height: 3m</div>
                    <div>Structure: RC Frame</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Materials</h4>
                  <div className="text-sm space-y-1">
                    <div>Concrete: C30/37</div>
                    <div>Steel: Grade 500</div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'analysis' && (
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Analysis Settings</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Analysis Type</label>
                  <select className="w-full p-2 border rounded-lg">
                    <option>Linear Static</option>
                    <option>Modal Analysis</option>
                    <option>Response Spectrum</option>
                    <option>Time History</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Load Cases</label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input type="checkbox" checked className="mr-2" />
                      Dead Load (DL)
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" checked className="mr-2" />
                      Live Load (LL)
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="mr-2" />
                      Wind Load (WL)
                    </label>
                    <label className="flex items-center">
                      <input type="checkbox" className="mr-2" />
                      Seismic Load (EQ)
                    </label>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Solver Settings</label>
                  <div className="space-y-2">
                    <div>
                      <label className="block text-xs text-gray-600">Tolerance</label>
                      <input type="text" defaultValue="1e-6" className="w-full p-1 border rounded text-sm" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600">Max Iterations</label>
                      <input type="text" defaultValue="1000" className="w-full p-1 border rounded text-sm" />
                    </div>
                  </div>
                </div>
                
                {isAnalysisRunning && (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                      <span className="text-sm">Running analysis...</span>
                    </div>
                    <div className="mt-2 bg-blue-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full w-1/3 animate-pulse"></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {activeTab === 'results' && (
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Result Visualization</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Visualization Type</label>
                  <select 
                    value={visualizationType}
                    onChange={(e) => setVisualizationType(e.target.value as any)}
                    className="w-full p-2 border rounded-lg"
                  >
                    <option value="displacement">Displacements</option>
                    <option value="stress">Stress Contours</option>
                    <option value="forces">Force Diagrams</option>
                    <option value="modeShape">Mode Shapes</option>
                  </select>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Max Values</h4>
                  <div className="text-sm space-y-1">
                    <div>Max Displacement: {Math.max(...analysisResults.map(r => r.displacement.magnitude)).toFixed(2)} mm</div>
                    <div>Max Stress: {Math.max(...elementResults.map(r => r.stress.vonMises)).toFixed(1)} MPa</div>
                    <div>Max Axial Force: {Math.max(...elementResults.map(r => Math.abs(r.forces.axial))).toFixed(0)} kN</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Design Checks</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Deflection</span>
                      <span className="text-sm text-green-600">✓ Pass</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Stress</span>
                      <span className="text-sm text-green-600">✓ Pass</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Stability</span>
                      <span className="text-sm text-yellow-600">⚠ Check</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'collaboration' && (
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Team & Activity</h3>
              
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Online Now</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs">JD</div>
                      <div>
                        <div className="text-sm font-medium">John Doe</div>
                        <div className="text-xs text-gray-600">Engineer</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">JS</div>
                      <div>
                        <div className="text-sm font-medium">Jane Smith</div>
                        <div className="text-xs text-gray-600">Designer</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Recent Activity</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Analysis completed</span>
                      <span className="text-gray-500">2m ago</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Model updated</span>
                      <span className="text-gray-500">15m ago</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Jane joined project</span>
                      <span className="text-gray-500">1h ago</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Version History</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>v2.1 - Current</span>
                      <span className="text-gray-500">Today</span>
                    </div>
                    <div className="flex justify-between">
                      <span>v2.0 - Analysis update</span>
                      <span className="text-gray-500">Yesterday</span>
                    </div>
                    <div className="flex justify-between">
                      <span>v1.9 - Initial model</span>
                      <span className="text-gray-500">2 days ago</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}