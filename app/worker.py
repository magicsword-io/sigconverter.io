#!/usr/bin/env python3
import sys
import json
import importlib

try:
    import yaml
except ImportError as e:
    print("Error: PyYAML not installed", file=sys.stderr)
    sys.exit(1)

try:
    from sigma.conversion.base import Backend
    from sigma.collection import SigmaCollection
    from sigma.plugins import InstalledSigmaPlugins
    from sigma.exceptions import SigmaError
    from sigma.processing.pipeline import ProcessingPipeline
except ImportError as e:
    print("Error: sigma-cli not installed correctly", file=sys.stderr)
    sys.exit(1)

def get_available_backends():
    """Get list of available backends"""
    try:
        plugins = InstalledSigmaPlugins.autodiscover()
        backends = {}
        
        for backend_id, backend_class in plugins.backends.items():
            formats = []
            if hasattr(backend_class, 'formats'):
                formats = list(backend_class.formats.keys())
            
            # Get pipelines
            pipelines = []
            pipeline_resolver = plugins.get_pipeline_resolver()
            available_pipelines = pipeline_resolver.list_pipelines()
            for name, pipeline in available_pipelines:
                if (not pipeline.allowed_backends) or (backend_id in pipeline.allowed_backends):
                    pipelines.append(name)
            
            backends[backend_id] = {
                'name': backend_id,
                'formats': formats,
                'pipelines': pipelines
            }
        
        return backends
    except Exception as e:
        return {}

def main():
    try:
        if len(sys.argv) < 2:
            print("Error: No endpoint specified", file=sys.stderr)
            sys.exit(1)

        endpoint = sys.argv[1]
        
        plugins = InstalledSigmaPlugins.autodiscover()
        pipeline_resolver = plugins.get_pipeline_resolver()
        
        if endpoint == "targets":
            backends = get_available_backends()
            print(json.dumps({"targets": list(backends.keys())}))
            
        elif endpoint == "formats":
            if len(sys.argv) < 3:
                print("Error: No backend specified", file=sys.stderr)
                sys.exit(1)
                
            backend_id = sys.argv[2]
            backends = get_available_backends()
            
            if backend_id in backends:
                print(json.dumps({"formats": backends[backend_id]['formats']}))
            else:
                print(f"Error: Unknown backend {backend_id}", file=sys.stderr)
                sys.exit(1)
                
        elif endpoint == "pipelines":
            if len(sys.argv) < 3:
                print("Error: No backend specified", file=sys.stderr)
                sys.exit(1)
                
            backend_id = sys.argv[2]
            backends = get_available_backends()
            
            if backend_id in backends:
                print(json.dumps({"pipelines": backends[backend_id]['pipelines']}))
            else:
                print(f"Error: Unknown backend {backend_id}", file=sys.stderr)
                sys.exit(1)
                
        elif endpoint == "convert":
            if len(sys.argv) < 4:
                print("Error: Missing arguments for conversion", file=sys.stderr)
                sys.exit(1)
                
            backend_id = sys.argv[2]
            rule_yaml = sys.argv[3]
            format_id = sys.argv[4] if len(sys.argv) > 4 else None
            pipeline_ids = sys.argv[5].split(',') if len(sys.argv) > 5 else None
            
            # Print arguments for debugging
            print(f"Converting with backend: {backend_id}", file=sys.stderr)
            print(f"Rule YAML: {rule_yaml}", file=sys.stderr)
            print(f"Format: {format_id}", file=sys.stderr)
            print(f"Pipelines: {pipeline_ids}", file=sys.stderr)
            
            # Parse YAML
            try:
                rule_dict = yaml.safe_load(rule_yaml)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {e}", file=sys.stderr)
                sys.exit(1)
            
            # Convert rule
            try:
                if isinstance(rule_dict, list):
                    sigma_rule = SigmaCollection.from_yaml(rule_yaml)
                else:
                    sigma_rule = SigmaCollection.from_yaml(rule_yaml)
                
                backend_class = plugins.backends[backend_id]
                processing_pipeline = None
                if pipeline_ids:
                    processing_pipeline = pipeline_resolver.resolve(pipeline_ids)
                
                backend = backend_class(processing_pipeline=processing_pipeline)
                result = backend.convert(sigma_rule, format_id)
                
                if isinstance(result, list):
                    result = result[0]
                    
                print(json.dumps({"queries": result}))
                
            except SigmaError as e:
                print(f"Error during conversion: {str(e)}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error during conversion: {str(e)}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: Unknown endpoint {endpoint}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 