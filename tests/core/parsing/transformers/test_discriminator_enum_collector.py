"""Unit tests for DiscriminatorEnumCollector class."""

import pytest

from pyopenapi_gen import IRDiscriminator, IRSchema
from pyopenapi_gen.core.parsing.transformers.discriminator_enum_collector import (
    DiscriminatorEnumCollector,
)


class TestDiscriminatorEnumCollectorInit:
    """Test DiscriminatorEnumCollector initialisation."""

    def test_init__with_schemas__stores_schemas(self) -> None:
        """
        Scenario:
            DiscriminatorEnumCollector is initialised with a schema dictionary.

        Expected Outcome:
            The schemas should be stored as an instance attribute.
        """
        # Arrange
        schemas = {"TestSchema": IRSchema(name="TestSchema", type="object")}

        # Act
        collector = DiscriminatorEnumCollector(schemas)

        # Assert
        assert collector.schemas == schemas
        assert collector.unified_enums == {}
        assert collector.variant_enum_skip_list == set()


class TestIsDiscriminatedUnion:
    """Test _is_discriminated_union method."""

    @pytest.fixture
    def collector(self) -> DiscriminatorEnumCollector:
        """Provide a DiscriminatorEnumCollector instance."""
        return DiscriminatorEnumCollector({})

    def test_is_discriminated_union__with_discriminator_and_one_of__returns_true(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Schema has discriminator and oneOf.

        Expected Outcome:
            Returns True.
        """
        # Arrange
        schema = IRSchema(
            name="Node",
            type="object",
            one_of=[
                IRSchema(name="StartNode", type="object"),
                IRSchema(name="EndNode", type="object"),
            ],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Act
        result = collector._is_discriminated_union(schema)

        # Assert
        assert result is True

    def test_is_discriminated_union__with_discriminator_and_any_of__returns_true(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Schema has discriminator and anyOf.

        Expected Outcome:
            Returns True.
        """
        # Arrange
        schema = IRSchema(
            name="Node",
            type="object",
            any_of=[
                IRSchema(name="StartNode", type="object"),
                IRSchema(name="EndNode", type="object"),
            ],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Act
        result = collector._is_discriminated_union(schema)

        # Assert
        assert result is True

    def test_is_discriminated_union__without_discriminator__returns_false(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Schema has oneOf but no discriminator.

        Expected Outcome:
            Returns False.
        """
        # Arrange
        schema = IRSchema(
            name="Node",
            type="object",
            one_of=[
                IRSchema(name="StartNode", type="object"),
                IRSchema(name="EndNode", type="object"),
            ],
        )

        # Act
        result = collector._is_discriminated_union(schema)

        # Assert
        assert result is False

    def test_is_discriminated_union__without_one_of_or_any_of__returns_false(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Schema has discriminator but no oneOf or anyOf.

        Expected Outcome:
            Returns False.
        """
        # Arrange
        schema = IRSchema(
            name="Node",
            type="object",
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Act
        result = collector._is_discriminated_union(schema)

        # Assert
        assert result is False


class TestCollectUnifiedEnums:
    """Test collect_unified_enums method."""

    def test_collect_unified_enums__simple_two_variant_union__creates_unified_enum(self) -> None:
        """
        Scenario:
            Union with 2 variants, each with single-value discriminator enum.

        Expected Outcome:
            Creates one unified enum with both values.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={
                "type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"]),
                "id": IRSchema(type="string"),
            },
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={
                "type": IRSchema(name="EndNodeTypeEnum", type="string", enum=["end"]),
                "id": IRSchema(type="string"),
            },
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "NodeTypeEnum" in unified_enums

        unified_enum = unified_enums["NodeTypeEnum"]
        assert unified_enum.name == "NodeTypeEnum"
        assert unified_enum.property_name == "type"
        assert unified_enum.union_schema_name == "Node"
        assert len(unified_enum.values) == 2
        assert ("START", "start") in unified_enum.values
        assert ("END", "end") in unified_enum.values
        assert "StartNodeTypeEnum" in unified_enum.variant_enum_names
        assert "EndNodeTypeEnum" in unified_enum.variant_enum_names

    def test_collect_unified_enums__large_union__collects_all_values(self) -> None:
        """
        Scenario:
            Union with 5 variants (simulating workflow nodes scenario).

        Expected Outcome:
            Creates one unified enum with all 5 values.
        """
        # Arrange
        variants = []
        schemas = {}

        variant_configs = [
            ("StartNode", "start"),
            ("EndNode", "end"),
            ("AgentNode", "agent"),
            ("ConditionalNode", "conditional"),
            ("DelayNode", "delay"),
        ]

        for node_name, type_value in variant_configs:
            variant = IRSchema(
                name=node_name,
                type="object",
                properties={
                    "type": IRSchema(name=f"{node_name}TypeEnum", type="string", enum=[type_value]),
                    "id": IRSchema(type="string"),
                },
            )
            variants.append(variant)
            schemas[node_name] = variant

        node_union = IRSchema(
            name="WorkflowNode",
            type="object",
            one_of=variants,
            discriminator=IRDiscriminator(property_name="type"),
        )
        schemas["WorkflowNode"] = node_union

        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "WorkflowNodeTypeEnum" in unified_enums

        unified_enum = unified_enums["WorkflowNodeTypeEnum"]
        assert unified_enum.name == "WorkflowNodeTypeEnum"
        assert len(unified_enum.values) == 5

        # Verify all values present
        value_dict = dict(unified_enum.values)
        assert value_dict["START"] == "start"
        assert value_dict["END"] == "end"
        assert value_dict["AGENT"] == "agent"
        assert value_dict["CONDITIONAL"] == "conditional"
        assert value_dict["DELAY"] == "delay"

    def test_collect_unified_enums__no_discriminated_unions__returns_empty(self) -> None:
        """
        Scenario:
            Schemas contain no discriminated unions.

        Expected Outcome:
            Returns empty dictionary.
        """
        # Arrange
        schemas = {
            "SimpleSchema": IRSchema(name="SimpleSchema", type="object"),
            "StatusEnum": IRSchema(name="StatusEnum", type="string", enum=["active", "inactive"]),
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert unified_enums == {}
        assert collector.variant_enum_skip_list == set()

    def test_collect_unified_enums__mixed_unions__only_processes_discriminated(self) -> None:
        """
        Scenario:
            Mix of discriminated and non-discriminated unions.

        Expected Outcome:
            Only creates unified enums for discriminated unions.
        """
        # Arrange
        # Discriminated union
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"])},
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"type": IRSchema(name="EndNodeTypeEnum", type="string", enum=["end"])},
        )
        discriminated_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Non-discriminated union
        non_discriminated = IRSchema(
            name="Value",
            type="object",
            one_of=[
                IRSchema(type="string"),
                IRSchema(type="integer"),
            ],
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": discriminated_union,
            "Value": non_discriminated,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "NodeTypeEnum" in unified_enums
        assert "ValueTypeEnum" not in unified_enums

    def test_collect_unified_enums__variant_without_discriminator_property__skips_variant(self) -> None:
        """
        Scenario:
            One variant is missing the discriminator property.

        Expected Outcome:
            Only collects values from variants with the property.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"])},
        )
        # End node missing 'type' property
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"id": IRSchema(type="string")},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        unified_enum = unified_enums["NodeTypeEnum"]
        assert len(unified_enum.values) == 1
        assert ("START", "start") in unified_enum.values

    def test_collect_unified_enums__integer_discriminator__handles_correctly(self) -> None:
        """
        Scenario:
            Discriminator property uses integer enum values.

        Expected Outcome:
            Creates unified enum with integer type and correct values.
        """
        # Arrange
        status_active = IRSchema(
            name="ActiveStatus",
            type="object",
            properties={
                "code": IRSchema(name="ActiveStatusCodeEnum", type="integer", enum=[1]),
                "message": IRSchema(type="string"),
            },
        )
        status_inactive = IRSchema(
            name="InactiveStatus",
            type="object",
            properties={
                "code": IRSchema(name="InactiveStatusCodeEnum", type="integer", enum=[0]),
                "message": IRSchema(type="string"),
            },
        )
        status_union = IRSchema(
            name="Status",
            type="object",
            one_of=[status_active, status_inactive],
            discriminator=IRDiscriminator(property_name="code"),
        )

        schemas = {
            "ActiveStatus": status_active,
            "InactiveStatus": status_inactive,
            "Status": status_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "StatusCodeEnum" in unified_enums

        unified_enum = unified_enums["StatusCodeEnum"]
        assert unified_enum.name == "StatusCodeEnum"
        assert len(unified_enum.values) == 2
        # Note: member names are generated from integer values
        value_dict = dict(unified_enum.values)
        assert value_dict["1"] == 1
        assert value_dict["0"] == 0

    def test_collect_unified_enums__updates_variant_property_references(self) -> None:
        """
        Scenario:
            After collection, variant property references should be updated.

        Expected Outcome:
            Property.name and generation_name are set to unified enum name,
            and enum values are cleared.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="StartNodeTypeEnum",
                    type="string",
                    enum=["start"],
                    generation_name="StartNodeType",
                ),
                "id": IRSchema(type="string"),
            },
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="EndNodeTypeEnum",
                    type="string",
                    enum=["end"],
                    generation_name="EndNodeType",
                ),
                "id": IRSchema(type="string"),
            },
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1

        # Verify StartNode property references
        start_type_prop = start_node.properties["type"]
        assert start_type_prop.name == "NodeTypeEnum"
        assert start_type_prop.generation_name == "NodeTypeEnum"
        assert start_type_prop.enum is None

        # Verify EndNode property references
        end_type_prop = end_node.properties["type"]
        assert end_type_prop.name == "NodeTypeEnum"
        assert end_type_prop.generation_name == "NodeTypeEnum"
        assert end_type_prop.enum is None

    def test_collect_unified_enums__removes_old_property_schemas(self) -> None:
        """
        Scenario:
            Old property schemas (e.g., StartNodeType) should be removed from schemas dict.

        Expected Outcome:
            Schemas dict no longer contains variant property schemas,
            and they are added to the skip list.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="StartNodeTypeEnum",
                    type="string",
                    enum=["start"],
                    generation_name="StartNodeType",
                ),
            },
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="EndNodeTypeEnum",
                    type="string",
                    enum=["end"],
                    generation_name="EndNodeType",
                ),
            },
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Add property schemas to schemas dict (simulating what parser does)
        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
            "StartNodeType": IRSchema(name="StartNodeType", type="string", enum=["start"]),
            "EndNodeType": IRSchema(name="EndNodeType", type="string", enum=["end"]),
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1

        # Verify old schemas removed
        assert "StartNodeType" not in schemas
        assert "EndNodeType" not in schemas

        # Verify they're in skip list
        assert "StartNodeType" in collector.variant_enum_skip_list
        assert "EndNodeType" in collector.variant_enum_skip_list

    def test_collect_unified_enums__multiple_discriminated_unions__creates_multiple(self) -> None:
        """
        Scenario:
            Two separate discriminated unions (e.g., Node and Message).

        Expected Outcome:
            Creates two unified enums (NodeTypeEnum, MessageTypeEnum).
        """
        # Arrange
        # First union: Node
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"])},
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"type": IRSchema(name="EndNodeTypeEnum", type="string", enum=["end"])},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Second union: Message
        text_message = IRSchema(
            name="TextMessage",
            type="object",
            properties={"kind": IRSchema(name="TextMessageKindEnum", type="string", enum=["text"])},
        )
        image_message = IRSchema(
            name="ImageMessage",
            type="object",
            properties={"kind": IRSchema(name="ImageMessageKindEnum", type="string", enum=["image"])},
        )
        message_union = IRSchema(
            name="Message",
            type="object",
            one_of=[text_message, image_message],
            discriminator=IRDiscriminator(property_name="kind"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
            "TextMessage": text_message,
            "ImageMessage": image_message,
            "Message": message_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 2
        assert "NodeTypeEnum" in unified_enums
        assert "MessageKindEnum" in unified_enums

        # Verify Node enum
        node_enum = unified_enums["NodeTypeEnum"]
        assert node_enum.union_schema_name == "Node"
        assert len(node_enum.values) == 2

        # Verify Message enum
        message_enum = unified_enums["MessageKindEnum"]
        assert message_enum.union_schema_name == "Message"
        assert len(message_enum.values) == 2

    def test_collect_unified_enums__property_without_enum_values__skips_variant(self) -> None:
        """
        Scenario:
            Discriminator property exists but has no enum values.

        Expected Outcome:
            Variant is skipped, only variants with enum values are collected.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"])},
        )
        # End node has type property but no enum values
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"type": IRSchema(name="EndNodeType", type="string")},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        unified_enum = unified_enums["NodeTypeEnum"]
        # Only START value collected (END has no enum)
        assert len(unified_enum.values) == 1
        assert ("START", "start") in unified_enum.values

    def test_collect_unified_enums__duplicate_discriminator_values__includes_all(self) -> None:
        """
        Scenario:
            Multiple variants have same discriminator value (unusual but valid).

        Expected Outcome:
            All tuples included, even if values are duplicates.
        """
        # Arrange
        start_node_a = IRSchema(
            name="StartNodeA",
            type="object",
            properties={"type": IRSchema(name="StartNodeATypeEnum", type="string", enum=["start"])},
        )
        start_node_b = IRSchema(
            name="StartNodeB",
            type="object",
            properties={"type": IRSchema(name="StartNodeBTypeEnum", type="string", enum=["start"])},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node_a, start_node_b],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNodeA": start_node_a,
            "StartNodeB": start_node_b,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        unified_enum = unified_enums["NodeTypeEnum"]
        # Both START tuples included (duplicate values)
        assert len(unified_enum.values) == 2
        # Both have same member name and value
        assert unified_enum.values[0] == ("START", "start")
        assert unified_enum.values[1] == ("START", "start")


class TestIdentifyDiscriminatorProperties:
    """Test identify_discriminator_properties method."""

    def test_identify_discriminator_properties__simple_union__returns_all_variants(self) -> None:
        """
        Scenario:
            Union with 2 variants, each with discriminator property.

        Expected Outcome:
            Returns set with (variant_name, property_name) tuples for both variants.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(name="StartNodeTypeEnum", type="string", enum=["start"])},
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"type": IRSchema(name="EndNodeTypeEnum", type="string", enum=["end"])},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        discriminator_properties = collector.identify_discriminator_properties()

        # Assert
        assert len(discriminator_properties) == 2
        assert ("StartNode", "type") in discriminator_properties
        assert ("EndNode", "type") in discriminator_properties

    def test_identify_discriminator_properties__multiple_unions__returns_all(self) -> None:
        """
        Scenario:
            Multiple discriminated unions with different property names.

        Expected Outcome:
            Returns tuples for all variants from all unions.
        """
        # Arrange
        # First union with 'type' discriminator
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(type="string", enum=["start"])},
        )
        end_node = IRSchema(
            name="EndNode",
            type="object",
            properties={"type": IRSchema(type="string", enum=["end"])},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, end_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        # Second union with 'kind' discriminator
        text_msg = IRSchema(
            name="TextMessage",
            type="object",
            properties={"kind": IRSchema(type="string", enum=["text"])},
        )
        message_union = IRSchema(
            name="Message",
            type="object",
            one_of=[text_msg],
            discriminator=IRDiscriminator(property_name="kind"),
        )

        schemas = {
            "StartNode": start_node,
            "EndNode": end_node,
            "Node": node_union,
            "TextMessage": text_msg,
            "Message": message_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        discriminator_properties = collector.identify_discriminator_properties()

        # Assert
        assert len(discriminator_properties) == 3
        assert ("StartNode", "type") in discriminator_properties
        assert ("EndNode", "type") in discriminator_properties
        assert ("TextMessage", "kind") in discriminator_properties

    def test_identify_discriminator_properties__no_discriminated_unions__returns_empty(self) -> None:
        """
        Scenario:
            Schemas contain no discriminated unions.

        Expected Outcome:
            Returns empty set.
        """
        # Arrange
        schemas = {
            "SimpleSchema": IRSchema(name="SimpleSchema", type="object"),
            "StatusEnum": IRSchema(name="StatusEnum", type="string", enum=["active", "inactive"]),
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        discriminator_properties = collector.identify_discriminator_properties()

        # Assert
        assert len(discriminator_properties) == 0

    def test_identify_discriminator_properties__variant_without_name__skips_variant(self) -> None:
        """
        Scenario:
            One variant schema has no name attribute.

        Expected Outcome:
            Only includes variants with valid names.
        """
        # Arrange
        start_node = IRSchema(
            name="StartNode",
            type="object",
            properties={"type": IRSchema(type="string", enum=["start"])},
        )
        # Variant without name
        unnamed_node = IRSchema(
            type="object",
            properties={"type": IRSchema(type="string", enum=["unnamed"])},
        )
        node_union = IRSchema(
            name="Node",
            type="object",
            one_of=[start_node, unnamed_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "StartNode": start_node,
            "Node": node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        discriminator_properties = collector.identify_discriminator_properties()

        # Assert
        assert len(discriminator_properties) == 1
        assert ("StartNode", "type") in discriminator_properties


class TestShouldSkipEnum:
    """Test should_skip_enum method."""

    def test_should_skip_enum__variant_enum__returns_true(self) -> None:
        """
        Scenario:
            Enum name is in variant_enum_skip_list.

        Expected Outcome:
            Returns True.
        """
        # Arrange
        schemas = {}
        collector = DiscriminatorEnumCollector(schemas)
        collector.variant_enum_skip_list = {"StartNodeTypeEnum", "EndNodeTypeEnum"}

        # Act
        result = collector.should_skip_enum("StartNodeTypeEnum")

        # Assert
        assert result is True

    def test_should_skip_enum__regular_enum__returns_false(self) -> None:
        """
        Scenario:
            Enum name is NOT in variant_enum_skip_list.

        Expected Outcome:
            Returns False.
        """
        # Arrange
        schemas = {}
        collector = DiscriminatorEnumCollector(schemas)
        collector.variant_enum_skip_list = {"StartNodeTypeEnum"}

        # Act
        result = collector.should_skip_enum("StatusEnum")

        # Assert
        assert result is False


class TestGenerateUnifiedEnumName:
    """Test _generate_unified_enum_name method."""

    @pytest.fixture
    def collector(self) -> DiscriminatorEnumCollector:
        """Provide a DiscriminatorEnumCollector instance."""
        return DiscriminatorEnumCollector({})

    def test_generate_unified_enum_name__node_union__correct_pattern(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Union name "Node", property name "type".

        Expected Outcome:
            Returns "NodeTypeEnum".
        """
        # Arrange
        union_name = "Node"
        property_name = "type"

        # Act
        result = collector._generate_unified_enum_name(union_name, property_name)

        # Assert
        assert result == "NodeTypeEnum"

    def test_generate_unified_enum_name__workflow_node_union__correct_pattern(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Union name "WorkflowNode", property name "type".

        Expected Outcome:
            Returns "WorkflowNodeTypeEnum".
        """
        # Arrange
        union_name = "WorkflowNode"
        property_name = "type"

        # Act
        result = collector._generate_unified_enum_name(union_name, property_name)

        # Assert
        assert result == "WorkflowNodeTypeEnum"

    def test_generate_unified_enum_name__union_already_has_enum_suffix__removes_duplicate(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Union name already ends with "Enum".

        Expected Outcome:
            Removes "Enum" suffix to avoid "EnumEnum" duplication.
        """
        # Arrange
        union_name = "NodeEnum"
        property_name = "type"

        # Act
        result = collector._generate_unified_enum_name(union_name, property_name)

        # Assert
        assert result == "NodeTypeEnum"
        assert "EnumEnum" not in result

    def test_generate_unified_enum_name__property_with_underscore__handles_correctly(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Property name contains underscore.

        Expected Outcome:
            Capitalises and sanitises correctly following PascalCase.
        """
        # Arrange
        union_name = "Node"
        property_name = "node_type"

        # Act
        result = collector._generate_unified_enum_name(union_name, property_name)

        # Assert
        assert result == "NodeNodeTypeEnum"  # NameSanitizer converts to PascalCase


class TestGenerateMemberName:
    """Test _generate_member_name method."""

    @pytest.fixture
    def collector(self) -> DiscriminatorEnumCollector:
        """Provide a DiscriminatorEnumCollector instance."""
        return DiscriminatorEnumCollector({})

    def test_generate_member_name__simple_string__returns_uppercase(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Simple string value "start".

        Expected Outcome:
            Returns "START".
        """
        # Arrange
        value = "start"

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "START"

    def test_generate_member_name__string_with_hyphens__replaces_with_underscores(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            String value with hyphens "sheet-parser".

        Expected Outcome:
            Returns "SHEET_PARSER".
        """
        # Arrange
        value = "sheet-parser"

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "SHEET_PARSER"

    def test_generate_member_name__string_with_spaces__replaces_with_underscores(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            String value with spaces "query dataset".

        Expected Outcome:
            Returns "QUERY_DATASET".
        """
        # Arrange
        value = "query dataset"

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "QUERY_DATASET"

    def test_generate_member_name__string_with_dots__replaces_with_underscores(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            String value with dots "api.v1.endpoint".

        Expected Outcome:
            Returns "API.V1.ENDPOINT" (dots preserved, uppercased).
        """
        # Arrange
        value = "api.v1.endpoint"

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "API.V1.ENDPOINT"

    def test_generate_member_name__mixed_special_characters__handles_conversion(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            String value with mixed special characters "http-request handler".

        Expected Outcome:
            Returns uppercase with hyphens and spaces converted to underscores.
        """
        # Arrange
        value = "http-request handler"

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "HTTP_REQUEST_HANDLER"

    def test_generate_member_name__numeric_value__converts_to_string(
        self, collector: DiscriminatorEnumCollector
    ) -> None:
        """
        Scenario:
            Numeric value 42.

        Expected Outcome:
            Returns "42" as string.
        """
        # Arrange
        value = 42

        # Act
        result = collector._generate_member_name(value)

        # Assert
        assert result == "42"

    def test_collect_unified_enums__property_references_enum_schema__resolves_enum_values(self) -> None:
        """
        Scenario:
            Discriminator property is a reference to an enum schema via _refers_to_schema
            instead of having inline enum values. This simulates the real-world case where
            a discriminator property uses $ref to reference a separate enum schema like:
                WorkflowConnectorNode.type -> $ref: '#/components/schemas/ConnectorToolConfigTypeEnum'

        Expected Outcome:
            The collector should follow the _refers_to_schema link and collect enum values
            from the referenced schema, including them in the unified enum.
        """
        # Arrange: Create separate enum schemas
        connector_enum = IRSchema(name="ConnectorToolConfigTypeEnum", type="string", enum=["connector"])
        agent_enum = IRSchema(name="AgentToolConfigTypeEnum", type="string", enum=["agent"])

        # Create variant nodes with properties that reference the enum schemas
        # (not inline enums, but references via _refers_to_schema)
        connector_node = IRSchema(
            name="WorkflowConnectorNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="ConnectorToolConfigTypeEnum",
                    type="string",
                    # Note: enum is None because this is a reference
                    enum=None,
                    # _refers_to_schema points to the actual enum
                    _refers_to_schema=connector_enum,
                )
            },
        )
        agent_node = IRSchema(
            name="WorkflowAgentNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="AgentToolConfigTypeEnum",
                    type="string",
                    enum=None,
                    _refers_to_schema=agent_enum,
                )
            },
        )

        # Create discriminated union
        workflow_node_union = IRSchema(
            name="WorkflowNode",
            type="object",
            one_of=[connector_node, agent_node],
            discriminator=IRDiscriminator(property_name="type"),
        )

        schemas = {
            "ConnectorToolConfigTypeEnum": connector_enum,
            "AgentToolConfigTypeEnum": agent_enum,
            "WorkflowConnectorNode": connector_node,
            "WorkflowAgentNode": agent_node,
            "WorkflowNode": workflow_node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "WorkflowNodeTypeEnum" in unified_enums

        unified_enum = unified_enums["WorkflowNodeTypeEnum"]
        assert unified_enum.union_schema_name == "WorkflowNode"
        assert unified_enum.property_name == "type"

        # Verify all discriminator values are collected (from referenced enums)
        assert len(unified_enum.values) == 2
        value_dict = dict(unified_enum.values)
        assert "CONNECTOR" in value_dict
        assert value_dict["CONNECTOR"] == "connector"
        assert "AGENT" in value_dict
        assert value_dict["AGENT"] == "agent"

        # Verify variant enum names are tracked for skipping
        assert "ConnectorToolConfigTypeEnum" in unified_enum.variant_enum_names
        assert "AgentToolConfigTypeEnum" in unified_enum.variant_enum_names

    def test_collect_unified_enums__uses_discriminator_mapping_fallback__when_property_enum_unified(self) -> None:
        """
        Scenario:
            Multiple discriminated unions share the same discriminator value (e.g., "connector").
            When the first union's discriminator properties get unified, the second union's
            variants lose access to the original enum values. The collector should use the
            discriminator mapping as a fallback to get the discriminator value.

            Real-world example:
            - ToolConfig union has ConnectorToolConfig.type = "connector"
            - WorkflowNode union has WorkflowConnectorNode.type = "connector"
            - After ToolConfig is processed, ConnectorToolConfig.type references ToolConfigTypeEnum
            - When processing WorkflowNode, WorkflowConnectorNode.type has no enum values
            - The collector should use the discriminator mapping to get "connector"

        Expected Outcome:
            The collector uses the discriminator mapping to resolve the discriminator value
            when the property's enum has been unified by another union.
        """
        # Arrange: Simulate the state after ToolConfig union has been processed
        # WorkflowConnectorNode.type now references a unified enum that doesn't exist yet
        connector_node = IRSchema(
            name="WorkflowConnectorNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="ToolConfigTypeEnum",  # This was updated by ToolConfig union processing
                    type="string",
                    enum=None,  # Enum values were cleared
                    _refers_to_schema=None,  # No reference available
                )
            },
        )
        start_node = IRSchema(
            name="WorkflowStartNode",
            type="object",
            properties={
                "type": IRSchema(
                    name="WorkflowStartNodeTypeEnum",
                    type="string",
                    enum=["start"],
                )
            },
        )

        # Create discriminated union with mapping
        workflow_node_union = IRSchema(
            name="WorkflowNode",
            type="object",
            one_of=[connector_node, start_node],
            discriminator=IRDiscriminator(
                property_name="type",
                mapping={
                    "connector": "#/components/schemas/WorkflowConnectorNode",
                    "start": "#/components/schemas/WorkflowStartNode",
                },
            ),
        )

        schemas = {
            "WorkflowConnectorNode": connector_node,
            "WorkflowStartNode": start_node,
            "WorkflowNode": workflow_node_union,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert
        assert len(unified_enums) == 1
        assert "WorkflowNodeTypeEnum" in unified_enums

        unified_enum = unified_enums["WorkflowNodeTypeEnum"]
        assert len(unified_enum.values) == 2

        # Verify "connector" was resolved from the discriminator mapping
        value_dict = dict(unified_enum.values)
        assert "CONNECTOR" in value_dict
        assert value_dict["CONNECTOR"] == "connector"
        assert "START" in value_dict
        assert value_dict["START"] == "start"

    def test_collect_unified_enums__shared_ref_enum__does_not_corrupt_unrelated_references(self) -> None:
        """
        Regression test for shared IRSchema reference corruption.

        Scenario:
            An enum IRSchema object is referenced by both a discriminator variant's
            property AND an unrelated schema's property (simulating $ref resolution
            returning the same Python object). When the collector creates a unified
            enum, it must NOT corrupt the unrelated reference.

        Expected Outcome:
            The unrelated schema's property still points to the original enum,
            whilst the variant's property is replaced with a new reference to
            the unified enum.
        """
        # Arrange: Create a SHARED enum IRSchema (same object, simulating $ref reuse)
        shared_enum = IRSchema(
            name="GoogleAuthVariantMethodEnum",
            type="string",
            enum=["google"],
            generation_name="GoogleAuthVariantMethodEnum",
            final_module_stem="google_auth_variant_method_enum",
        )

        # Both variant and unrelated schema reference the SAME object
        auth_variant = IRSchema(
            name="GoogleAuthVariant",
            type="object",
            properties={
                "method": shared_enum,  # Same object
            },
        )
        unrelated_schema = IRSchema(
            name="GoogleTenantCredentialMetadata",
            type="object",
            properties={
                "provider": shared_enum,  # Same object — would be corrupted before fix
            },
        )

        # Another variant for the union
        mobile_enum = IRSchema(
            name="MobileAuthRequestMethodEnum",
            type="string",
            enum=["mobile"],
            generation_name="MobileAuthRequestMethodEnum",
            final_module_stem="mobile_auth_request_method_enum",
        )
        mobile_auth = IRSchema(
            name="MobileAuthRequest",
            type="object",
            properties={
                "method": mobile_enum,
            },
        )

        # Discriminated union
        auth_union = IRSchema(
            name="AuthMethod",
            type="object",
            one_of=[auth_variant, mobile_auth],
            discriminator=IRDiscriminator(property_name="method"),
        )

        schemas = {
            "GoogleAuthVariantMethodEnum": shared_enum,
            "MobileAuthRequestMethodEnum": mobile_enum,
            "GoogleAuthVariant": auth_variant,
            "MobileAuthRequest": mobile_auth,
            "AuthMethod": auth_union,
            "GoogleTenantCredentialMetadata": unrelated_schema,
        }
        collector = DiscriminatorEnumCollector(schemas)

        # Act
        unified_enums = collector.collect_unified_enums()

        # Assert: Unified enum was created
        assert len(unified_enums) == 1
        assert "AuthMethodMethodEnum" in unified_enums

        # Assert: Variant property was REPLACED with new reference to unified enum
        variant_prop = auth_variant.properties["method"]
        assert variant_prop.generation_name == "AuthMethodMethodEnum"
        assert variant_prop is not shared_enum  # Must be a NEW object

        # Assert: Unrelated schema's property is UNCHANGED (the critical check)
        unrelated_prop = unrelated_schema.properties["provider"]
        assert unrelated_prop is shared_enum  # Must still be the SAME original object
        assert unrelated_prop.name == "GoogleAuthVariantMethodEnum"
        assert unrelated_prop.generation_name == "GoogleAuthVariantMethodEnum"
        assert unrelated_prop.final_module_stem == "google_auth_variant_method_enum"
        assert unrelated_prop.enum == ["google"]
