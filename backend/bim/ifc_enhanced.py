"""
Enhanced IFC (Industry Foundation Classes) import/export with full BIM integration
"""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime
import uuid
import json

class IFCEnhancedProcessor:
    """Enhanced IFC processor with full BIM capabilities"""
    
    def __init__(self):
        self.ifc_file = None
        self.project = None
        self.site = None
        self.building = None
        self.building_storey = None
        
    def create_new_ifc_project(self, project_data: Dict[str, Any]) -> ifcopenshell.file:
        """Create a new IFC project from scratch"""
        
        # Create new IFC file
        self.ifc_file = ifcopenshell.api.run("root.create_entity", 
                                           ifcopenshell.file(schema="IFC4"), 
                                           ifc_class="IfcProject")
        
        # Set up project information
        self.project = ifcopenshell.api.run("root.create_entity", 
                                          self.ifc_file, 
                                          ifc_class="IfcProject",
                                          name=project_data.get('name', 'StruMind Project'))
        
        # Create project context
        self._create_project_context()
        
        # Create site
        self.site = ifcopenshell.api.run("root.create_entity", 
                                       self.ifc_file, 
                                       ifc_class="IfcSite",
                                       name=project_data.get('site_name', 'Project Site'))
        
        # Create building
        self.building = ifcopenshell.api.run("root.create_entity", 
                                           self.ifc_file, 
                                           ifc_class="IfcBuilding",
                                           name=project_data.get('building_name', 'Main Building'))
        
        # Establish spatial hierarchy
        ifcopenshell.api.run("aggregate.assign_object", 
                           self.ifc_file, 
                           relating_object=self.project, 
                           product=self.site)
        
        ifcopenshell.api.run("aggregate.assign_object", 
                           self.ifc_file, 
                           relating_object=self.site, 
                           product=self.building)
        
        return self.ifc_file
    
    def import_structural_model(self, ifc_path: str) -> Dict[str, Any]:
        """Import structural model from IFC file"""
        
        self.ifc_file = ifcopenshell.open(ifc_path)
        
        # Extract structural elements
        structural_data = {
            'nodes': [],
            'elements': [],
            'materials': [],
            'sections': [],
            'loads': [],
            'load_cases': [],
            'building_info': {},
            'spatial_structure': []
        }
        
        # Extract building information
        structural_data['building_info'] = self._extract_building_info()
        
        # Extract spatial structure
        structural_data['spatial_structure'] = self._extract_spatial_structure()
        
        # Extract structural elements
        structural_data['elements'] = self._extract_structural_elements()
        
        # Extract nodes from structural elements
        structural_data['nodes'] = self._extract_structural_nodes()
        
        # Extract materials
        structural_data['materials'] = self._extract_materials()
        
        # Extract sections
        structural_data['sections'] = self._extract_sections()
        
        # Extract loads
        structural_data['loads'] = self._extract_loads()
        
        # Extract load cases
        structural_data['load_cases'] = self._extract_load_cases()
        
        return structural_data
    
    def export_structural_model(self, structural_data: Dict[str, Any], output_path: str) -> str:
        """Export structural model to IFC file"""
        
        # Create new IFC project if not exists
        if not self.ifc_file:
            self.create_new_ifc_project(structural_data.get('project_info', {}))
        
        # Create building storeys
        self._create_building_storeys(structural_data.get('spatial_structure', []))
        
        # Create materials
        material_map = self._create_materials(structural_data.get('materials', []))
        
        # Create sections
        section_map = self._create_sections(structural_data.get('sections', []), material_map)
        
        # Create structural nodes
        node_map = self._create_structural_nodes(structural_data.get('nodes', []))
        
        # Create structural elements
        element_map = self._create_structural_elements(
            structural_data.get('elements', []), 
            node_map, 
            section_map
        )
        
        # Create loads
        self._create_loads(structural_data.get('loads', []), node_map, element_map)
        
        # Create load cases
        self._create_load_cases(structural_data.get('load_cases', []))
        
        # Save IFC file
        self.ifc_file.write(output_path)
        return output_path
    
    def export_for_revit(self, structural_data: Dict[str, Any], output_path: str) -> str:
        """Export model in Revit-compatible IFC format"""
        
        # Set Revit-specific settings
        self._configure_for_revit()
        
        # Export with Revit compatibility
        return self.export_structural_model(structural_data, output_path)
    
    def export_for_tekla(self, structural_data: Dict[str, Any], output_path: str) -> str:
        """Export model in Tekla-compatible format"""
        
        # Set Tekla-specific settings
        self._configure_for_tekla()
        
        # Export with Tekla compatibility
        return self.export_structural_model(structural_data, output_path)
    
    def _create_project_context(self):
        """Create project context and coordinate systems"""
        
        # Create geometric representation context
        context = ifcopenshell.api.run("context.add_context", 
                                     self.ifc_file, 
                                     context_type="Model")
        
        # Create 3D body context
        body_context = ifcopenshell.api.run("context.add_context", 
                                          self.ifc_file,
                                          context_type="Model", 
                                          context_identifier="Body", 
                                          target_view="MODEL_VIEW", 
                                          parent=context)
        
        # Create axis context
        axis_context = ifcopenshell.api.run("context.add_context", 
                                          self.ifc_file,
                                          context_type="Model", 
                                          context_identifier="Axis", 
                                          target_view="GRAPH_VIEW", 
                                          parent=context)
    
    def _extract_building_info(self) -> Dict[str, Any]:
        """Extract building information from IFC"""
        
        building_info = {}
        
        # Get project
        project = self.ifc_file.by_type("IfcProject")[0] if self.ifc_file.by_type("IfcProject") else None
        if project:
            building_info['project_name'] = project.Name
            building_info['project_description'] = project.Description
        
        # Get building
        buildings = self.ifc_file.by_type("IfcBuilding")
        if buildings:
            building = buildings[0]
            building_info['building_name'] = building.Name
            building_info['building_description'] = building.Description
            
            # Get building address
            if building.BuildingAddress:
                address = building.BuildingAddress
                building_info['address'] = {
                    'street': address.AddressLines[0] if address.AddressLines else None,
                    'city': address.Town,
                    'country': address.Country,
                    'postal_code': address.PostalCode
                }
        
        return building_info
    
    def _extract_spatial_structure(self) -> List[Dict[str, Any]]:
        """Extract spatial structure (storeys, spaces)"""
        
        spatial_structure = []
        
        # Get building storeys
        storeys = self.ifc_file.by_type("IfcBuildingStorey")
        for storey in storeys:
            storey_data = {
                'id': storey.GlobalId,
                'name': storey.Name,
                'description': storey.Description,
                'elevation': storey.Elevation if hasattr(storey, 'Elevation') else 0.0,
                'type': 'storey'
            }
            spatial_structure.append(storey_data)
        
        # Get spaces
        spaces = self.ifc_file.by_type("IfcSpace")
        for space in spaces:
            space_data = {
                'id': space.GlobalId,
                'name': space.Name,
                'description': space.Description,
                'type': 'space'
            }
            spatial_structure.append(space_data)
        
        return spatial_structure
    
    def _extract_structural_elements(self) -> List[Dict[str, Any]]:
        """Extract structural elements (beams, columns, slabs, etc.)"""
        
        elements = []
        
        # Extract beams
        beams = self.ifc_file.by_type("IfcBeam")
        for beam in beams:
            element_data = self._extract_element_data(beam, 'beam')
            elements.append(element_data)
        
        # Extract columns
        columns = self.ifc_file.by_type("IfcColumn")
        for column in columns:
            element_data = self._extract_element_data(column, 'column')
            elements.append(element_data)
        
        # Extract slabs
        slabs = self.ifc_file.by_type("IfcSlab")
        for slab in slabs:
            element_data = self._extract_element_data(slab, 'slab')
            elements.append(element_data)
        
        # Extract walls (structural)
        walls = self.ifc_file.by_type("IfcWall")
        for wall in walls:
            # Check if wall is structural
            if self._is_structural_wall(wall):
                element_data = self._extract_element_data(wall, 'wall')
                elements.append(element_data)
        
        # Extract structural members
        members = self.ifc_file.by_type("IfcStructuralMember")
        for member in members:
            element_data = self._extract_structural_member_data(member)
            elements.append(element_data)
        
        return elements
    
    def _extract_element_data(self, element, element_type: str) -> Dict[str, Any]:
        """Extract data from IFC element"""
        
        element_data = {
            'id': element.GlobalId,
            'name': element.Name,
            'description': element.Description,
            'type': element_type,
            'geometry': self._extract_geometry(element),
            'material': self._extract_element_material(element),
            'properties': self._extract_element_properties(element)
        }
        
        return element_data
    
    def _extract_structural_member_data(self, member) -> Dict[str, Any]:
        """Extract structural member data"""
        
        member_data = {
            'id': member.GlobalId,
            'name': member.Name,
            'description': member.Description,
            'type': 'structural_member',
            'predefined_type': member.PredefinedType if hasattr(member, 'PredefinedType') else None,
            'geometry': self._extract_geometry(member),
            'material': self._extract_element_material(member),
            'properties': self._extract_element_properties(member)
        }
        
        return member_data
    
    def _extract_geometry(self, element) -> Dict[str, Any]:
        """Extract geometry information from element"""
        
        geometry = {
            'placement': None,
            'representation': None,
            'bounding_box': None
        }
        
        # Extract placement
        if element.ObjectPlacement:
            placement = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
            geometry['placement'] = {
                'location': placement[:3, 3].tolist(),
                'rotation_matrix': placement[:3, :3].tolist()
            }
        
        # Extract representation
        if element.Representation:
            representations = element.Representation.Representations
            for rep in representations:
                if rep.RepresentationIdentifier == "Body":
                    geometry['representation'] = self._extract_representation_data(rep)
                    break
        
        return geometry
    
    def _extract_representation_data(self, representation) -> Dict[str, Any]:
        """Extract representation data"""
        
        rep_data = {
            'type': representation.RepresentationType,
            'items': []
        }
        
        for item in representation.Items:
            item_data = {
                'type': item.is_a(),
                'parameters': {}
            }
            
            # Extract specific parameters based on item type
            if item.is_a("IfcExtrudedAreaSolid"):
                item_data['parameters'] = {
                    'depth': item.Depth,
                    'swept_area': self._extract_profile_data(item.SweptArea)
                }
            elif item.is_a("IfcRectangleProfileDef"):
                item_data['parameters'] = {
                    'x_dim': item.XDim,
                    'y_dim': item.YDim
                }
            
            rep_data['items'].append(item_data)
        
        return rep_data
    
    def _extract_profile_data(self, profile) -> Dict[str, Any]:
        """Extract profile definition data"""
        
        profile_data = {
            'type': profile.is_a(),
            'name': profile.ProfileName if hasattr(profile, 'ProfileName') else None
        }
        
        if profile.is_a("IfcRectangleProfileDef"):
            profile_data.update({
                'x_dim': profile.XDim,
                'y_dim': profile.YDim
            })
        elif profile.is_a("IfcIShapeProfileDef"):
            profile_data.update({
                'overall_width': profile.OverallWidth,
                'overall_depth': profile.OverallDepth,
                'web_thickness': profile.WebThickness,
                'flange_thickness': profile.FlangeThickness
            })
        
        return profile_data
    
    def _extract_structural_nodes(self) -> List[Dict[str, Any]]:
        """Extract structural nodes from elements"""
        
        nodes = []
        node_id_counter = 1
        
        # Extract from structural point connections
        point_connections = self.ifc_file.by_type("IfcStructuralPointConnection")
        for connection in point_connections:
            node_data = {
                'id': connection.GlobalId,
                'name': connection.Name or f"N{node_id_counter}",
                'coordinates': self._extract_point_coordinates(connection),
                'boundary_conditions': self._extract_boundary_conditions(connection)
            }
            nodes.append(node_data)
            node_id_counter += 1
        
        return nodes
    
    def _extract_point_coordinates(self, point_connection) -> List[float]:
        """Extract coordinates from structural point connection"""
        
        if point_connection.ObjectPlacement:
            placement = ifcopenshell.util.placement.get_local_placement(point_connection.ObjectPlacement)
            return placement[:3, 3].tolist()
        
        return [0.0, 0.0, 0.0]
    
    def _extract_boundary_conditions(self, connection) -> Dict[str, Any]:
        """Extract boundary conditions from connection"""
        
        boundary_conditions = {
            'translation_x': 'free',
            'translation_y': 'free',
            'translation_z': 'free',
            'rotation_x': 'free',
            'rotation_y': 'free',
            'rotation_z': 'free'
        }
        
        # Extract from applied conditions
        if hasattr(connection, 'AppliedCondition') and connection.AppliedCondition:
            condition = connection.AppliedCondition
            if condition.is_a("IfcBoundaryNodeCondition"):
                if hasattr(condition, 'TranslationalStiffnessX'):
                    boundary_conditions['translation_x'] = 'fixed' if condition.TranslationalStiffnessX else 'free'
                if hasattr(condition, 'TranslationalStiffnessY'):
                    boundary_conditions['translation_y'] = 'fixed' if condition.TranslationalStiffnessY else 'free'
                if hasattr(condition, 'TranslationalStiffnessZ'):
                    boundary_conditions['translation_z'] = 'fixed' if condition.TranslationalStiffnessZ else 'free'
                if hasattr(condition, 'RotationalStiffnessX'):
                    boundary_conditions['rotation_x'] = 'fixed' if condition.RotationalStiffnessX else 'free'
                if hasattr(condition, 'RotationalStiffnessY'):
                    boundary_conditions['rotation_y'] = 'fixed' if condition.RotationalStiffnessY else 'free'
                if hasattr(condition, 'RotationalStiffnessZ'):
                    boundary_conditions['rotation_z'] = 'fixed' if condition.RotationalStiffnessZ else 'free'
        
        return boundary_conditions
    
    def _extract_materials(self) -> List[Dict[str, Any]]:
        """Extract materials from IFC"""
        
        materials = []
        
        ifc_materials = self.ifc_file.by_type("IfcMaterial")
        for material in ifc_materials:
            material_data = {
                'id': material.id(),
                'name': material.Name,
                'description': material.Description if hasattr(material, 'Description') else None,
                'properties': self._extract_material_properties(material)
            }
            materials.append(material_data)
        
        return materials
    
    def _extract_material_properties(self, material) -> Dict[str, Any]:
        """Extract material properties"""
        
        properties = {}
        
        # Get material properties
        if hasattr(material, 'HasProperties'):
            for prop_set in material.HasProperties:
                if prop_set.is_a("IfcMaterialProperties"):
                    for prop in prop_set.Properties:
                        if prop.is_a("IfcPropertySingleValue"):
                            properties[prop.Name] = prop.NominalValue.wrappedValue if prop.NominalValue else None
        
        return properties
    
    def _extract_sections(self) -> List[Dict[str, Any]]:
        """Extract sections from IFC"""
        
        sections = []
        
        # Extract from profile definitions
        profiles = self.ifc_file.by_type("IfcProfileDef")
        for profile in profiles:
            section_data = {
                'id': profile.id(),
                'name': profile.ProfileName,
                'type': profile.is_a(),
                'properties': self._extract_profile_data(profile)
            }
            sections.append(section_data)
        
        return sections
    
    def _extract_loads(self) -> List[Dict[str, Any]]:
        """Extract loads from IFC"""
        
        loads = []
        
        # Extract structural loads
        structural_loads = self.ifc_file.by_type("IfcStructuralLoad")
        for load in structural_loads:
            load_data = {
                'id': load.id(),
                'name': load.Name if hasattr(load, 'Name') else None,
                'type': load.is_a(),
                'values': self._extract_load_values(load)
            }
            loads.append(load_data)
        
        return loads
    
    def _extract_load_values(self, load) -> Dict[str, Any]:
        """Extract load values"""
        
        values = {}
        
        if load.is_a("IfcStructuralLoadSingleForce"):
            values.update({
                'force_x': load.ForceX if hasattr(load, 'ForceX') else 0.0,
                'force_y': load.ForceY if hasattr(load, 'ForceY') else 0.0,
                'force_z': load.ForceZ if hasattr(load, 'ForceZ') else 0.0,
                'moment_x': load.MomentX if hasattr(load, 'MomentX') else 0.0,
                'moment_y': load.MomentY if hasattr(load, 'MomentY') else 0.0,
                'moment_z': load.MomentZ if hasattr(load, 'MomentZ') else 0.0
            })
        elif load.is_a("IfcStructuralLoadLinearForce"):
            values.update({
                'linear_force_x': load.LinearForceX if hasattr(load, 'LinearForceX') else 0.0,
                'linear_force_y': load.LinearForceY if hasattr(load, 'LinearForceY') else 0.0,
                'linear_force_z': load.LinearForceZ if hasattr(load, 'LinearForceZ') else 0.0,
                'linear_moment_x': load.LinearMomentX if hasattr(load, 'LinearMomentX') else 0.0,
                'linear_moment_y': load.LinearMomentY if hasattr(load, 'LinearMomentY') else 0.0,
                'linear_moment_z': load.LinearMomentZ if hasattr(load, 'LinearMomentZ') else 0.0
            })
        
        return values
    
    def _extract_load_cases(self) -> List[Dict[str, Any]]:
        """Extract load cases from IFC"""
        
        load_cases = []
        
        # Extract structural load cases
        ifc_load_cases = self.ifc_file.by_type("IfcStructuralLoadCase")
        for load_case in ifc_load_cases:
            load_case_data = {
                'id': load_case.GlobalId,
                'name': load_case.Name,
                'description': load_case.Description if hasattr(load_case, 'Description') else None,
                'action_type': load_case.ActionType if hasattr(load_case, 'ActionType') else None,
                'action_source': load_case.ActionSource if hasattr(load_case, 'ActionSource') else None
            }
            load_cases.append(load_case_data)
        
        return load_cases
    
    def _is_structural_wall(self, wall) -> bool:
        """Check if wall is structural"""
        
        # Check if wall has structural property
        if hasattr(wall, 'IsDefinedBy'):
            for definition in wall.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    prop_set = definition.RelatingPropertyDefinition
                    if prop_set.Name and 'structural' in prop_set.Name.lower():
                        return True
        
        return False
    
    def _extract_element_material(self, element) -> Optional[str]:
        """Extract material from element"""
        
        if hasattr(element, 'HasAssociations'):
            for association in element.HasAssociations:
                if association.is_a("IfcRelAssociatesMaterial"):
                    material = association.RelatingMaterial
                    if material.is_a("IfcMaterial"):
                        return material.Name
                    elif material.is_a("IfcMaterialLayerSetUsage"):
                        return material.ForLayerSet.MaterialLayers[0].Material.Name
        
        return None
    
    def _extract_element_properties(self, element) -> Dict[str, Any]:
        """Extract properties from element"""
        
        properties = {}
        
        if hasattr(element, 'IsDefinedBy'):
            for definition in element.IsDefinedBy:
                if definition.is_a("IfcRelDefinesByProperties"):
                    prop_set = definition.RelatingPropertyDefinition
                    if prop_set.is_a("IfcPropertySet"):
                        for prop in prop_set.HasProperties:
                            if prop.is_a("IfcPropertySingleValue"):
                                properties[prop.Name] = prop.NominalValue.wrappedValue if prop.NominalValue else None
        
        return properties
    
    def _create_building_storeys(self, spatial_structure: List[Dict[str, Any]]):
        """Create building storeys in IFC"""
        
        storeys = [item for item in spatial_structure if item.get('type') == 'storey']
        
        for storey_data in storeys:
            storey = ifcopenshell.api.run("root.create_entity", 
                                        self.ifc_file, 
                                        ifc_class="IfcBuildingStorey",
                                        name=storey_data.get('name', 'Level'))
            
            storey.Elevation = storey_data.get('elevation', 0.0)
            
            # Assign to building
            ifcopenshell.api.run("aggregate.assign_object", 
                               self.ifc_file, 
                               relating_object=self.building, 
                               product=storey)
    
    def _create_materials(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create materials in IFC"""
        
        material_map = {}
        
        for material_data in materials:
            material = ifcopenshell.api.run("material.add_material", 
                                          self.ifc_file, 
                                          name=material_data.get('name', 'Material'))
            
            # Add material properties
            properties = material_data.get('properties', {})
            if properties:
                prop_set = ifcopenshell.api.run("pset.add_pset", 
                                              self.ifc_file, 
                                              product=material, 
                                              name="MaterialProperties")
                
                for prop_name, prop_value in properties.items():
                    ifcopenshell.api.run("pset.edit_pset", 
                                       self.ifc_file, 
                                       pset=prop_set, 
                                       properties={prop_name: prop_value})
            
            material_map[material_data.get('id')] = material
        
        return material_map
    
    def _create_sections(self, sections: List[Dict[str, Any]], material_map: Dict[str, Any]) -> Dict[str, Any]:
        """Create sections in IFC"""
        
        section_map = {}
        
        for section_data in sections:
            # Create profile based on type
            section_type = section_data.get('type', 'IfcRectangleProfileDef')
            properties = section_data.get('properties', {})
            
            if section_type == 'IfcRectangleProfileDef':
                profile = self.ifc_file.create_entity("IfcRectangleProfileDef",
                    ProfileType="AREA",
                    ProfileName=section_data.get('name', 'Section'),
                    XDim=properties.get('x_dim', 300),
                    YDim=properties.get('y_dim', 600)
                )
            elif section_type == 'IfcIShapeProfileDef':
                profile = self.ifc_file.create_entity("IfcIShapeProfileDef",
                    ProfileType="AREA",
                    ProfileName=section_data.get('name', 'Section'),
                    OverallWidth=properties.get('overall_width', 200),
                    OverallDepth=properties.get('overall_depth', 400),
                    WebThickness=properties.get('web_thickness', 10),
                    FlangeThickness=properties.get('flange_thickness', 15)
                )
            else:
                # Default to rectangle
                profile = self.ifc_file.create_entity("IfcRectangleProfileDef",
                    ProfileType="AREA",
                    ProfileName=section_data.get('name', 'Section'),
                    XDim=300,
                    YDim=600
                )
            
            section_map[section_data.get('id')] = profile
        
        return section_map
    
    def _create_structural_nodes(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create structural nodes in IFC"""
        
        node_map = {}
        
        for node_data in nodes:
            # Create structural point connection
            point_connection = ifcopenshell.api.run("root.create_entity", 
                                                   self.ifc_file, 
                                                   ifc_class="IfcStructuralPointConnection",
                                                   name=node_data.get('name', 'Node'))
            
            # Set placement
            coordinates = node_data.get('coordinates', [0, 0, 0])
            placement = self.ifc_file.create_entity("IfcLocalPlacement",
                PlacementRelTo=None,
                RelativePlacement=self.ifc_file.create_entity("IfcAxis2Placement3D",
                    Location=self.ifc_file.create_entity("IfcCartesianPoint", coordinates)
                )
            )
            point_connection.ObjectPlacement = placement
            
            # Add boundary conditions
            boundary_conditions = node_data.get('boundary_conditions', {})
            if boundary_conditions:
                condition = self.ifc_file.create_entity("IfcBoundaryNodeCondition",
                    Name="BoundaryCondition",
                    TranslationalStiffnessX=boundary_conditions.get('translation_x') == 'fixed',
                    TranslationalStiffnessY=boundary_conditions.get('translation_y') == 'fixed',
                    TranslationalStiffnessZ=boundary_conditions.get('translation_z') == 'fixed',
                    RotationalStiffnessX=boundary_conditions.get('rotation_x') == 'fixed',
                    RotationalStiffnessY=boundary_conditions.get('rotation_y') == 'fixed',
                    RotationalStiffnessZ=boundary_conditions.get('rotation_z') == 'fixed'
                )
                point_connection.AppliedCondition = condition
            
            node_map[node_data.get('id')] = point_connection
        
        return node_map
    
    def _create_structural_elements(self, elements: List[Dict[str, Any]], 
                                  node_map: Dict[str, Any], 
                                  section_map: Dict[str, Any]) -> Dict[str, Any]:
        """Create structural elements in IFC"""
        
        element_map = {}
        
        for element_data in elements:
            element_type = element_data.get('type', 'beam')
            
            if element_type == 'beam':
                element = ifcopenshell.api.run("root.create_entity", 
                                             self.ifc_file, 
                                             ifc_class="IfcBeam",
                                             name=element_data.get('name', 'Beam'))
            elif element_type == 'column':
                element = ifcopenshell.api.run("root.create_entity", 
                                             self.ifc_file, 
                                             ifc_class="IfcColumn",
                                             name=element_data.get('name', 'Column'))
            else:
                element = ifcopenshell.api.run("root.create_entity", 
                                             self.ifc_file, 
                                             ifc_class="IfcStructuralMember",
                                             name=element_data.get('name', 'Member'))
            
            element_map[element_data.get('id')] = element
        
        return element_map
    
    def _create_loads(self, loads: List[Dict[str, Any]], 
                     node_map: Dict[str, Any], 
                     element_map: Dict[str, Any]):
        """Create loads in IFC"""
        
        for load_data in loads:
            load_type = load_data.get('type', 'IfcStructuralLoadSingleForce')
            values = load_data.get('values', {})
            
            if load_type == 'IfcStructuralLoadSingleForce':
                load = self.ifc_file.create_entity("IfcStructuralLoadSingleForce",
                    Name=load_data.get('name', 'Load'),
                    ForceX=values.get('force_x', 0.0),
                    ForceY=values.get('force_y', 0.0),
                    ForceZ=values.get('force_z', 0.0),
                    MomentX=values.get('moment_x', 0.0),
                    MomentY=values.get('moment_y', 0.0),
                    MomentZ=values.get('moment_z', 0.0)
                )
    
    def _create_load_cases(self, load_cases: List[Dict[str, Any]]):
        """Create load cases in IFC"""
        
        for load_case_data in load_cases:
            load_case = ifcopenshell.api.run("root.create_entity", 
                                           self.ifc_file, 
                                           ifc_class="IfcStructuralLoadCase",
                                           name=load_case_data.get('name', 'Load Case'))
            
            load_case.ActionType = load_case_data.get('action_type', 'PERMANENT_G')
            load_case.ActionSource = load_case_data.get('action_source', 'DEAD_LOAD_G')
    
    def _configure_for_revit(self):
        """Configure IFC settings for Revit compatibility"""
        
        # Set Revit-specific application info
        application = self.ifc_file.by_type("IfcApplication")[0] if self.ifc_file.by_type("IfcApplication") else None
        if application:
            application.ApplicationFullName = "StruMind for Revit"
            application.Version = "2024"
    
    def _configure_for_tekla(self):
        """Configure IFC settings for Tekla compatibility"""
        
        # Set Tekla-specific application info
        application = self.ifc_file.by_type("IfcApplication")[0] if self.ifc_file.by_type("IfcApplication") else None
        if application:
            application.ApplicationFullName = "StruMind for Tekla"
            application.Version = "2024"