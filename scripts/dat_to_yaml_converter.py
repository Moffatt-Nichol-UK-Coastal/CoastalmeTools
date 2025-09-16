#!/usr/bin/env python3
"""
CoastalME .dat to YAML Converter

This script converts CoastalME .dat configuration files to the new YAML format.
The converter preserves all parameter values and adds proper structure and comments.

Usage:
    python dat_to_yaml_converter.py input.dat [output.yaml]
    
If no output file is specified, it will create a .yaml file with the same base name.

Author: CoastalME Development Team
Date: 2025
"""

import sys
import os
import re
import yaml
from pathlib import Path


class DatToYamlConverter:
    """Converts CoastalME .dat files to YAML format"""
    
    def __init__(self):
        self.line_number = 0
        self.config = {}
        
        # Parameter mapping from .dat line numbers to YAML structure
        self.parameter_map = {
            1: ('run_information', 'output_file_names'),
            2: ('run_information', 'log_file_detail'),
            3: ('run_information', 'csv_per_timestep_results'),
            4: ('simulation', 'start_date_time'),
            5: ('simulation', 'duration'),
            6: ('simulation', 'timestep'),
            7: ('simulation', 'save_times'),
            8: ('simulation', 'random_seed'),
            9: ('gis_output', 'max_save_digits'),
            10: ('gis_output', 'save_digits_mode'),
            11: ('gis_output', 'raster_files'),
            12: ('gis_output', 'raster_format'),
            13: ('gis_output', 'world_file'),
            14: ('gis_output', 'scale_values'),
            15: ('gis_output', 'slice_elevations'),
            16: ('gis_output', 'vector_files'),
            17: ('gis_output', 'vector_format'),
            18: ('gis_output', 'time_series_files'),
            19: ('grid_and_coastline', 'coastline_smoothing'),
            20: ('grid_and_coastline', 'coastline_smoothing_window'),
            21: ('grid_and_coastline', 'polynomial_order'),
            22: ('grid_and_coastline', 'omit_grid_edges'),
            23: ('grid_and_coastline', 'profile_smoothing_window'),
            24: ('grid_and_coastline', 'max_local_slope'),
            25: ('grid_and_coastline', 'max_beach_elevation'),
            26: ('layers_and_files', 'num_layers'),
            27: ('layers_and_files', 'basement_dem_file'),
            # Layer 0 thickness files (lines 28-35 are dynamic based on layers)
            30: ('layers_and_files', 'layer_0', 'unconsolidated_fine'),
            31: ('layers_and_files', 'layer_0', 'unconsolidated_sand'),
            32: ('layers_and_files', 'layer_0', 'unconsolidated_coarse'),
            33: ('layers_and_files', 'layer_0', 'consolidated_fine'),
            34: ('layers_and_files', 'layer_0', 'consolidated_sand'),
            35: ('layers_and_files', 'layer_0', 'consolidated_coarse'),
            36: ('layers_and_files', 'suspended_sediment_file'),
            37: ('layers_and_files', 'landform_file'),
            38: ('layers_and_files', 'intervention_class_file'),
            39: ('layers_and_files', 'intervention_height_file'),
            40: ('hydrology', 'wave_propagation_model'),
            41: ('hydrology', 'seawater_density'),
            42: ('hydrology', 'initial_water_level'),
            43: ('hydrology', 'final_water_level'),
            44: ('hydrology', 'wave_height'),
            45: ('hydrology', 'wave_height_time_series'),
            46: ('hydrology', 'wave_orientation'),
            47: ('hydrology', 'wave_period'),
            48: ('hydrology', 'tide_data_file'),
            49: ('hydrology', 'breaking_wave_ratio'),
            50: ('sediment_and_erosion', 'coast_platform_erosion'),
            51: ('sediment_and_erosion', 'platform_erosion_resistance'),
            52: ('sediment_and_erosion', 'beach_sediment_transport'),
            53: ('sediment_and_erosion', 'beach_transport_at_edges'),
            54: ('sediment_and_erosion', 'beach_erosion_equation'),
            55: ('sediment_and_erosion', 'median_sizes', 'fine'),
            56: ('sediment_and_erosion', 'median_sizes', 'sand'),
            57: ('sediment_and_erosion', 'median_sizes', 'coarse'),
            58: ('sediment_and_erosion', 'sediment_density'),
            59: ('sediment_and_erosion', 'beach_sediment_porosity'),
            60: ('sediment_and_erosion', 'erosivity', 'fine'),
            61: ('sediment_and_erosion', 'erosivity', 'sand'),
            62: ('sediment_and_erosion', 'erosivity', 'coarse'),
            63: ('sediment_and_erosion', 'transport_kls'),
            64: ('sediment_and_erosion', 'kamphuis_parameter'),
            65: ('sediment_and_erosion', 'berm_height'),
            66: ('cliff_parameters', 'cliff_collapse'),
            67: ('cliff_parameters', 'cliff_erosion_resistance'),
            68: ('cliff_parameters', 'notch_overhang'),
            69: ('cliff_parameters', 'notch_base'),
            70: ('cliff_parameters', 'deposition_scale_parameter_a'),
            71: ('cliff_parameters', 'talus_width'),
            72: ('cliff_parameters', 'min_talus_length'),
            73: ('cliff_parameters', 'min_talus_height'),
            74: ('flood_parameters', 'flood_input'),
            75: ('flood_parameters', 'flood_coastline'),
            76: ('flood_parameters', 'runup_equation'),
            77: ('flood_parameters', 'characteristic_locations'),
            78: ('flood_parameters', 'flood_input_location'),
            79: ('sediment_input_parameters', 'sediment_input'),
            80: ('sediment_input_parameters', 'location'),
            81: ('sediment_input_parameters', 'type'),
            82: ('sediment_input_parameters', 'details_file'),
            83: ('physics_and_geometry', 'gravitational_acceleration'),
            84: ('physics_and_geometry', 'normal_spacing'),
            85: ('physics_and_geometry', 'random_factor'),
            86: ('physics_and_geometry', 'normal_length'),
            87: ('physics_and_geometry', 'start_depth_ratio'),
            88: ('profile_and_output', 'save_profile_data'),
            89: ('profile_and_output', 'profile_numbers'),
            90: ('profile_and_output', 'profile_timesteps'),
            91: ('profile_and_output', 'save_parallel_profiles'),
            92: ('profile_and_output', 'output_erosion_potential'),
            93: ('profile_and_output', 'curvature_window'),
            94: ('cliff_edge_processing', 'cliff_edge_smoothing'),
            95: ('cliff_edge_processing', 'cliff_edge_smoothing_window'),
            96: ('cliff_edge_processing', 'cliff_edge_polynomial_order'),
            97: ('cliff_edge_processing', 'cliff_slope_limit'),
        }
    
    def parse_dat_file(self, dat_file_path):
        """Parse a .dat file and extract parameter values"""
        self.config = {}
        param_index = 0
        
        with open(dat_file_path, 'r') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith(';'):
                continue
            
            param_index += 1
            
            # Find the colon separator
            colon_pos = line.find(':')
            if colon_pos == -1:
                continue
            
            # Extract value after colon
            value_part = line[colon_pos + 1:].strip()
            
            # Remove trailing comments
            comment_pos = value_part.find(';')
            if comment_pos != -1:
                value_part = value_part[:comment_pos].strip()
            
            # Convert value to appropriate type
            converted_value = self._convert_value(value_part, param_index)
            
            # Map to YAML structure
            if param_index in self.parameter_map:
                self._set_nested_value(self.config, self.parameter_map[param_index], converted_value)
    
    def _convert_value(self, value_str, param_index):
        """Convert string value to appropriate Python type"""
        if not value_str:
            return None
        
        # Handle special cases based on parameter type
        if param_index in [3, 13, 14, 50, 52, 66, 74, 79, 88, 91, 92]:  # Boolean parameters
            return self._parse_boolean(value_str)
        elif param_index == 7:  # Save times - convert to list
            return self._parse_save_times(value_str)
        elif param_index in [11, 16, 18]:  # File lists
            return self._parse_file_list(value_str)
        elif param_index == 15:  # Slice elevations - could be empty or list of numbers
            return self._parse_numeric_list(value_str)
        elif param_index in [89, 90]:  # Profile numbers/timesteps - could be empty or list
            return self._parse_numeric_list(value_str)
        elif param_index == 40:  # Wave propagation model - convert to string
            return "CShore" if value_str == "1" else "COVE"
        elif param_index == 54:  # Beach erosion equation
            return "CERC" if value_str == "0" else "Kamphuis"
        elif param_index == 10:  # Save digits mode
            return "sequential" if value_str.lower() == "s" else "iteration"
        elif param_index == 19:  # Coastline smoothing
            smoothing_map = {"0": "none", "1": "running_mean", "2": "savitzky_golay"}
            return smoothing_map.get(value_str, int(value_str))
        elif param_index == 94:  # Cliff edge smoothing
            smoothing_map = {"0": "none", "1": "running_mean", "2": "savitzky_golay"}
            return smoothing_map.get(value_str, int(value_str))
        else:
            # Try to convert to number, fallback to string
            try:
                if '.' in value_str or 'e' in value_str.lower():
                    return float(value_str)
                else:
                    return int(value_str)
            except ValueError:
                return value_str
    
    def _parse_boolean(self, value_str):
        """Parse boolean values from .dat format"""
        value_lower = value_str.lower()
        return value_lower in ['y', 'yes', 'true', '1']
    
    def _parse_save_times(self, value_str):
        """Parse save times string into list"""
        # Extract time values and units from format like "6 12 24 120 250 500 1000 3000 5000 hours"
        parts = value_str.split()
        if len(parts) == 0:
            return []
        
        # The last part should be the unit (hours, days, etc.)
        if parts[-1] in ['hours', 'days', 'months', 'years']:
            unit = parts[-1]
            numbers = parts[:-1]
            return [f"{num} {unit}" for num in numbers]
        else:
            # If no unit specified, assume the whole string is the time specification
            return [value_str]
    
    def _parse_file_list(self, value_str):
        """Parse file list specifications"""
        if value_str.lower() in ['usual', 'all']:
            return [value_str.lower()]
        else:
            # Could be a list of specific codes
            return [code.strip() for code in value_str.split()]
    
    def _parse_numeric_list(self, value_str):
        """Parse numeric lists"""
        if not value_str:
            return []
        try:
            return [float(x.strip()) for x in value_str.split() if x.strip()]
        except ValueError:
            return []
    
    def _set_nested_value(self, config_dict, keys, value):
        """Set a nested value in the configuration dictionary"""
        current = config_dict
        
        # Navigate/create nested structure
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def write_yaml_file(self, yaml_file_path):
        """Write the configuration to a YAML file with proper formatting"""
        
        # Custom YAML representer for better formatting
        def represent_none(self, data):
            return self.represent_scalar('tag:yaml.org,2002:null', '')
        
        yaml.add_representer(type(None), represent_none)
        
        # Create YAML content with header comment
        yaml_content = f"""# CoastalME Configuration File - YAML Format
# Converted from .dat file format
# 
# This file contains all simulation parameters for CoastalME.
# For parameter descriptions, see the original .dat file or CoastalME documentation.

"""
        
        # Add sections with comments
        sections = [
            ('run_information', 'Run Information Settings'),
            ('simulation', 'Simulation Timing and Control'),
            ('gis_output', 'GIS Output Configuration'),
            ('grid_and_coastline', 'Grid and Coastline Processing'),
            ('layers_and_files', 'Input Files and Layer Configuration'),
            ('hydrology', 'Hydrological Parameters'),
            ('sediment_and_erosion', 'Sediment Transport and Erosion'),
            ('cliff_parameters', 'Cliff Collapse Parameters'),
            ('flood_parameters', 'Flood Modeling Parameters'),
            ('sediment_input_parameters', 'Sediment Input Events'),
            ('physics_and_geometry', 'Physical Constants and Geometry'),
            ('profile_and_output', 'Profile Analysis and Output'),
            ('cliff_edge_processing', 'Cliff Edge Processing Parameters'),
        ]
        
        # Build the ordered configuration
        ordered_config = {}
        for section_key, section_name in sections:
            if section_key in self.config:
                ordered_config[section_key] = self.config[section_key]
        
        # Write to file with custom formatting
        with open(yaml_file_path, 'w') as f:
            f.write(yaml_content)
            
            for section_key, section_name in sections:
                if section_key in ordered_config:
                    f.write(f"\n# {section_name}\n")
                    section_yaml = yaml.dump(
                        {section_key: ordered_config[section_key]}, 
                        default_flow_style=False, 
                        indent=2,
                        sort_keys=False
                    )
                    f.write(section_yaml)


def main():
    """Main function to handle command line arguments and run conversion"""
    if len(sys.argv) < 2:
        print("Usage: python dat_to_yaml_converter.py input.dat [output.yaml]")
        print("  input.dat  - Path to the input .dat file")
        print("  output.yaml - Optional output YAML file path")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Determine output file name
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Create output filename by replacing .dat extension with .yaml
        input_path = Path(input_file)
        output_file = input_path.with_suffix('.yaml')
    
    print(f"Converting '{input_file}' to '{output_file}'...")
    
    try:
        # Create converter and process files
        converter = DatToYamlConverter()
        converter.parse_dat_file(input_file)
        converter.write_yaml_file(output_file)
        
        print(f"✅ Conversion completed successfully!")
        print(f"   Output written to: {output_file}")
        print(f"\nTo use the YAML file with CoastalME:")
        print(f"   ./cme --yaml --datafile={output_file}")
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()