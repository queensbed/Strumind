"""
Drawing generation engine for structural drawings, plans, elevations, and sections.
"""

import ezdxf
from ezdxf import units
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, A2, A1
from reportlab.lib.units import mm
from reportlab.lib.colors import black, blue, red, green
from reportlab.graphics.shapes import Drawing, Line, Circle, Rect, String
from reportlab.graphics.renderPDF import drawToFile
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import os
from datetime import datetime

class DrawingGenerator:
    """Main drawing generation class"""
    
    def __init__(self):
        self.drawing_scale = 1.0
        self.page_size = A1
        self.units = 'mm'
        
    def create_structural_plan(self, 
                             nodes: List[Dict], 
                             elements: List[Dict], 
                             level: float = 0.0,
                             output_path: str = None) -> str:
        """Generate structural plan drawing"""
        
        # Create DXF document
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        # Filter nodes and elements for the specified level
        level_nodes = [n for n in nodes if abs(n.get('z', 0) - level) < 0.1]
        level_elements = []
        
        for element in elements:
            start_node = next((n for n in nodes if n['id'] == element['nodeIds'][0]), None)
            end_node = next((n for n in nodes if n['id'] == element['nodeIds'][1]), None)
            
            if (start_node and end_node and 
                abs(start_node.get('z', 0) - level) < 0.1 and 
                abs(end_node.get('z', 0) - level) < 0.1):
                level_elements.append(element)
        
        # Draw grid lines
        self._draw_grid(msp, level_nodes)
        
        # Draw structural elements
        for element in level_elements:
            start_node = next((n for n in nodes if n['id'] == element['nodeIds'][0]), None)
            end_node = next((n for n in nodes if n['id'] == element['nodeIds'][1]), None)
            
            if start_node and end_node:
                self._draw_element_plan(msp, start_node, end_node, element)
        
        # Draw nodes
        for node in level_nodes:
            self._draw_node_plan(msp, node)
        
        # Add dimensions
        self._add_plan_dimensions(msp, level_nodes, level_elements)
        
        # Add title block
        self._add_title_block(msp, f"Structural Plan - Level {level}m")
        
        # Save DXF file
        if not output_path:
            output_path = f"structural_plan_level_{level}.dxf"
        
        doc.saveas(output_path)
        return output_path
    
    def create_elevation_drawing(self, 
                               nodes: List[Dict], 
                               elements: List[Dict],
                               direction: str = 'front',
                               output_path: str = None) -> str:
        """Generate elevation drawing"""
        
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        # Project nodes to 2D based on direction
        projected_nodes = self._project_nodes_for_elevation(nodes, direction)
        
        # Draw structural elements in elevation
        for element in elements:
            start_node = next((n for n in projected_nodes if n['id'] == element['nodeIds'][0]), None)
            end_node = next((n for n in projected_nodes if n['id'] == element['nodeIds'][1]), None)
            
            if start_node and end_node:
                self._draw_element_elevation(msp, start_node, end_node, element)
        
        # Draw nodes
        for node in projected_nodes:
            self._draw_node_elevation(msp, node)
        
        # Add level markers
        self._add_level_markers(msp, projected_nodes)
        
        # Add dimensions
        self._add_elevation_dimensions(msp, projected_nodes, elements)
        
        # Add title block
        self._add_title_block(msp, f"Structural Elevation - {direction.title()} View")
        
        if not output_path:
            output_path = f"structural_elevation_{direction}.dxf"
        
        doc.saveas(output_path)
        return output_path
    
    def create_section_drawing(self, 
                             nodes: List[Dict], 
                             elements: List[Dict],
                             section_line: Dict,
                             output_path: str = None) -> str:
        """Generate section drawing"""
        
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        # Find elements that intersect with section line
        section_elements = self._find_section_elements(elements, nodes, section_line)
        
        # Draw section view
        for element in section_elements:
            start_node = next((n for n in nodes if n['id'] == element['nodeIds'][0]), None)
            end_node = next((n for n in nodes if n['id'] == element['nodeIds'][1]), None)
            
            if start_node and end_node:
                self._draw_element_section(msp, start_node, end_node, element, section_line)
        
        # Add section markers
        self._add_section_markers(msp, section_elements, nodes)
        
        # Add title block
        self._add_title_block(msp, f"Structural Section")
        
        if not output_path:
            output_path = f"structural_section.dxf"
        
        doc.saveas(output_path)
        return output_path
    
    def create_reinforcement_drawing(self, 
                                   element: Dict,
                                   reinforcement_data: Dict,
                                   output_path: str = None) -> str:
        """Generate reinforcement detailing drawing"""
        
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        # Draw element outline
        self._draw_element_outline(msp, element)
        
        # Draw reinforcement bars
        if 'longitudinal_bars' in reinforcement_data:
            self._draw_longitudinal_reinforcement(msp, reinforcement_data['longitudinal_bars'])
        
        if 'stirrups' in reinforcement_data:
            self._draw_stirrups(msp, reinforcement_data['stirrups'])
        
        # Add reinforcement schedule
        self._add_reinforcement_schedule(msp, reinforcement_data)
        
        # Add dimensions and annotations
        self._add_reinforcement_dimensions(msp, element, reinforcement_data)
        
        # Add title block
        self._add_title_block(msp, f"Reinforcement Details - {element.get('id', 'Element')}")
        
        if not output_path:
            output_path = f"reinforcement_details_{element.get('id', 'element')}.dxf"
        
        doc.saveas(output_path)
        return output_path
    
    def generate_bar_bending_schedule(self, 
                                    reinforcement_data: List[Dict],
                                    output_path: str = None) -> str:
        """Generate Bar Bending Schedule (BBS)"""
        
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        if not output_path:
            output_path = "bar_bending_schedule.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph("BAR BENDING SCHEDULE", styles['Title'])
        story.append(title)
        
        # Create table data
        headers = ['Mark', 'Diameter', 'Length', 'Shape', 'Quantity', 'Total Length', 'Weight (kg)']
        data = [headers]
        
        total_weight = 0
        
        for rebar in reinforcement_data:
            mark = rebar.get('mark', '')
            diameter = rebar.get('diameter', 0)
            length = rebar.get('length', 0)
            shape = rebar.get('shape', 'Straight')
            quantity = rebar.get('quantity', 1)
            total_length = length * quantity
            
            # Calculate weight (assuming steel density of 7850 kg/m³)
            area = np.pi * (diameter/2)**2 / 1000000  # Convert mm² to m²
            weight = area * (total_length/1000) * 7850  # kg
            total_weight += weight
            
            data.append([
                mark,
                f"{diameter}mm",
                f"{length}mm",
                shape,
                str(quantity),
                f"{total_length}mm",
                f"{weight:.2f}"
            ])
        
        # Add total row
        data.append(['', '', '', '', 'TOTAL', '', f"{total_weight:.2f}"])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#4CAF50'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f2f2f2'),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ('BACKGROUND', (0, -1), (-1, -1), '#ffeb3b'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        return output_path
    
    def export_to_pdf(self, dxf_path: str, output_path: str = None) -> str:
        """Convert DXF to PDF"""
        
        if not output_path:
            output_path = dxf_path.replace('.dxf', '.pdf')
        
        # Load DXF document
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Create matplotlib figure
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111)
        
        # Render DXF to matplotlib
        ctx = RenderContext(doc)
        out = MatplotlibBackend(ax)
        Frontend(ctx, out).draw_layout(msp, finalize=True)
        
        # Save as PDF
        plt.savefig(output_path, format='pdf', bbox_inches='tight', dpi=300)
        plt.close()
        
        return output_path
    
    # Helper methods
    def _draw_grid(self, msp, nodes: List[Dict]):
        """Draw grid lines"""
        if not nodes:
            return
        
        # Find grid extents
        x_coords = [n['x'] for n in nodes]
        y_coords = [n['y'] for n in nodes]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Draw grid lines every 5m
        grid_spacing = 5000  # 5m in mm
        
        # Vertical grid lines
        x = min_x - (min_x % grid_spacing)
        while x <= max_x + grid_spacing:
            msp.add_line((x, min_y - 1000), (x, max_y + 1000), 
                        dxfattribs={'color': 8, 'linetype': 'DASHED'})
            x += grid_spacing
        
        # Horizontal grid lines
        y = min_y - (min_y % grid_spacing)
        while y <= max_y + grid_spacing:
            msp.add_line((min_x - 1000, y), (max_x + 1000, y), 
                        dxfattribs={'color': 8, 'linetype': 'DASHED'})
            y += grid_spacing
    
    def _draw_element_plan(self, msp, start_node: Dict, end_node: Dict, element: Dict):
        """Draw element in plan view"""
        start_point = (start_node['x'], start_node['y'])
        end_point = (end_node['x'], end_node['y'])
        
        # Different line types for different elements
        element_type = element.get('type', 'beam')
        if element_type == 'beam':
            color = 1  # Red
            lineweight = 50
        elif element_type == 'column':
            color = 2  # Yellow
            lineweight = 70
        else:
            color = 3  # Green
            lineweight = 30
        
        msp.add_line(start_point, end_point, 
                    dxfattribs={'color': color, 'lineweight': lineweight})
        
        # Add element label
        mid_x = (start_point[0] + end_point[0]) / 2
        mid_y = (start_point[1] + end_point[1]) / 2
        msp.add_text(element['id'], dxfattribs={'height': 200}).set_pos((mid_x, mid_y))
    
    def _draw_node_plan(self, msp, node: Dict):
        """Draw node in plan view"""
        center = (node['x'], node['y'])
        msp.add_circle(center, 100, dxfattribs={'color': 4})  # Cyan
        msp.add_text(node['id'], dxfattribs={'height': 150}).set_pos(
            (center[0] + 200, center[1] + 200))
    
    def _draw_element_elevation(self, msp, start_node: Dict, end_node: Dict, element: Dict):
        """Draw element in elevation view"""
        start_point = (start_node['x'], start_node['z'])
        end_point = (end_node['x'], end_node['z'])
        
        element_type = element.get('type', 'beam')
        if element_type == 'beam':
            color = 1
            lineweight = 50
        elif element_type == 'column':
            color = 2
            lineweight = 70
        else:
            color = 3
            lineweight = 30
        
        msp.add_line(start_point, end_point, 
                    dxfattribs={'color': color, 'lineweight': lineweight})
    
    def _draw_node_elevation(self, msp, node: Dict):
        """Draw node in elevation view"""
        center = (node['x'], node['z'])
        msp.add_circle(center, 100, dxfattribs={'color': 4})
    
    def _project_nodes_for_elevation(self, nodes: List[Dict], direction: str) -> List[Dict]:
        """Project 3D nodes to 2D for elevation view"""
        projected = []
        
        for node in nodes:
            if direction == 'front':
                # Front view: X-Z plane
                projected.append({
                    'id': node['id'],
                    'x': node['x'],
                    'z': node.get('z', 0)
                })
            elif direction == 'side':
                # Side view: Y-Z plane
                projected.append({
                    'id': node['id'],
                    'x': node['y'],
                    'z': node.get('z', 0)
                })
        
        return projected
    
    def _add_plan_dimensions(self, msp, nodes: List[Dict], elements: List[Dict]):
        """Add dimensions to plan view"""
        # Add basic dimensions between major grid lines
        pass
    
    def _add_elevation_dimensions(self, msp, nodes: List[Dict], elements: List[Dict]):
        """Add dimensions to elevation view"""
        # Add level dimensions
        pass
    
    def _add_level_markers(self, msp, nodes: List[Dict]):
        """Add level markers to elevation"""
        levels = list(set(node.get('z', 0) for node in nodes))
        levels.sort()
        
        for level in levels:
            # Add level line and label
            msp.add_text(f"Level {level}m", dxfattribs={'height': 200}).set_pos(
                (-2000, level))
    
    def _add_title_block(self, msp, title: str):
        """Add title block to drawing"""
        # Title block position (bottom right)
        x, y = 200000, 10000
        
        # Draw title block border
        msp.add_lwpolyline([
            (x, y), (x + 15000, y), (x + 15000, y + 8000), (x, y + 8000), (x, y)
        ], dxfattribs={'color': 0})
        
        # Add title text
        msp.add_text(title, dxfattribs={'height': 800}).set_pos((x + 500, y + 6000))
        msp.add_text(f"Date: {datetime.now().strftime('%Y-%m-%d')}", 
                    dxfattribs={'height': 400}).set_pos((x + 500, y + 4500))
        msp.add_text("StruMind - Structural Engineering Platform", 
                    dxfattribs={'height': 400}).set_pos((x + 500, y + 3000))
    
    def _find_section_elements(self, elements: List[Dict], nodes: List[Dict], section_line: Dict) -> List[Dict]:
        """Find elements that intersect with section line"""
        # Simplified implementation - would need proper geometric intersection
        return elements
    
    def _draw_element_section(self, msp, start_node: Dict, end_node: Dict, element: Dict, section_line: Dict):
        """Draw element in section view"""
        # Simplified section view
        start_point = (start_node['x'], start_node.get('z', 0))
        end_point = (end_node['x'], end_node.get('z', 0))
        
        msp.add_line(start_point, end_point, dxfattribs={'color': 1, 'lineweight': 50})
    
    def _add_section_markers(self, msp, elements: List[Dict], nodes: List[Dict]):
        """Add section markers"""
        pass
    
    def _draw_element_outline(self, msp, element: Dict):
        """Draw element outline for reinforcement drawing"""
        # Simplified beam outline
        width = element.get('width', 300)
        height = element.get('height', 600)
        length = element.get('length', 6000)
        
        # Draw beam outline
        msp.add_lwpolyline([
            (0, 0), (length, 0), (length, height), (0, height), (0, 0)
        ], dxfattribs={'color': 0})
    
    def _draw_longitudinal_reinforcement(self, msp, bars: List[Dict]):
        """Draw longitudinal reinforcement bars"""
        for bar in bars:
            x = bar.get('x', 0)
            y = bar.get('y', 0)
            diameter = bar.get('diameter', 16)
            
            msp.add_circle((x, y), diameter/2, dxfattribs={'color': 1})
    
    def _draw_stirrups(self, msp, stirrups: List[Dict]):
        """Draw stirrup reinforcement"""
        for stirrup in stirrups:
            x = stirrup.get('x', 0)
            width = stirrup.get('width', 250)
            height = stirrup.get('height', 550)
            
            # Draw stirrup outline
            msp.add_lwpolyline([
                (x, 25), (x + width, 25), (x + width, height - 25), 
                (x, height - 25), (x, 25)
            ], dxfattribs={'color': 2})
    
    def _add_reinforcement_schedule(self, msp, reinforcement_data: Dict):
        """Add reinforcement schedule to drawing"""
        # Add schedule table
        x, y = 8000, 1000
        msp.add_text("REINFORCEMENT SCHEDULE", dxfattribs={'height': 300}).set_pos((x, y))
    
    def _add_reinforcement_dimensions(self, msp, element: Dict, reinforcement_data: Dict):
        """Add dimensions to reinforcement drawing"""
        # Add basic dimensions
        pass