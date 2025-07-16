# generator/ - Main Orchestration

## Why This Folder?
High-level orchestration of the entire code generation pipeline. Coordinates loader → parser → visitors → emitters → post-processing flow.

## Key Dependencies
- **Input**: CLI arguments, OpenAPI spec path
- **Output**: Complete generated client package
- **Orchestrates**: All other system components
- **Error Handling**: `GenerationError` for CLI reporting

## Essential Architecture

### 1. Generation Pipeline
```python
# client_generator.py
def generate(self, spec_path: str, project_root: Path, output_package: str, 
             force: bool = False, no_postprocess: bool = False, 
             core_package: str = None) -> None:
    
    # 1. Load OpenAPI spec
    spec = self.load_spec(spec_path)
    
    # 2. Parse to IR
    ir_spec = self.parse_to_ir(spec)
    
    # 3. Generate code
    self.generate_code(ir_spec, project_root, output_package, core_package)
    
    # 4. Post-process (format, typecheck)
    if not no_postprocess:
        self.post_process(project_root, output_package)
```

### 2. Diff Checking
```python
def generate_with_diff_check(self, ...) -> None:
    if not force and self.output_exists():
        # Generate to temporary location
        temp_output = self.create_temp_output()
        self.generate_to_path(temp_output)
        
        # Compare with existing
        if self.has_changes(temp_output, self.final_output):
            self.prompt_user_for_confirmation()
        
        # Move temp to final location
        self.move_temp_to_final(temp_output, self.final_output)
```

## Critical Components

### client_generator.py
**Purpose**: Main entry point for all generation operations
```python
class ClientGenerator:
    def __init__(self):
        self.loader = SpecLoader()
        self.parser = SpecParser()
        self.type_service = None  # Created per generation
        self.visitors = self.create_visitors()
        self.emitters = self.create_emitters()
        self.post_processor = PostProcessManager()
    
    def generate(self, spec_path: str, project_root: Path, output_package: str, 
                 force: bool = False, no_postprocess: bool = False, 
                 core_package: str = None) -> None:
        """Main generation method called by CLI"""
        try:
            self.validate_inputs(spec_path, project_root, output_package)
            self.run_generation_pipeline(...)
        except Exception as e:
            raise GenerationError(f"Generation failed: {e}")
```

### Generation Workflow
```python
def run_generation_pipeline(self, spec_path: str, project_root: Path, 
                           output_package: str, core_package: str) -> None:
    
    # 1. Load and validate OpenAPI spec
    raw_spec = self.loader.load(spec_path)
    
    # 2. Parse to intermediate representation
    ir_spec = self.parser.parse(raw_spec)
    
    # 3. Create context for generation
    context = RenderContext(project_root, output_package)
    
    # 4. Initialize type service
    self.type_service = UnifiedTypeService(ir_spec.schemas, ir_spec.responses)
    
    # 5. Generate code using visitors
    self.generate_models(ir_spec.schemas, context)
    self.generate_endpoints(ir_spec.operations, context)
    self.generate_client(ir_spec, context)
    self.generate_exceptions(ir_spec.responses, context)
    
    # 6. Emit files using emitters
    self.emit_all_files(ir_spec, context, core_package)
    
    # 7. Post-process (format, typecheck)
    self.post_process_if_enabled(project_root, output_package)
```

## Error Handling Strategy

### 1. Structured Error Hierarchy
```python
class GenerationError(Exception):
    """Top-level error for CLI reporting"""
    pass

class ValidationError(GenerationError):
    """Input validation failures"""
    pass

class ParsingError(GenerationError):
    """OpenAPI parsing failures"""
    pass

class CodeGenerationError(GenerationError):
    """Code generation failures"""
    pass
```

### 2. Error Context Collection
```python
def handle_generation_error(self, error: Exception, context: Dict[str, Any]) -> None:
    """Add context to errors for better debugging"""
    error_context = {
        "spec_path": context.get("spec_path"),
        "output_package": context.get("output_package"),
        "current_stage": context.get("current_stage"),
        "current_schema": context.get("current_schema")
    }
    
    detailed_message = f"Generation failed at {error_context['current_stage']}: {error}"
    if error_context.get("current_schema"):
        detailed_message += f" (processing schema: {error_context['current_schema']})"
    
    raise GenerationError(detailed_message) from error
```

## Visitor Coordination

### 1. Visitor Initialization
```python
def create_visitors(self) -> Dict[str, Visitor]:
    """Create all visitors with proper dependencies"""
    return {
        "model": ModelVisitor(self.type_service),
        "endpoint": EndpointVisitor(self.type_service),
        "client": ClientVisitor(self.type_service),
        "exception": ExceptionVisitor(self.type_service),
        "docs": DocsVisitor()
    }
```

### 2. Visitor Execution
```python
def generate_models(self, schemas: Dict[str, IRSchema], context: RenderContext) -> None:
    """Generate model code using visitor"""
    model_codes = {}
    
    for schema_name, schema in schemas.items():
        try:
            # Generate code for single schema
            code = self.visitors["model"].visit_schema(schema, context)
            model_codes[schema_name] = code
            
        except Exception as e:
            # Add schema context to error
            context_info = {"current_schema": schema_name, "current_stage": "model_generation"}
            self.handle_generation_error(e, context_info)
    
    # Store for emitters
    self.generated_models = model_codes
```

## Emitter Coordination

### 1. Emitter Initialization
```python
def create_emitters(self, output_path: Path) -> Dict[str, Emitter]:
    """Create all emitters with proper configuration"""
    file_manager = FileManager(output_path)
    
    return {
        "models": ModelsEmitter(output_path, file_manager),
        "endpoints": EndpointsEmitter(output_path, file_manager),
        "client": ClientEmitter(output_path, file_manager),
        "core": CoreEmitter(output_path, file_manager),
        "exceptions": ExceptionsEmitter(output_path, file_manager)
    }
```

### 2. Emitter Execution
```python
def emit_all_files(self, ir_spec: IRSpec, context: RenderContext, core_package: str) -> None:
    """Emit all generated code to files"""
    
    # Emit in dependency order
    self.emitters["core"].emit_core(context.output_package, core_package)
    self.emitters["models"].emit_models(ir_spec.schemas, context)
    self.emitters["endpoints"].emit_endpoints(ir_spec.operations, context)
    self.emitters["exceptions"].emit_exceptions(ir_spec.responses, context)
    self.emitters["client"].emit_client(ir_spec, context)
```

## Post-Processing

### 1. Format and Typecheck
```python
def post_process(self, project_root: Path, output_package: str) -> None:
    """Run Black formatting and mypy type checking"""
    
    package_path = self.resolve_package_path(project_root, output_package)
    
    # Format with Black
    self.run_black_formatting(package_path)
    
    # Type check with mypy
    self.run_mypy_checking(package_path)
```

### 2. Validation
```python
def validate_generated_code(self, package_path: Path) -> None:
    """Validate generated code can be imported"""
    
    # Try to import generated client
    try:
        spec = importlib.util.spec_from_file_location("client", package_path / "client.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        raise GenerationError(f"Generated code validation failed: {e}")
```

## Dependencies on Other Systems

### From core/
- Uses `SpecLoader` for OpenAPI loading
- Uses `SpecParser` for IR creation
- Uses `PostProcessManager` for formatting

### From types/
- Creates `UnifiedTypeService` for visitors
- Coordinates type resolution across generation

### From visit/
- Orchestrates all visitors
- Manages visitor dependencies

### From emitters/
- Coordinates all emitters
- Manages file output

## Testing Requirements

### Integration Tests
```python
def test_client_generator__complete_generation__creates_working_client():
    # Test full generation pipeline
    generator = ClientGenerator()
    
    # Generate client
    generator.generate(
        spec_path="test_spec.yaml",
        project_root=temp_dir,
        output_package="test_client"
    )
    
    # Verify client works
    assert can_import_client(temp_dir / "test_client")
    assert client_methods_work(temp_dir / "test_client")
```

### Error Handling Tests
```python
def test_client_generator__invalid_spec__raises_generation_error():
    generator = ClientGenerator()
    
    with pytest.raises(GenerationError) as exc_info:
        generator.generate(
            spec_path="invalid_spec.yaml",
            project_root=temp_dir,
            output_package="test_client"
        )
    
    assert "parsing failed" in str(exc_info.value)
```

## Extension Points

### Custom Generation Steps
```python
class CustomClientGenerator(ClientGenerator):
    def run_generation_pipeline(self, *args, **kwargs):
        # Add custom pre-processing
        self.custom_pre_process()
        
        # Run standard pipeline
        super().run_generation_pipeline(*args, **kwargs)
        
        # Add custom post-processing
        self.custom_post_process()
```

### Plugin System
```python
def register_plugin(self, plugin: GenerationPlugin) -> None:
    """Register custom generation plugin"""
    self.plugins.append(plugin)
    
def run_plugins(self, stage: str, context: Dict[str, Any]) -> None:
    """Run plugins at specific generation stage"""
    for plugin in self.plugins:
        if plugin.handles_stage(stage):
            plugin.execute(context)
```

## Critical Implementation Details

### Resource Management
```python
def generate_safely(self, *args, **kwargs) -> None:
    """Generate with proper resource cleanup"""
    temp_files = []
    
    try:
        # Generation logic
        pass
    except Exception:
        # Clean up temporary files
        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()
        raise
```

### Progress Reporting
```python
def generate_with_progress(self, *args, **kwargs) -> None:
    """Generate with progress reporting"""
    stages = ["loading", "parsing", "code_generation", "file_emission", "post_processing"]
    
    for i, stage in enumerate(stages):
        print(f"[{i+1}/{len(stages)}] {stage.replace('_', ' ').title()}...")
        self.run_stage(stage)
```