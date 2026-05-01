import streamlit as st
from anthropic import Anthropic

st.set_page_config(page_title="Second Brain", page_icon="🧠", layout="wide")

PROMPT_TEMPLATE = (
    "Break down the following topic as an elite IDX-focused investment analyst.\\n"
    "Use EXACTLY these delimiters to separate sections — nothing before the first delimiter:\\n\\n"
    "###SIMPLE###\\n"
    "(3-5 sentence plain explanation)\\n\\n"
    "###SYSTEM###\\n"
    "(key components + step-by-step, use • bullets)\\n\\n"
    "###MONEY###\\n"
    "(where money comes from, where it goes, who captures value — be specific about margins, rupiah flows, structures. Use • bullets. This is the most important section, go deep.)\\n\\n"
    "###PLAYERS###\\n"
    "(institutions + real IDX-listed company examples where possible, • bullets)\\n\\n"
    "###ECONOMICS###\\n"
    "(key drivers, attractive/risky factors, metrics to watch, • bullets)\\n\\n"
    "###RISKS###\\n"
    "(what breaks this system — include IDX-specific risks like ARB traps, OJK regulation, liquidity, FX, • bullets)\\n\\n"
    "###EXAMPLE###\\n"
    "(real or illustrative Indonesia deal or company — name names)\\n\\n"
    "###CONNECTIONS###\\n"
    "(links to other sectors: banking, coal, infra, capital markets)\\n\\n"
    "###INSIGHT###\\n"
    "(if I were a banker, analyst, or investor — what's the edge, what do I watch most)\\n\\n"
    "Topic: {topic}"
)

SECTION_META = [
    ("SIMPLE", "💡 Simple Explanation"),
    ("SYSTEM", "⚙️ System Breakdown"),
    ("MONEY", "💰 Money Flow"),
    ("PLAYERS", "🏦 Key Players"),
    ("ECONOMICS", "📊 Economics & Incentives"),
    ("RISKS", "⚠️ Risks & Failure Points"),
    ("EXAMPLE", "🇮🇩 Real-World Example (Indonesia)"),
    ("CONNECTIONS", "🔗 Connections"),
    ("INSIGHT", "🎯 Investor / Deal Insight"),
]

PRESET_TOPICS = [
    "Coal IDX",
    "CPO/Palm Oil",
    "Indonesian Banks & Project Finance",
    "Nickel Mining",
    "Toll Road Concessions",
    "DIRE/REIT",
]


def parse_sections(raw_text: str) -> dict[str, str]:
    content = raw_text.strip()
    parsed: dict[str, str] = {key: "" for key, _ in SECTION_META}

    for idx, (key, _) in enumerate(SECTION_META):
        delimiter = f"###{key}###"
        start = content.find(delimiter)
        if start == -1:
            continue
        start += len(delimiter)
        if idx + 1 < len(SECTION_META):
            next_delimiter = f"###{SECTION_META[idx + 1][0]}###"
            end = content.find(next_delimiter, start)
        else:
            end = len(content)
        parsed[key] = content[start:end].strip()

    if all(not section for section in parsed.values()):
        parsed["SIMPLE"] = content
    return parsed


def run_analysis(topic: str) -> dict[str, str]:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        st.error(
            "Missing ANTHROPIC_API_KEY. Add it to .streamlit/secrets.toml locally "
            "or Streamlit Cloud Secrets before running analysis."
        )
        st.stop()

    client = Anthropic(api_key=api_key)
    with st.spinner("Analyzing topic with Claude..."):
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2200,
            temperature=0.25,
            messages=[
                {"role": "user", "content": PROMPT_TEMPLATE.format(topic=topic.strip())}
            ],
        )

    text_blocks = [
        block.text for block in response.content if getattr(block, "type", "") == "text"
    ]
    return parse_sections("\n".join(text_blocks))


def render_sections(sections: dict[str, str]) -> None:
    for key, label in SECTION_META:
        body = sections.get(key) or "No content returned for this section."
        with st.expander(label, expanded=True):
            if key == "MONEY":
                st.markdown(
                    """
                    <div style="border-left: 6px solid #d97706; background: #fffbeb; padding: 0.85rem 1rem; border-radius: 0.35rem;">
                      <div style="font-weight: 700; color: #92400e; margin-bottom: 0.45rem;">High-Priority Value Capture Map</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(body)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown(body)


st.sidebar.title("🧠 SECOND_BRAIN_V1")
st.sidebar.caption("Structured sector intelligence for IDX-focused investors.")
st.sidebar.markdown("---")
st.sidebar.subheader("Preset Topics")

if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "analysis_sections" not in st.session_state:
    st.session_state.analysis_sections = None

for preset in PRESET_TOPICS:
    if st.sidebar.button(preset, use_container_width=True):
        st.session_state.topic_input = preset
        st.session_state.analysis_sections = run_analysis(preset)

st.title("Second Brain")
st.write("Analyze sectors, financing structures, and business models with IDX context.")

topic = st.text_input(
    "Enter any sector, deal structure, or business model...",
    value=st.session_state.topic_input,
)
st.session_state.topic_input = topic

if st.button("Analyze ↗", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("Please enter a topic before analyzing.")
    else:
        st.session_state.analysis_sections = run_analysis(topic)

if st.session_state.analysis_sections:
    render_sections(st.session_state.analysis_sections)
