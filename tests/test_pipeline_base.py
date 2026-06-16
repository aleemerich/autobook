import pytest
from pipelines.base import Step, Pipeline

class MockStep(Step):
    def __init__(self, name, description=None, requires=None, produces=None, should_fail=False):
        super().__init__(name, description, requires, produces)
        self.should_fail = should_fail
        self.executed = False

    def run(self, context):
        self.executed = True
        if self.should_fail:
            raise ValueError(f"Step {self.name} failed")
        context[self.name] = "done"

def test_step_defaults():
    step = Step("x")
    assert step.name == "x"
    assert step.description is None
    assert step.requires == []
    assert step.produces == []

def test_step_with_metadata():
    step = Step("x", description="desc", requires=["a"], produces=["b"])
    assert step.name == "x"
    assert step.description == "desc"
    assert step.requires == ["a"]
    assert step.produces == ["b"]

def test_metadata_lists_are_copied():
    reqs = ["a"]
    prods = ["b"]
    step = Step("x", requires=reqs, produces=prods)
    
    # Mutating original list should not affect step
    reqs.append("c")
    prods.append("d")
    
    assert step.requires == ["a"]
    assert step.produces == ["b"]

def test_steps_do_not_share_default_lists():
    step1 = Step("x")
    step2 = Step("y")
    
    assert step1.requires is not step2.requires
    assert step1.produces is not step2.produces

def test_pipeline_defaults():
    pipeline = Pipeline("p")
    assert pipeline.name == "p"
    assert pipeline.steps == []
    assert pipeline.description is None
    assert pipeline.requires == []
    assert pipeline.produces == []

def test_pipeline_runs_steps_in_order():
    step1 = MockStep("step1")
    step2 = MockStep("step2")
    pipeline = Pipeline("p", steps=[step1, step2])
    
    context = {}
    pipeline.run(context)
    
    assert step1.executed is True
    assert step2.executed is True
    assert context == {"step1": "done", "step2": "done"}

def test_pipeline_with_metadata():
    pipeline = Pipeline(
        name="p",
        description="pipeline-desc",
        requires=["req-a"],
        produces=["prod-b"]
    )
    assert pipeline.name == "p"
    assert pipeline.description == "pipeline-desc"
    assert pipeline.requires == ["req-a"]
    assert pipeline.produces == ["prod-b"]

def test_pipeline_exception_propagation():
    step1 = MockStep("step1")
    step2 = MockStep("step2", should_fail=True)
    pipeline = Pipeline("p", steps=[step1, step2])
    
    context = {}
    with pytest.raises(ValueError) as excinfo:
        pipeline.run(context)
    
    assert "Step step2 failed" in str(excinfo.value)
    assert step1.executed is True
    assert step2.executed is True

def test_pipeline_add_step():
    pipeline = Pipeline("p")
    step = MockStep("step1")
    pipeline.add_step(step)
    assert pipeline.steps == [step]
