from pyopenapi_gen.core.utils import TemplateRenderer


def test_sanitize_module_name_filter():
    renderer = TemplateRenderer()
    # Jinja2 filter for module name sanitization
    template = "{{ 'My-API Client!' | sanitize_module_name }}"
    output = renderer.render(template)
    assert output == "my_api_client"


def test_sanitize_class_name_filter():
    renderer = TemplateRenderer()
    # Jinja2 filter for class name sanitization
    template = "{{ '123 example_name' | sanitize_class_name }}"
    output = renderer.render(template)
    assert output == "_123ExampleName"


def test_render_path_filter():
    renderer = TemplateRenderer()
    # Use the render_path filter to substitute path params
    template = "{{ '/users/{userId}/items/{itemId}' | render_path }}"
    # Jinja2 alone can't pass dict to filter without a variable; use direct call via global
    output = renderer.render(
        "{{ render_path('/users/{userId}/items/{itemId}', {'userId': 42, 'itemId': 'abc'}) }}"
    )
    assert output == "/users/42/items/abc"


def test_kwargsbuilder_global():
    renderer = TemplateRenderer()
    # KwargsBuilder is available as a global; build params and json
    tpl = (
        "{% set kb = KwargsBuilder().with_params(a=1,b=None).with_json({'x': 2}) %}"
        "{{ kb.build() }}"
    )
    output = renderer.render(tpl)
    # The resulting dict string should include both params and json
    assert '"params": {"a": 1}' in output or "'params': {'a': 1}" in output
    assert '"json": {"x": 2}' in output or "'json': {'x': 2}" in output
