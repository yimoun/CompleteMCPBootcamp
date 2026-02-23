import base64
import re
import zlib
from typing import Dict


def clean_mermaid_code(raw: str) -> str:
    if not raw:
        return ""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("mermaid", "", 1).strip()
    text = text.replace("-->|", "--|").replace("|>", "|-->")
    return text


def normalize_mermaid(raw: str) -> str:
    template: Dict[str, str] = {
        "A1": "Skill 1",
        "A2": "Certification 1",
        "A3": "Project 1",
        "A4": "Milestone 1",
        "B1": "Skill 2",
        "B2": "Certification 2",
        "B3": "Project 2",
        "B4": "Milestone 2",
        "B5": "Experience 1",
        "B6": "Outcome 1",
        "C1": "Skill 3",
        "C2": "Certification 3",
        "C3": "Project 3",
        "C4": "Milestone 3",
        "C5": "Networking 1",
        "C6": "Outcome 2",
    }
    if raw:
        key_pattern = "|".join(map(re.escape, template.keys()))
        node_pattern = re.compile(
            rf"\b({key_pattern})\s*(\[[^\]]+\]|\([^\)]+\))"
        )
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            for match in node_pattern.finditer(line):
                key = match.group(1)
                raw_label = match.group(2)[1:-1].strip()
                label = raw_label.strip("\"'").replace("[", "").replace("]", "").strip()
                label = label[:50]
                if label:
                    template[key] = label
    return (
        "graph LR\n"
        "  subgraph 0-3 months\n"
        f"    A1[{template['A1']}] --> A2[{template['A2']}]\n"
        f"    A3[{template['A3']}] --> A4[{template['A4']}]\n"
        "  end\n"
        "  subgraph 3-6 months\n"
        f"    B1[{template['B1']}] --> B2[{template['B2']}]\n"
        f"    B3[{template['B3']}] --> B4[{template['B4']}]\n"
        f"    B5[{template['B5']}] --> B6[{template['B6']}]\n"
        "  end\n"
        "  subgraph 6-12 months\n"
        f"    C1[{template['C1']}] --> C2[{template['C2']}]\n"
        f"    C3[{template['C3']}] --> C4[{template['C4']}]\n"
        f"    C5[{template['C5']}] --> C6[{template['C6']}]\n"
        "  end\n"
        "  A2 --> B1\n"
        "  A4 --> B3\n"
        "  B2 --> C1\n"
        "  B4 --> C3\n"
        "  B6 --> C5\n"
    )


def build_mermaid_from_labels(labels: Dict[str, str]) -> str:
    template: Dict[str, str] = {
        "A1": "Skill 1",
        "A2": "Certification 1",
        "A3": "Project 1",
        "A4": "Milestone 1",
        "B1": "Skill 2",
        "B2": "Certification 2",
        "B3": "Project 2",
        "B4": "Milestone 2",
        "B5": "Experience 1",
        "B6": "Outcome 1",
        "C1": "Skill 3",
        "C2": "Certification 3",
        "C3": "Project 3",
        "C4": "Milestone 3",
        "C5": "Networking 1",
        "C6": "Outcome 2",
    }
    for key, value in (labels or {}).items():
        if key in template and isinstance(value, str):
            label = value.strip().strip("\"'")[:50]
            if label:
                template[key] = label
    return (
        "graph LR\n"
        "  subgraph 0-3 months\n"
        f"    A1[{template['A1']}] --> A2[{template['A2']}]\n"
        f"    A3[{template['A3']}] --> A4[{template['A4']}]\n"
        "  end\n"
        "  subgraph 3-6 months\n"
        f"    B1[{template['B1']}] --> B2[{template['B2']}]\n"
        f"    B3[{template['B3']}] --> B4[{template['B4']}]\n"
        f"    B5[{template['B5']}] --> B6[{template['B6']}]\n"
        "  end\n"
        "  subgraph 6-12 months\n"
        f"    C1[{template['C1']}] --> C2[{template['C2']}]\n"
        f"    C3[{template['C3']}] --> C4[{template['C4']}]\n"
        f"    C5[{template['C5']}] --> C6[{template['C6']}]\n"
        "  end\n"
        "  A2 --> B1\n"
        "  A4 --> B3\n"
        "  B2 --> C1\n"
        "  B4 --> C3\n"
        "  B6 --> C5\n"
    )


def mermaid_image_url(mermaid_code: str) -> str:
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(mermaid_code.encode("utf-8")) + compressor.flush()
    payload = base64.urlsafe_b64encode(compressed).decode("utf-8").rstrip("=")
    return f"https://mermaid.ink/svg/{payload}"
