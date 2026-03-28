from graphviz import Digraph
from smal.schemas.smal_file import SMALFile
from pathlib import Path

def generate_state_machine_svg(smal_path: str | Path, svg_output_dir: str | Path) -> None:
    smal_path = Path(smal_path)
    if not smal_path.is_file():
        raise ValueError(f"Invalid filepath for SMAL file: {smal_path}")
    svg_output_dir = Path(svg_output_dir)
    if not svg_output_dir.is_dir():
        raise ValueError(f"Invalid SVG output dir: {svg_output_dir}")

    # Parse the SMAL file
    smal = SMALFile.from_file(smal_path)

    # Create a graphviz Digraph using the SMAL file
    dot = Digraph(
        name=smal.machine,
        format="svg",
        graph_attr={"rankdir": "LR", "fontsize": "12", "fontname": "Arial"},
        node_attr={"shape": "box", "style": "filled", "fillcolor": "#f0f0f0"},
        edge_attr={"fontsize": "10"},
    )

    # Add states
    for state in smal.states:
        dot.node(state.name)

    # Add transitions
    for t in smal.transitions:
        label = f"{t.trigger_evt} / {t.action}"
        if t.landing_state_entry_evt:
            label += f" → {t.landing_state_entry_evt}"
        dot.edge(t.trigger_state, t.landing_state, label=label)

    # Render the SVG file
    dot.render(filename=smal.machine.lower(), directory=svg_output_dir, cleanup=True)
