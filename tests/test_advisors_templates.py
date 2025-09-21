# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OTHER DEALINGS IN THE
# SOFTWARE.

"""
Comprehensive tests for advisors templates module.

Tests template management, rendering, validation, and persistence.
"""

import json

import pytest

from src.chatty_commander.advisors.templates import (
    Template,
    TemplateCategory,
    TemplateManager,
    TemplateMetadata,
    TemplateRenderer,
    TemplateValidator,
)


class TestTemplateCategory:
    """Test TemplateCategory enum."""

    def test_template_category_values(self):
        """Test TemplateCategory enum values."""
        assert TemplateCategory.PROMPT.value == "prompt"
        assert TemplateCategory.RESPONSE.value == "response"
        assert TemplateCategory.SYSTEM.value == "system"
        assert TemplateCategory.USER.value == "user"
        assert TemplateCategory.CUSTOM.value == "custom"

    def test_template_category_from_string(self):
        """Test creating TemplateCategory from string."""
        assert TemplateCategory.from_string("prompt") == TemplateCategory.PROMPT
        assert TemplateCategory.from_string("response") == TemplateCategory.RESPONSE
        assert TemplateCategory.from_string("system") == TemplateCategory.SYSTEM
        assert TemplateCategory.from_string("custom") == TemplateCategory.CUSTOM

    def test_template_category_from_string_invalid(self):
        """Test TemplateCategory.from_string with invalid input."""
        assert (
            TemplateCategory.from_string("invalid") == TemplateCategory.CUSTOM
        )  # Default
        assert TemplateCategory.from_string("") == TemplateCategory.CUSTOM  # Default
        assert TemplateCategory.from_string(None) == TemplateCategory.CUSTOM  # Default


class TestTemplateMetadata:
    """Test TemplateMetadata class."""

    def test_template_metadata_creation(self):
        """Test creating a TemplateMetadata instance."""
        metadata = TemplateMetadata(
            name="test_template",
            description="A test template",
            version="1.0.0",
            author="Test Author",
            category=TemplateCategory.PROMPT,
            tags=["test", "example"],
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-02T00:00:00Z",
            dependencies=["jinja2", "markupsafe"],
            compatibility=["python>=3.8"],
            license="MIT",
        )

        assert metadata.name == "test_template"
        assert metadata.description == "A test template"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.category == TemplateCategory.PROMPT
        assert metadata.tags == ["test", "example"]
        assert metadata.dependencies == ["jinja2", "markupsafe"]
        assert metadata.compatibility == ["python>=3.8"]
        assert metadata.license == "MIT"

    def test_template_metadata_defaults(self):
        """Test TemplateMetadata with default values."""
        metadata = TemplateMetadata(name="simple_template")

        assert metadata.name == "simple_template"
        assert metadata.description == ""
        assert metadata.version == "1.0.0"
        assert metadata.author == "Unknown"
        assert metadata.category == TemplateCategory.CUSTOM
        assert metadata.tags == []
        assert metadata.dependencies == []
        assert metadata.compatibility == []
        assert metadata.license == "Unknown"

    def test_template_metadata_to_dict(self):
        """Test converting TemplateMetadata to dictionary."""
        metadata = TemplateMetadata(
            name="test_template",
            description="Test template",
            version="2.0.0",
            category=TemplateCategory.SYSTEM,
            tags=["test", "system"],
        )

        metadata_dict = metadata.to_dict()

        assert metadata_dict["name"] == "test_template"
        assert metadata_dict["description"] == "Test template"
        assert metadata_dict["version"] == "2.0.0"
        assert metadata_dict["category"] == "system"
        assert metadata_dict["tags"] == ["test", "system"]

    def test_template_metadata_from_dict(self):
        """Test creating TemplateMetadata from dictionary."""
        metadata_dict = {
            "name": "dict_template",
            "description": "Template from dict",
            "version": "1.5.0",
            "author": "Dict Author",
            "category": "prompt",
            "tags": ["dict", "test"],
            "dependencies": ["requests"],
            "compatibility": ["python>=3.9"],
            "license": "Apache-2.0",
        }

        metadata = TemplateMetadata.from_dict(metadata_dict)

        assert metadata.name == "dict_template"
        assert metadata.description == "Template from dict"
        assert metadata.version == "1.5.0"
        assert metadata.author == "Dict Author"
        assert metadata.category == TemplateCategory.PROMPT
        assert metadata.tags == ["dict", "test"]
        assert metadata.dependencies == ["requests"]
        assert metadata.compatibility == ["python>=3.9"]
        assert metadata.license == "Apache-2.0"


class TestTemplate:
    """Test Template class."""

    def test_template_creation(self):
        """Test creating a Template instance."""
        template = Template(
            template_id="test_template_001",
            content="Hello {{name}}, welcome to {{place}}!",
            variables=["name", "place"],
            metadata=TemplateMetadata(
                name="greeting_template",
                description="A greeting template",
                category=TemplateCategory.PROMPT,
            ),
        )

        assert template.template_id == "test_template_001"
        assert template.content == "Hello {{name}}, welcome to {{place}}!"
        assert template.variables == ["name", "place"]
        assert template.metadata.name == "greeting_template"

    def test_template_render(self):
        """Test rendering a template."""
        template = Template(
            template_id="render_test",
            content="Hello {{name}}, you have {{count}} messages.",
            variables=["name", "count"],
        )

        rendered = template.render({"name": "Alice", "count": "5"})

        assert rendered == "Hello Alice, you have 5 messages."

    def test_template_render_missing_variables(self):
        """Test rendering template with missing variables."""
        template = Template(
            template_id="missing_vars",
            content="Hello {{name}}, you are {{age}} years old.",
            variables=["name", "age"],
        )

        rendered = template.render({"name": "Bob"})

        assert "Hello Bob, you are " in rendered
        assert "years old." in rendered

    def test_template_render_extra_variables(self):
        """Test rendering template with extra variables."""
        template = Template(
            template_id="extra_vars", content="Hello {{name}}!", variables=["name"]
        )

        rendered = template.render(
            {"name": "Charlie", "extra": "ignored", "another": "also_ignored"}
        )

        assert rendered == "Hello Charlie!"

    def test_template_validation(self):
        """Test template validation."""
        # Valid template
        valid_template = Template(
            template_id="valid_template", content="Hello {{name}}!", variables=["name"]
        )
        assert valid_template.validate() is True

        # Invalid template (no variables defined)
        invalid_template = Template(
            template_id="invalid_template",
            content="Hello {{name}}!",
            variables=[],  # Missing 'name' variable
        )
        assert invalid_template.validate() is False

    def test_template_get_required_variables(self):
        """Test getting required variables from template."""
        template = Template(
            template_id="variable_test",
            content="User: {{user_name}}, Age: {{user_age}}, City: {{user_city}}",
            variables=["user_name", "user_age", "user_city"],
        )

        required_vars = template.get_required_variables()

        assert "user_name" in required_vars
        assert "user_age" in required_vars
        assert "user_city" in required_vars
        assert len(required_vars) == 3

    def test_template_to_dict(self):
        """Test converting Template to dictionary."""
        template = Template(
            template_id="dict_test",
            content="Test content: {{value}}",
            variables=["value"],
            metadata=TemplateMetadata(
                name="test_template", description="Test template", version="1.0.0"
            ),
        )

        template_dict = template.to_dict()

        assert template_dict["template_id"] == "dict_test"
        assert template_dict["content"] == "Test content: {{value}}"
        assert template_dict["variables"] == ["value"]
        assert template_dict["metadata"]["name"] == "test_template"

    def test_template_from_dict(self):
        """Test creating Template from dictionary."""
        template_dict = {
            "template_id": "from_dict_test",
            "content": "Hello {{person}} from {{location}}!",
            "variables": ["person", "location"],
            "metadata": {
                "name": "dict_template",
                "description": "Template from dictionary",
                "version": "2.0.0",
                "category": "prompt",
            },
        }

        template = Template.from_dict(template_dict)

        assert template.template_id == "from_dict_test"
        assert template.content == "Hello {{person}} from {{location}}!"
        assert template.variables == ["person", "location"]
        assert template.metadata.name == "dict_template"
        assert template.metadata.category == TemplateCategory.PROMPT


class TestTemplateValidator:
    """Test TemplateValidator class."""

    def test_template_validator_creation(self):
        """Test creating a TemplateValidator instance."""
        validator = TemplateValidator()

        assert validator.supported_syntax == ["jinja2", "string.Template"]
        assert validator.max_template_size == 100000  # 100KB default

    def test_validate_jinja2_template(self):
        """Test validating Jinja2 template."""
        validator = TemplateValidator()

        # Valid Jinja2 template
        valid_jinja2 = "Hello {{name}}, welcome to {{place}}!"
        assert validator.validate_template(valid_jinja2, "jinja2") is True

        # Invalid Jinja2 template
        invalid_jinja2 = "Hello {{name, welcome to {{place}}!"  # Malformed
        assert validator.validate_template(invalid_jinja2, "jinja2") is False

    def test_validate_string_template(self):
        """Test validating string.Template."""
        validator = TemplateValidator()

        # Valid string template
        valid_string = "Hello $name, welcome to $place!"
        assert validator.validate_template(valid_string, "string.Template") is True

        # Invalid string template
        invalid_string = "Hello $name, welcome to $place!"  # Missing closing brace
        assert validator.validate_template(invalid_string, "string.Template") is False

    def test_validate_template_size(self):
        """Test template size validation."""
        validator = TemplateValidator()

        # Create large template
        large_template = "x" * 150000  # 150KB
        assert validator.validate_template_size(large_template) is False

        # Create normal size template
        normal_template = "Hello {{name}}!"
        assert validator.validate_template_size(normal_template) is True

    def test_detect_template_syntax(self):
        """Test detecting template syntax."""
        validator = TemplateValidator()

        # Jinja2 syntax
        jinja2_template = "Hello {{name}}, you have {{count}} items."
        assert validator.detect_template_syntax(jinja2_template) == "jinja2"

        # String template syntax
        string_template = "Hello $name, you have $count items."
        assert validator.detect_template_syntax(string_template) == "string.Template"

        # Plain text
        plain_text = "Hello name, you have count items."
        assert validator.detect_template_syntax(plain_text) == "plain"

    def test_extract_variables_jinja2(self):
        """Test extracting variables from Jinja2 template."""
        validator = TemplateValidator()

        template = (
            "Hello {{user_name}}, you are {{user_age}} years old from {{user_city}}."
        )
        variables = validator.extract_variables(template, "jinja2")

        assert "user_name" in variables
        assert "user_age" in variables
        assert "user_city" in variables
        assert len(variables) == 3

    def test_extract_variables_string_template(self):
        """Test extracting variables from string.Template."""
        validator = TemplateValidator()

        template = "Hello $user_name, you are $user_age years old from $user_city."
        variables = validator.extract_variables(template, "string.Template")

        assert "user_name" in variables
        assert "user_age" in variables
        assert "user_city" in variables
        assert len(variables) == 3

    def test_validate_template_security(self):
        """Test template security validation."""
        validator = TemplateValidator()

        # Safe template
        safe_template = "Hello {{name}}, welcome!"
        assert validator.validate_template_security(safe_template) is True

        # Potentially unsafe template (file operations)
        unsafe_template = "File content: {{file('/etc/passwd').read()}}"
        assert validator.validate_template_security(unsafe_template) is False

        # Another unsafe pattern
        unsafe_template2 = "{{os.system('rm -rf /')}}"
        assert validator.validate_template_security(unsafe_template2) is False


class TestTemplateRenderer:
    """Test TemplateRenderer class."""

    @pytest.fixture
    def sample_templates(self):
        """Create sample templates for testing."""
        return [
            Template(
                template_id="greeting",
                content="Hello {{name}}, welcome to {{place}}!",
                variables=["name", "place"],
            ),
            Template(
                template_id="info",
                content="User: {{user}}\nEmail: {{email}}\nAge: {{age}}",
                variables=["user", "email", "age"],
            ),
        ]

    def test_template_renderer_initialization(self, sample_templates):
        """Test TemplateRenderer initialization."""
        renderer = TemplateRenderer(templates=sample_templates)

        assert len(renderer.templates) == 2
        assert "greeting" in renderer.templates
        assert "info" in renderer.templates

    def test_render_single_template(self, sample_templates):
        """Test rendering a single template."""
        renderer = TemplateRenderer(templates=sample_templates)

        result = renderer.render_template(
            "greeting", {"name": "Alice", "place": "Wonderland"}
        )

        assert result == "Hello Alice, welcome to Wonderland!"

    def test_render_template_not_found(self, sample_templates):
        """Test rendering non-existent template."""
        renderer = TemplateRenderer(templates=sample_templates)

        result = renderer.render_template("nonexistent", {})

        assert result == ""

    def test_render_template_missing_variables(self, sample_templates):
        """Test rendering template with missing variables."""
        renderer = TemplateRenderer(templates=sample_templates)

        result = renderer.render_template("greeting", {"name": "Bob"})

        assert "Hello Bob, welcome to" in result

    def test_render_batch_templates(self, sample_templates):
        """Test rendering multiple templates in batch."""
        renderer = TemplateRenderer(templates=sample_templates)

        requests = [
            {
                "template_id": "greeting",
                "variables": {"name": "Alice", "place": "Wonderland"},
            },
            {
                "template_id": "info",
                "variables": {"user": "Bob", "email": "bob@example.com", "age": "25"},
            },
        ]

        results = renderer.render_batch(requests)

        assert len(results) == 2
        assert "Hello Alice, welcome to Wonderland!" in results[0]
        assert "User: Bob" in results[1]
        assert "bob@example.com" in results[1]
        assert "Age: 25" in results[1]

    def test_add_template(self, sample_templates):
        """Test adding template to renderer."""
        renderer = TemplateRenderer(templates=sample_templates)

        new_template = Template(
            template_id="farewell", content="Goodbye {{name}}!", variables=["name"]
        )

        renderer.add_template(new_template)

        assert "farewell" in renderer.templates
        assert len(renderer.templates) == 3

    def test_remove_template(self, sample_templates):
        """Test removing template from renderer."""
        renderer = TemplateRenderer(templates=sample_templates)

        renderer.remove_template("greeting")

        assert "greeting" not in renderer.templates
        assert len(renderer.templates) == 1

    def test_list_templates(self, sample_templates):
        """Test listing all templates."""
        renderer = TemplateRenderer(templates=sample_templates)

        template_list = renderer.list_templates()

        assert len(template_list) == 2
        assert "greeting" in template_list
        assert "info" in template_list

    def test_get_template(self, sample_templates):
        """Test getting individual template."""
        renderer = TemplateRenderer(templates=sample_templates)

        template = renderer.get_template("greeting")

        assert template is not None
        assert template.template_id == "greeting"
        assert template.content == "Hello {{name}}, welcome to {{place}}!"

    def test_render_with_custom_delimiters(self, sample_templates):
        """Test rendering with custom template delimiters."""
        # Create template with custom delimiters
        custom_template = Template(
            template_id="custom",
            content="Hello [name], welcome to [place]!",
            variables=["name", "place"],
            metadata=TemplateMetadata(name="custom_template"),
        )

        renderer = TemplateRenderer(templates=[custom_template])

        result = renderer.render_template(
            "custom", {"name": "Custom", "place": "World"}, delimiters=("[", "]")
        )

        assert result == "Hello Custom, welcome to World!"

    def test_render_with_filters(self, sample_templates):
        """Test rendering with Jinja2 filters."""
        template = Template(
            template_id="filter_test",
            content="Name: {{name|upper}}, Items: {{items|length}}",
            variables=["name", "items"],
        )

        renderer = TemplateRenderer(templates=[template])

        result = renderer.render_template(
            "filter_test", {"name": "alice", "items": [1, 2, 3]}
        )

        assert result == "Name: ALICE, Items: 3"


class TestTemplateManager:
    """Comprehensive tests for TemplateManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            "template_directories": ["/app/templates", "/user/templates"],
            "enable_caching": True,
            "cache_size_limit": 100,
            "default_category": "prompt",
            "enable_validation": True,
            "auto_reload": True,
        }

    @pytest.fixture
    def sample_templates(self):
        """Create sample templates for testing."""
        return [
            Template(
                template_id="greeting_v1",
                content="Hello {{name}}!",
                variables=["name"],
                metadata=TemplateMetadata(
                    name="greeting", version="1.0.0", category=TemplateCategory.PROMPT
                ),
            ),
            Template(
                template_id="info_v1",
                content="User: {{user}}\nStatus: {{status}}",
                variables=["user", "status"],
                metadata=TemplateMetadata(
                    name="user_info",
                    version="1.0.0",
                    category=TemplateCategory.RESPONSE,
                ),
            ),
        ]

    def test_template_manager_initialization(self, mock_config, sample_templates):
        """Test TemplateManager initialization."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        assert manager.config == mock_config
        assert len(manager.templates) == 2
        assert manager.cache == {}

    def test_register_template(self, mock_config, sample_templates):
        """Test registering new template."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        new_template = Template(
            template_id="farewell_v1",
            content="Goodbye {{name}}!",
            variables=["name"],
            metadata=TemplateMetadata(
                name="farewell", version="1.0.0", category=TemplateCategory.PROMPT
            ),
        )

        result = manager.register_template(new_template)

        assert result is True
        assert "farewell_v1" in manager.templates
        assert len(manager.templates) == 3

    def test_register_duplicate_template(self, mock_config, sample_templates):
        """Test registering duplicate template."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Try to register template with existing ID
        duplicate_template = Template(
            template_id="greeting_v1",  # Same ID
            content="Hi {{name}}!",
            variables=["name"],
        )

        result = manager.register_template(duplicate_template)

        assert result is False  # Should fail

    def test_unregister_template(self, mock_config, sample_templates):
        """Test unregistering template."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        result = manager.unregister_template("greeting_v1")

        assert result is True
        assert "greeting_v1" not in manager.templates
        assert len(manager.templates) == 1

    def test_get_template_by_id(self, mock_config, sample_templates):
        """Test getting template by ID."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        template = manager.get_template("greeting_v1")

        assert template is not None
        assert template.template_id == "greeting_v1"
        assert template.content == "Hello {{name}}!"

    def test_get_template_by_name(self, mock_config, sample_templates):
        """Test getting template by name."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        template = manager.get_template_by_name("greeting")

        assert template is not None
        assert template.metadata.name == "greeting"

    def test_list_templates_by_category(self, mock_config, sample_templates):
        """Test listing templates by category."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        prompt_templates = manager.list_templates(category=TemplateCategory.PROMPT)
        response_templates = manager.list_templates(category=TemplateCategory.RESPONSE)

        assert len(prompt_templates) == 1
        assert len(response_templates) == 1
        assert prompt_templates[0].metadata.category == TemplateCategory.PROMPT
        assert response_templates[0].metadata.category == TemplateCategory.RESPONSE

    def test_search_templates(self, mock_config, sample_templates):
        """Test searching templates."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Add another template for searching
        search_template = Template(
            template_id="search_test",
            content="Search result: {{query}}",
            variables=["query"],
            metadata=TemplateMetadata(
                name="search_template",
                description="Template for search queries",
                tags=["search", "query"],
            ),
        )
        manager.register_template(search_template)

        # Search by name
        results = manager.search_templates("greeting")
        assert len(results) == 1
        assert results[0].metadata.name == "greeting"

        # Search by tag
        results = manager.search_templates("search")
        assert len(results) == 1
        assert results[0].metadata.name == "search_template"

        # Search by description
        results = manager.search_templates("query")
        assert len(results) == 1
        assert results[0].metadata.name == "search_template"

    def test_render_template(self, mock_config, sample_templates):
        """Test rendering template through manager."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        result = manager.render_template("greeting_v1", {"name": "World"})

        assert result == "Hello World!"
        assert "greeting_v1" in manager.cache

    def test_render_template_with_caching(self, mock_config, sample_templates):
        """Test template rendering with caching."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Render same template twice
        result1 = manager.render_template("greeting_v1", {"name": "Alice"})
        result2 = manager.render_template("greeting_v1", {"name": "Alice"})

        assert result1 == result2
        assert len(manager.cache) == 1

    def test_clear_cache(self, mock_config, sample_templates):
        """Test clearing template cache."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Render some templates
        manager.render_template("greeting_v1", {"name": "Test1"})
        manager.render_template("info_v1", {"user": "Test2", "status": "active"})

        assert len(manager.cache) == 2

        # Clear cache
        manager.clear_cache()

        assert len(manager.cache) == 0

    def test_get_template_statistics(self, mock_config, sample_templates):
        """Test getting template statistics."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Use templates
        manager.render_template("greeting_v1", {"name": "User1"})
        manager.render_template("info_v1", {"user": "User2", "status": "active"})
        manager.render_template("greeting_v1", {"name": "User3"})  # Same template again

        stats = manager.get_statistics()

        assert "total_templates" in stats
        assert "cache_size" in stats
        assert "render_count" in stats
        assert "category_distribution" in stats
        assert stats["total_templates"] == 2
        assert stats["cache_size"] == 2
        assert stats["render_count"] == 3
        assert stats["category_distribution"]["prompt"] == 1
        assert stats["category_distribution"]["response"] == 1

    def test_save_template_to_file(self, mock_config, sample_templates, tmp_path):
        """Test saving template to file."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        template_file = tmp_path / "test_template.json"
        result = manager.save_template_to_file("greeting_v1", str(template_file))

        assert result is True
        assert template_file.exists()

        # Verify content
        with open(template_file) as f:
            saved_template = json.load(f)

        assert saved_template["template_id"] == "greeting_v1"
        assert saved_template["content"] == "Hello {{name}}!"
        assert saved_template["metadata"]["name"] == "greeting"

    def test_load_template_from_file(self, mock_config, sample_templates, tmp_path):
        """Test loading template from file."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Create template file
        template_data = {
            "template_id": "loaded_template",
            "content": "Loaded content: {{value}}",
            "variables": ["value"],
            "metadata": {
                "name": "loaded_template",
                "description": "Template loaded from file",
                "version": "1.0.0",
                "category": "custom",
            },
        }

        template_file = tmp_path / "loaded_template.json"
        with open(template_file, "w") as f:
            json.dump(template_data, f)

        # Load template
        result = manager.load_template_from_file(str(template_file))

        assert result is True
        assert "loaded_template" in manager.templates

        # Verify loaded template
        loaded_template = manager.get_template("loaded_template")
        assert loaded_template.content == "Loaded content: {{value}}"
        assert loaded_template.metadata.description == "Template loaded from file"

    def test_load_templates_from_directory(
        self, mock_config, sample_templates, tmp_path
    ):
        """Test loading templates from directory."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Create temporary template directory
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create multiple template files
        template_files = [
            {
                "template_id": "dir_template_1",
                "content": "Template 1: {{var1}}",
                "variables": ["var1"],
                "metadata": {"name": "template1", "category": "prompt"},
            },
            {
                "template_id": "dir_template_2",
                "content": "Template 2: {{var2}}",
                "variables": ["var2"],
                "metadata": {"name": "template2", "category": "response"},
            },
        ]

        for i, template_data in enumerate(template_files):
            template_file = template_dir / f"template_{i+1}.json"
            with open(template_file, "w") as f:
                json.dump(template_data, f)

        # Load templates from directory
        result = manager.load_templates_from_directory(str(template_dir))

        assert result is True
        assert "dir_template_1" in manager.templates
        assert "dir_template_2" in manager.templates
        assert len(manager.templates) == 4  # Original 2 + new 2

    def test_export_all_templates(self, mock_config, sample_templates, tmp_path):
        """Test exporting all templates."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        export_dir = tmp_path / "export"
        export_dir.mkdir()

        result = manager.export_all_templates(str(export_dir))

        assert result is True
        assert len(list(export_dir.glob("*.json"))) == 2

    def test_validate_all_templates(self, mock_config, sample_templates):
        """Test validating all templates."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # All templates should be valid
        validation_results = manager.validate_all_templates()

        assert len(validation_results) == 2
        assert all(result["valid"] for result in validation_results.values())

    def test_create_template_from_string(self, mock_config, sample_templates):
        """Test creating template from string."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        template_string = "New template: {{message}}"
        template_id = "new_template"

        result = manager.create_template_from_string(
            template_id=template_id,
            content=template_string,
            variables=["message"],
            name="New Template",
            category=TemplateCategory.CUSTOM,
        )

        assert result is True
        assert template_id in manager.templates

        # Test rendering the new template
        rendered = manager.render_template(template_id, {"message": "Hello"})
        assert rendered == "New template: Hello"

    def test_update_template(self, mock_config, sample_templates):
        """Test updating existing template."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Update existing template
        result = manager.update_template(
            "greeting_v1", content="Hi {{name}}, welcome!", variables=["name"]
        )

        assert result is True

        # Verify update
        updated_template = manager.get_template("greeting_v1")
        assert updated_template.content == "Hi {{name}}, welcome!"

    def test_template_versioning(self, mock_config, sample_templates):
        """Test template versioning functionality."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Update template with new version
        result = manager.update_template(
            "greeting_v1", content="Hi {{name}}!", version="2.0.0"
        )

        assert result is True

        # Get template info
        template = manager.get_template("greeting_v1")
        assert template.metadata.version == "2.0.0"

    def test_batch_template_operations(self, mock_config, sample_templates):
        """Test batch template operations."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Batch render
        requests = [
            {"template_id": "greeting_v1", "variables": {"name": "Alice"}},
            {
                "template_id": "info_v1",
                "variables": {"user": "Bob", "status": "active"},
            },
        ]

        results = manager.batch_render(requests)

        assert len(results) == 2
        assert "Hello Alice!" in results[0]
        assert "User: Bob" in results[1]

    def test_error_handling_invalid_operations(self, mock_config, sample_templates):
        """Test error handling for invalid operations."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Try to get non-existent template
        template = manager.get_template("nonexistent")
        assert template is None

        # Try to render non-existent template
        result = manager.render_template("nonexistent", {})
        assert result == ""

        # Try to register invalid template
        invalid_template = Template(
            template_id="",
            content="Invalid",
            variables=[],  # Invalid ID
        )

        result = manager.register_template(invalid_template)
        assert result is False  # Should fail gracefully

    def test_performance_monitoring(self, mock_config, sample_templates):
        """Test performance monitoring for template operations."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        # Perform several operations
        for i in range(10):
            manager.render_template("greeting_v1", {"name": f"User{i}"})

        # Get performance metrics
        metrics = manager.get_performance_metrics()

        assert "average_render_time" in metrics
        assert "total_renders" in metrics
        assert "cache_hit_rate" in metrics
        assert "templates_per_second" in metrics
        assert metrics["total_renders"] == 10

    def test_template_backup_and_restore(self, mock_config, sample_templates, tmp_path):
        """Test template backup and restore functionality."""
        manager = TemplateManager(mock_config, templates=sample_templates)

        backup_file = tmp_path / "template_backup.json"

        # Create backup
        backup_result = manager.backup_templates(str(backup_file))

        assert backup_result is True
        assert backup_file.exists()

        # Modify templates
        manager.update_template("greeting_v1", content="Modified greeting")

        # Restore from backup
        restore_result = manager.restore_templates(str(backup_file))

        assert restore_result is True

        # Verify restoration
        original_template = manager.get_template("greeting_v1")
        assert original_template.content == "Hello {{name}}!"  # Back to original
