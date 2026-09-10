from tools.schema import TOOLS


def test_tools_schema_shape():
    assert len(TOOLS) == 3
    names = [t["function"]["name"] for t in TOOLS]
    assert names == ["run_command", "write_file", "read_file"]
    for tool in TOOLS:
        assert tool["type"] == "function"
        fn = tool["function"]
        assert "description" in fn
        assert fn["parameters"]["type"] == "object"
        assert "properties" in fn["parameters"]
        assert "required" in fn["parameters"]
