from agent_template.agents.starter import starter_agent


def test_starter_agent_instantiates():
    agent = starter_agent()
    assert agent.name == "StarterAgent"
    assert any(t.name for t in agent.tools)
