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

"""
Comprehensive tests for advisors prompting module.

Tests prompt generation, template handling, and context-aware prompting.
"""


import pytest

from src.chatty_commander.advisors.prompting import (
    PromptBuilder,
    PromptManager,
    PromptTemplate,
)


class TestPromptTemplate:
    """Test PromptTemplate class."""

    def test_prompt_template_creation(self):
        """Test creating a PromptTemplate instance."""
        template = PromptTemplate(
            name="test_template",
            template_string="Hello {{name}}, welcome to {{place}}!",
            variables=["name", "place"],
            description="A simple greeting template",
        )

        assert template.name == "test_template"
        assert template.template_string == "Hello {{name}}, welcome to {{place}}!"
        assert template.variables == ["name", "place"]
        assert template.description == "A simple greeting template"

    def test_prompt_template_render(self):
        """Test rendering a prompt template."""
        template = PromptTemplate(
            name="greeting", template_string="Hello {{name}}!", variables=["name"]
        )

        rendered = template.render({"name": "World"})

        assert rendered == "Hello World!"

    def test_prompt_template_render_missing_variables(self):
        """Test rendering template with missing variables."""
        template = PromptTemplate(
            name="greeting",
            template_string="Hello {{name}} from {{place}}!",
            variables=["name", "place"],
        )

        rendered = template.render({"name": "World"})

        # Should render with missing variables as empty
        assert "Hello World from !!" in rendered

    def test_prompt_template_render_extra_variables(self):
        """Test rendering template with extra variables."""
        template = PromptTemplate(
            name="greeting", template_string="Hello {{name}}!", variables=["name"]
        )

        rendered = template.render({"name": "World", "extra": "ignored"})

        assert rendered == "Hello World!"

    def test_prompt_template_validation(self):
        """Test prompt template validation."""
        # Valid template
        valid_template = PromptTemplate(
            name="valid", template_string="Hello {{name}}!", variables=["name"]
        )
        assert valid_template.validate() is True

        # Invalid template (missing variable)
        invalid_template = PromptTemplate(
            name="invalid",
            template_string="Hello {{name}}!",
            variables=["name", "missing_var"],  # Missing missing_var
        )
        assert invalid_template.validate() is False

    def test_prompt_template_to_dict(self):
        """Test converting PromptTemplate to dictionary."""
        template = PromptTemplate(
            name="test",
            template_string="Hello {{name}}!",
            variables=["name"],
            description="Test template",
        )

        template_dict = template.to_dict()

        assert template_dict["name"] == "test"
        assert template_dict["template_string"] == "Hello {{name}}!"
        assert template_dict["variables"] == ["name"]
        assert template_dict["description"] == "Test template"

    def test_prompt_template_from_dict(self):
        """Test creating PromptTemplate from dictionary."""
        template_dict = {
            "name": "test",
            "template_string": "Hello {{name}}!",
            "variables": ["name"],
            "description": "Test template",
        }

        template = PromptTemplate.from_dict(template_dict)

        assert template.name == "test"
        assert template.template_string == "Hello {{name}}!"
        assert template.variables == ["name"]
        assert template.description == "Test template"


class TestPromptBuilder:
    """Test PromptBuilder class."""

    @pytest.fixture
    def sample_templates(self):
        """Create sample prompt templates."""
        return [
            PromptTemplate(
                name="greeting",
                template_string="Hello {{name}}, welcome to {{place}}!",
                variables=["name", "place"],
            ),
            PromptTemplate(
                name="question",
                template_string="Question: {{question}}\nContext: {{context}}",
                variables=["question", "context"],
            ),
        ]

    def test_prompt_builder_initialization(self, sample_templates):
        """Test PromptBuilder initialization."""
        builder = PromptBuilder(templates=sample_templates)

        assert len(builder.templates) == 2
        assert "greeting" in builder.templates
        assert "question" in builder.templates

    def test_build_prompt_basic(self, sample_templates):
        """Test basic prompt building."""
        builder = PromptBuilder(templates=sample_templates)

        prompt = builder.build_prompt(
            "greeting", {"name": "Alice", "place": "Wonderland"}
        )

        assert prompt == "Hello Alice, welcome to Wonderland!"

    def test_build_prompt_with_missing_template(self, sample_templates):
        """Test building prompt with missing template."""
        builder = PromptBuilder(templates=sample_templates)

        prompt = builder.build_prompt("nonexistent", {})

        assert prompt == ""

    def test_build_prompt_with_context(self, sample_templates):
        """Test building prompt with additional context."""
        builder = PromptBuilder(templates=sample_templates)

        context = {
            "conversation_history": "Previous: Hello\nResponse: Hi",
            "user_preferences": {"language": "en"},
        }

        prompt = builder.build_prompt(
            "question",
            {"question": "How are you?", "context": "Today"},
            context=context,
        )

        assert "Question: How are you?" in prompt
        assert "Context: Today" in prompt
        assert "conversation_history" in prompt

    def test_add_template(self, sample_templates):
        """Test adding template to builder."""
        builder = PromptBuilder(templates=sample_templates)

        new_template = PromptTemplate(
            name="farewell", template_string="Goodbye {{name}}!", variables=["name"]
        )

        builder.add_template(new_template)

        assert "farewell" in builder.templates
        assert len(builder.templates) == 3

    def test_remove_template(self, sample_templates):
        """Test removing template from builder."""
        builder = PromptBuilder(templates=sample_templates)

        builder.remove_template("greeting")

        assert "greeting" not in builder.templates
        assert len(builder.templates) == 1

    def test_get_template(self, sample_templates):
        """Test getting template from builder."""
        builder = PromptBuilder(templates=sample_templates)

        template = builder.get_template("greeting")

        assert template is not None
        assert template.name == "greeting"

    def test_list_templates(self, sample_templates):
        """Test listing all templates."""
        builder = PromptBuilder(templates=sample_templates)

        template_names = builder.list_templates()

        assert "greeting" in template_names
        assert "question" in template_names
        assert len(template_names) == 2

    def test_build_prompt_chain(self, sample_templates):
        """Test building a chain of prompts."""
        builder = PromptBuilder(templates=sample_templates)

        prompts = [
            ("greeting", {"name": "Alice", "place": "Wonderland"}),
            ("question", {"question": "How are you?", "context": "Today"}),
        ]

        chain = builder.build_prompt_chain(prompts)

        assert len(chain) == 2
        assert "Hello Alice, welcome to Wonderland!" in chain[0]
        assert "Question: How are you?" in chain[1]

    def test_template_validation_on_build(self, sample_templates):
        """Test template validation during build."""
        builder = PromptBuilder(templates=sample_templates)

        # Try to build with invalid template name
        with pytest.raises(ValueError):
            builder.build_prompt("invalid_template", {})


class TestPromptManager:
    """Comprehensive tests for PromptManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return {
            "default_templates": ["greeting", "question"],
            "template_directory": "/tmp/templates",
            "enable_caching": True,
            "max_cache_size": 100,
        }

    @pytest.fixture
    def sample_templates(self):
        """Create sample prompt templates."""
        return {
            "greeting": PromptTemplate(
                name="greeting", template_string="Hello {{name}}!", variables=["name"]
            ),
            "question": PromptTemplate(
                name="question",
                template_string="Q: {{question}}",
                variables=["question"],
            ),
        }

    def test_prompt_manager_initialization(self, mock_config, sample_templates):
        """Test PromptManager initialization."""
        manager = PromptManager(mock_config, templates=sample_templates)

        assert manager.config == mock_config
        assert len(manager.templates) == 2
        assert manager.cache == {}

    def test_generate_prompt_basic(self, mock_config, sample_templates):
        """Test basic prompt generation."""
        manager = PromptManager(mock_config, templates=sample_templates)

        prompt = manager.generate_prompt("greeting", {"name": "World"})

        assert prompt == "Hello World!"
        assert "greeting" in manager.cache

    def test_generate_prompt_with_caching(self, mock_config, sample_templates):
        """Test prompt generation with caching."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Generate same prompt twice
        prompt1 = manager.generate_prompt("greeting", {"name": "World"})
        prompt2 = manager.generate_prompt("greeting", {"name": "World"})

        assert prompt1 == prompt2
        assert len(manager.cache) == 1  # Should be cached

    def test_generate_prompt_caching_disabled(self, mock_config, sample_templates):
        """Test prompt generation with caching disabled."""
        disabled_config = mock_config.copy()
        disabled_config["enable_caching"] = False

        manager = PromptManager(disabled_config, templates=sample_templates)

        # Generate same prompt twice
        prompt1 = manager.generate_prompt("greeting", {"name": "World"})
        prompt2 = manager.generate_prompt("greeting", {"name": "World"})

        assert prompt1 == prompt2
        assert len(manager.cache) == 0  # Should not be cached

    def test_generate_prompt_with_context(self, mock_config, sample_templates):
        """Test prompt generation with context."""
        manager = PromptManager(mock_config, templates=sample_templates)

        context = {
            "user_id": "user123",
            "conversation_history": "Previous conversation...",
            "platform": "voice",
        }

        prompt = manager.generate_prompt(
            "question", {"question": "How are you?"}, context=context
        )

        assert "Q: How are you?" in prompt
        assert "user_id" in prompt
        assert "conversation_history" in prompt

    def test_generate_prompt_with_template_not_found(
        self, mock_config, sample_templates
    ):
        """Test prompt generation with missing template."""
        manager = PromptManager(mock_config, templates=sample_templates)

        prompt = manager.generate_prompt("nonexistent", {})

        assert prompt == ""

    def test_register_template(self, mock_config, sample_templates):
        """Test registering new template."""
        manager = PromptManager(mock_config, templates=sample_templates)

        new_template = PromptTemplate(
            name="farewell", template_string="Goodbye {{name}}!", variables=["name"]
        )

        manager.register_template(new_template)

        assert "farewell" in manager.templates
        assert len(manager.templates) == 3

    def test_unregister_template(self, mock_config, sample_templates):
        """Test unregistering template."""
        manager = PromptManager(mock_config, templates=sample_templates)

        manager.unregister_template("greeting")

        assert "greeting" not in manager.templates
        assert len(manager.templates) == 1

    def test_load_templates_from_directory(
        self, mock_config, sample_templates, tmp_path
    ):
        """Test loading templates from directory."""
        # Create temporary template files
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        greeting_file = template_dir / "greeting.json"
        greeting_file.write_text(
            """
        {
            "name": "greeting",
            "template_string": "Hi {{name}}!",
            "variables": ["name"],
            "description": "Custom greeting"
        }
        """
        )

        question_file = template_dir / "question.json"
        question_file.write_text(
            """
        {
            "name": "question",
            "template_string": "Question: {{question}}",
            "variables": ["question"]
        }
        """
        )

        load_config = mock_config.copy()
        load_config["template_directory"] = str(template_dir)

        manager = PromptManager(load_config)

        # Load templates
        manager.load_templates_from_directory()

        assert "greeting" in manager.templates
        assert "question" in manager.templates
        assert len(manager.templates) == 2

    def test_save_template_to_file(self, mock_config, sample_templates, tmp_path):
        """Test saving template to file."""
        manager = PromptManager(mock_config, templates=sample_templates)

        template_file = tmp_path / "test_template.json"
        manager.save_template_to_file("greeting", str(template_file))

        assert template_file.exists()

        # Verify content
        import json

        with open(template_file) as f:
            saved_template = json.load(f)

        assert saved_template["name"] == "greeting"
        assert saved_template["template_string"] == "Hello {{name}}!"
        assert saved_template["variables"] == ["name"]

    def test_get_template_statistics(self, mock_config, sample_templates):
        """Test getting template statistics."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Use templates
        manager.generate_prompt("greeting", {"name": "World"})
        manager.generate_prompt("question", {"question": "Test?"})
        manager.generate_prompt("greeting", {"name": "Alice"})  # Same template again

        stats = manager.get_statistics()

        assert "total_templates" in stats
        assert "cache_size" in stats
        assert "usage_counts" in stats
        assert stats["total_templates"] == 2
        assert stats["cache_size"] == 2  # Two unique prompts cached
        assert stats["usage_counts"]["greeting"] == 2
        assert stats["usage_counts"]["question"] == 1

    def test_clear_cache(self, mock_config, sample_templates):
        """Test clearing prompt cache."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Generate some prompts
        manager.generate_prompt("greeting", {"name": "World"})
        manager.generate_prompt("question", {"question": "Test?"})

        assert len(manager.cache) == 2

        # Clear cache
        manager.clear_cache()

        assert len(manager.cache) == 0

    def test_validate_template_variables(self, mock_config, sample_templates):
        """Test template variable validation."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Valid variables
        is_valid = manager.validate_template_variables("greeting", {"name": "World"})
        assert is_valid is True

        # Missing variables
        is_valid = manager.validate_template_variables("greeting", {})
        assert is_valid is False

        # Extra variables (should be OK)
        is_valid = manager.validate_template_variables(
            "greeting", {"name": "World", "extra": "value"}
        )
        assert is_valid is True

    def test_batch_prompt_generation(self, mock_config, sample_templates):
        """Test batch prompt generation."""
        manager = PromptManager(mock_config, templates=sample_templates)

        requests = [
            {"template": "greeting", "variables": {"name": "Alice"}},
            {"template": "question", "variables": {"question": "How are you?"}},
            {"template": "greeting", "variables": {"name": "Bob"}},
        ]

        prompts = manager.generate_batch_prompts(requests)

        assert len(prompts) == 3
        assert "Hello Alice!" in prompts[0]
        assert "Question: How are you?" in prompts[1]
        assert "Hello Bob!" in prompts[2]

    def test_template_search_functionality(self, mock_config, sample_templates):
        """Test template search functionality."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Add another template for searching
        search_template = PromptTemplate(
            name="search_test",
            template_string="Search for: {{query}}",
            variables=["query"],
            description="Template for search queries",
        )
        manager.register_template(search_template)

        # Search by name
        results = manager.search_templates("search")
        assert len(results) == 1
        assert results[0].name == "search_test"

        # Search by description
        results = manager.search_templates("greeting")
        assert len(results) == 1
        assert results[0].name == "greeting"

    def test_error_handling_invalid_template(self, mock_config, sample_templates):
        """Test error handling for invalid template operations."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Try to generate prompt with invalid template
        prompt = manager.generate_prompt("invalid_template", {})
        assert prompt == ""

        # Try to register invalid template
        invalid_template = PromptTemplate(
            name="",
            template_string="Invalid",
            variables=[],  # Invalid empty name
        )

        # Should handle gracefully
        manager.register_template(invalid_template)

    def test_template_inheritance(self, mock_config, sample_templates):
        """Test template inheritance functionality."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Create a template that inherits from another
        base_template = PromptTemplate(
            name="base_greeting",
            template_string="Greetings {{name}}!",
            variables=["name"],
        )
        manager.register_template(base_template)

        # Create inheriting template
        inheriting_template = PromptTemplate(
            name="formal_greeting",
            template_string="{{base_greeting}} How formal!",
            variables=["name"],
            inherits_from="base_greeting",
        )
        manager.register_template(inheriting_template)

        # Generate prompt using inheriting template
        prompt = manager.generate_prompt("formal_greeting", {"name": "Sir"})

        assert "Greetings Sir!" in prompt
        assert "How formal!" in prompt

    def test_template_versioning(self, mock_config, sample_templates):
        """Test template versioning functionality."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Create template with version
        versioned_template = PromptTemplate(
            name="versioned_greeting",
            template_string="Hello {{name}}! (v1.0)",
            variables=["name"],
            version="1.0",
        )
        manager.register_template(versioned_template)

        # Update template with new version
        updated_template = PromptTemplate(
            name="versioned_greeting",
            template_string="Hi {{name}}! (v2.0)",
            variables=["name"],
            version="2.0",
        )
        manager.register_template(updated_template)

        # Should have both versions
        assert "versioned_greeting" in manager.templates
        assert manager.templates["versioned_greeting"].version == "2.0"

    def test_performance_monitoring(self, mock_config, sample_templates):
        """Test performance monitoring for prompt generation."""
        manager = PromptManager(mock_config, templates=sample_templates)

        # Generate several prompts
        for i in range(10):
            prompt = manager.generate_prompt("greeting", {"name": f"User{i}"})

        # Check performance metrics
        metrics = manager.get_performance_metrics()

        assert "average_generation_time" in metrics
        assert "total_prompts_generated" in metrics
        assert "cache_hit_rate" in metrics
        assert metrics["total_prompts_generated"] == 10
