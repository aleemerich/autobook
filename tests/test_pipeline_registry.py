import dataclasses
import pytest
from unittest.mock import patch, MagicMock

from pipelines.registry import list_pipelines, get_pipeline_spec, get_pipeline, PipelineSpec
from pipelines.base import Pipeline

def test_list_pipelines_contains_four_pipelines():
    pipelines = list_pipelines()
    assert len(pipelines) == 4
    assert "ideation" in pipelines
    assert "foundation" in pipelines
    assert "book_generation" in pipelines
    assert "editorial_revision" in pipelines

def test_pipeline_specs_have_correct_metadata():
    # Test ideation spec
    spec_ideation = get_pipeline_spec("ideation")
    assert spec_ideation.name == "ideation"
    assert spec_ideation.supports_chapter is False
    assert spec_ideation.supports_from_scratch is True
    assert spec_ideation.requires_work_branch is True
    assert callable(spec_ideation.factory)

    # Test book_generation spec
    spec_gen = get_pipeline_spec("book_generation")
    assert spec_gen.name == "book_generation"
    assert spec_gen.supports_chapter is True
    assert spec_gen.supports_from_scratch is True
    assert spec_gen.requires_work_branch is True
    assert callable(spec_gen.factory)

    # Test all registered pipelines have requires_work_branch=True
    for name, spec in list_pipelines().items():
        assert spec.requires_work_branch is True

def test_get_pipeline_instantiates_correct_class():
    pipeline = get_pipeline("ideation")
    assert isinstance(pipeline, Pipeline)

def test_invalid_pipeline_raises_key_error():
    with pytest.raises(KeyError) as excinfo:
        get_pipeline_spec("invalid_name")
    assert "Pipeline desconhecida" in str(excinfo.value)

    with pytest.raises(KeyError) as excinfo:
        get_pipeline("invalid_name")
    assert "Pipeline desconhecida" in str(excinfo.value)

def test_list_pipelines_does_not_instantiate_or_run():
    pipelines = list_pipelines()
    for name, spec in pipelines.items():
        assert isinstance(spec, PipelineSpec)

def test_pipeline_spec_is_frozen():
    """Valida que PipelineSpec continua frozen."""
    spec = get_pipeline_spec("ideation")
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.requires_work_branch = False  # type: ignore

def test_run_py_accepts_valid_pipeline():
    import run
    
    with patch("run.get_pipeline_spec") as mock_get_spec:
        mock_spec = MagicMock()
        mock_spec.requires_work_branch = False
        mock_get_spec.return_value = mock_spec
        
        # Test running with --pipeline ideation
        with patch("sys.argv", ["run.py", "--pipeline", "ideation"]):
            run.main()
            
        mock_get_spec.assert_called_once_with("ideation")
        mock_spec.factory.return_value.run.assert_called_once()
