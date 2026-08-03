"""Entry point for running the teamwork coach workflow."""

from __future__ import annotations

from agents.coordinator import build_graph
from contract import AgentState, FinalResponse, ReflectionInput


def run_coach(reflection: str, student_goal: str | None = None) -> FinalResponse:
    """Run the full LangGraph workflow and return a final response."""
    app = build_graph()
    initial = AgentState(
        raw_input=reflection,
        student_goal=student_goal,
    )
    result = app.invoke(initial)
    # langgraph may return dict
    if isinstance(result, AgentState):
        final = result.final_response
    else:
        final = result.get("final_response")
        if isinstance(final, dict):
            final = FinalResponse.model_validate(final)

    if final is None:
        return FinalResponse(
            route="fallback",
            title="Unable to provide validated coaching",
            body="The workflow ended without a final response.",
        )
    return final


def main() -> None:
    sample = ReflectionInput(
        text=(
            "In our capstone team, tasks keep falling through because nobody is sure who owns "
            "the CAD and the report. Deadlines slip and meetings go in circles."
        ),
        student_goal="Improve coordination before the next milestone",
    )
    response = run_coach(sample.text, sample.student_goal)
    print(response.route)
    print(response.title)
    print(response.body)


if __name__ == "__main__":
    main()
