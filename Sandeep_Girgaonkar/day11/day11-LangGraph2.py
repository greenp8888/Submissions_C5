import streamlit as st
import json
import openai
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import requests
from datetime import datetime
import re

st.set_page_config(
    page_title="🌟 AI Story Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

class StoryState(TypedDict):
    story_id: str
    character_name: str
    story_theme: str
    story_genre: str
    current_scene: str
    story_context: str
    character_traits: List[str]
    inventory: List[str]
    relationships: Dict[str, str]
    choices_made: List[Dict[str, Any]]
    story_progression: int
    current_narrative: str
    available_choices: List[Dict[str, str]]
    story_complete: bool
    mood: str
    world_state: Dict[str, Any]

class AIStoryGenerator:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = "openai/gpt-4o-mini"
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(StoryState)
        workflow.add_node("initialize_story", self._initialize_story)
        workflow.add_node("generate_scene", self._generate_scene)
        workflow.add_node("process_choice", self._process_choice)
        workflow.add_node("update_world_state", self._update_world_state)
        workflow.add_node("generate_ending", self._generate_ending)
        workflow.set_entry_point("initialize_story")
        workflow.add_edge("initialize_story", "generate_scene")
        workflow.add_edge("generate_scene", END)
        workflow.add_edge("process_choice", "update_world_state")
        workflow.add_edge("update_world_state", "generate_scene")
        workflow.add_edge("generate_ending", END)
        return workflow.compile()

    def _call_gpt4o(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error("Error calling GPT-4o: " + str(e))
            return "Error generating content. Please check your API key and try again."

    def _extract_json_from_response(self, response: str) -> dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            matches = re.findall(r'\{.*\}', response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            return None

    def _initialize_story(self, state: StoryState) -> StoryState:
        system_prompt = (
            "You are a master storyteller creating an interactive " + state["story_genre"] + " story "
            "with the theme: " + state["story_theme"] + ".\\n\\n"
            "Create an engaging opening for a character named " + state["character_name"] + ".\\n\\n"
            "IMPORTANT: Your response must be valid JSON in this exact format:\\n"
            "{\\n"
            "    \"narrative\": \"The opening story text with rich descriptions and atmosphere\",\\n"
            "    \"context\": \"Brief summary of the current situation\",\\n"
            "    \"character_traits\": [\"trait1\", \"trait2\", \"trait3\"],\\n"
            "    \"inventory\": [\"item1\", \"item2\", \"item3\"],\\n"
            "    \"world_state\": {\"location\": \"starting_location\", \"time_of_day\": \"time\", \"weather\": \"weather_condition\"},\\n"
            "    \"mood\": \"current_story_mood\"\\n"
            "}\\n\\n"
            "Make the opening compelling and set up the adventure."
        )
        prompt = (
            "Create an opening scene for an interactive story:\\n"
            "- Character: " + state["character_name"] + "\\n"
            "- Genre: " + state["story_genre"] + "\\n"
            "- Theme: " + state["story_theme"] + "\\n\\n"
            "Generate an engaging opening that introduces the character and sets up the adventure."
        )
        response = self._call_gpt4o(prompt, system_prompt)
        story_data = self._extract_json_from_response(response)
        if story_data:
            state.update({
                "current_narrative": story_data.get("narrative", "Your adventure begins..."),
                "story_context": story_data.get("context", "A new adventure unfolds."),
                "character_traits": story_data.get("character_traits", ["brave", "curious"]),
                "inventory": story_data.get("inventory", ["basic supplies"]),
                "world_state": story_data.get("world_state", {}),
                "mood": story_data.get("mood", "mysterious"),
                "current_scene": "opening",
                "story_progression": 1
            })
        else:
            state.update({
                "current_narrative": "The story of " + state["character_name"] + " begins...",
                "story_context": "Beginning adventure for " + state["character_name"],
                "character_traits": ["brave", "curious", "determined"],
                "inventory": ["traveler\'s pack", "water flask", "mysterious compass"],
                "world_state": {"location": "mysterious crossroads", "time": "dawn", "weather": "misty"},
                "mood": "mysterious",
                "current_scene": "opening",
                "story_progression": 1
            })
        return state

    def _generate_scene(self, state: StoryState) -> StoryState:
        choice_history = ""
        if state["choices_made"]:
            recent_choices = state["choices_made"][-3:]
            choice_history = "Recent player choices: " + "; ".join([c["choice_text"] for c in recent_choices])
        system_prompt = (
            "You are continuing an interactive " + state["story_genre"] + " story with theme: " + state["story_theme"] + ".\\n\\n"
            "CONTEXT:\\n"
            "- Character: " + state["character_name"] + "\\n"
            "- Traits: " + ", ".join(state["character_traits"]) + "\\n"
            "- Inventory: " + ", ".join(state["inventory"]) + "\\n"
            "- Current mood: " + state["mood"] + "\\n"
            "- World state: " + json.dumps(state["world_state"]) + "\\n"
            "- Story progression: " + str(state["story_progression"]) + "/10\\n"
            "- " + choice_history + "\\n\\n"
            "Your response MUST be valid JSON in this exact format:\\n"
            "{\\n"
            "    \"narrative\": \"Compelling scene description continuing the story\",\\n"
            "    \"choices\": [\\n"
            "        {\"id\": \"choice1\", \"text\": \"First choice option\", \"consequences\": \"potential outcome\"},\\n"
            "        {\"id\": \"choice2\", \"text\": \"Second choice option\", \"consequences\": \"potential outcome\"},\\n"
            "        {\"id\": \"choice3\", \"text\": \"Third choice option\", \"consequences\": \"potential outcome\"}\\n"
            "    ],\\n"
            "    \"scene_type\": \"action/dialogue/exploration/puzzle/combat\",\\n"
            "    \"updated_mood\": \"current emotional tone\"\\n"
            "}\\n\\n"
            "Create meaningful choices that impact the story."
        )
        prompt = (
            "Continue the story from: " + state["story_context"] + "\\n\\n"
            "Current situation: " + state.get("current_narrative", "")[-500:] + "\\n\\n"
            "Generate the next scene with 3 meaningful choices for the player."
        )
        response = self._call_gpt4o(prompt, system_prompt)
        scene_data = self._extract_json_from_response(response)
        if scene_data:
            state.update({
                "current_narrative": scene_data.get("narrative", "The story continues..."),
                "available_choices": scene_data.get("choices", [
                    {"id": "continue", "text": "Continue forward", "consequences": "unknown"}
                ]),
                "current_scene": scene_data.get("scene_type", "exploration"),
                "mood": scene_data.get("updated_mood", state["mood"])
            })
        else:
            state.update({
                "current_narrative": "The adventure continues as " + state["character_name"] + " faces new challenges.",
                "available_choices": [
                    {"id": "continue", "text": "Continue the adventure", "consequences": "Move forward with courage"},
                    {"id": "explore", "text": "Explore the area thoroughly", "consequences": "Discover hidden secrets"},
                    {"id": "rest", "text": "Take a moment to rest and think", "consequences": "Regain strength and clarity"}
                ],
                "current_scene": "exploration"
            })
        return state

    def _process_choice(self, state: StoryState) -> StoryState:
        if not state.get("pending_choice"):
            return state
        choice_id = state["pending_choice"]
        chosen_option = None
        for choice in state["available_choices"]:
            if choice["id"] == choice_id:
                chosen_option = choice
                break
        if not chosen_option:
            return state
        system_prompt = (
            "You are processing a player choice in an interactive " + state["story_genre"] + " story.\\n\\n"
            "CONTEXT:\\n"
            "- Character: " + state["character_name"] + " with traits: " + ", ".join(state["character_traits"]) + "\\n"
            "- Current inventory: " + ", ".join(state["inventory"]) + "\\n"
            "- Player chose: " + chosen_option["text"] + "\\n"
            "- Potential consequences: " + chosen_option.get("consequences", "unknown") + "\\n\\n"
            "Your response MUST be valid JSON:\\n"
            "{\\n"
            "    \"consequence_narrative\": \"What happens as a result of this choice\",\\n"
            "    \"trait_changes\": [\"new_trait1\", \"new_trait2\"],\\n"
            "    \"inventory_changes\": {\"add\": [\"item1\"], \"remove\": [\"item2\"]},\\n"
            "    \"relationship_updates\": {\"character_name\": \"relationship_status\"},\\n"
            "    \"context_update\": \"Brief summary of new situation\"\\n"
            "}\\n\\n"
            "Make consequences meaningful and logical."
        )
        prompt = (
            "Process this choice: " + chosen_option["text"] + "\\n"
            "Current story context: " + state["story_context"] + "\\n"
            "Determine realistic consequences."
        )
        response = self._call_gpt4o(prompt, system_prompt)
        consequence_data = self._extract_json_from_response(response)
        if consequence_data:
            for trait in consequence_data.get("trait_changes", []):
                if trait not in state["character_traits"]:
                    state["character_traits"].append(trait)
            inventory_changes = consequence_data.get("inventory_changes", {})
            for item in inventory_changes.get("add", []):
                if item not in state["inventory"]:
                    state["inventory"].append(item)
            for item in inventory_changes.get("remove", []):
                if item in state["inventory"]:
                    state["inventory"].remove(item)
            state["relationships"].update(consequence_data.get("relationship_updates", {}))
            state["choices_made"].append({
                "choice_id": choice_id,
                "choice_text": chosen_option["text"],
                "consequence": consequence_data.get("consequence_narrative", ""),
                "scene": state["current_scene"]
            })
            state["story_context"] = consequence_data.get("context_update", state["story_context"])
        else:
            state["choices_made"].append({
                "choice_id": choice_id,
                "choice_text": chosen_option["text"],
                "consequence": state["character_name"] + "\'s choice leads to new developments.",
                "scene": state["current_scene"]
            })
        state["pending_choice"] = None
        state["story_progression"] += 1
        return state

    def _update_world_state(self, state: StoryState) -> StoryState:
        system_prompt = (
            "Update the world state for this " + state["story_genre"] + " story.\\n\\n"
            "CONTEXT:\\n"
            "- Current world state: " + json.dumps(state["world_state"]) + "\\n"
            "- Recent choice: " + (state["choices_made"][-1]["choice_text"] if state["choices_made"] else "None") + "\\n"
            "- Story progression: " + str(state["story_progression"]) + "/10\\n\\n"
            "Your response MUST be valid JSON:\\n"
            "{\\n"
            "    \"world_state\": {\"location\": \"current_location\", \"time_of_day\": \"time\", \"weather\": \"condition\"},\\n"
            "    \"story_context\": \"Updated situation summary\"\\n"
            "}"
        )
        prompt = "Update the world state based on recent events and story progression."
        response = self._call_gpt4o(prompt, system_prompt)
        update_data = self._extract_json_from_response(response)
        if update_data:
            state["world_state"].update(update_data.get("world_state", {}))
            state["story_context"] = update_data.get("story_context", state["story_context"])
        return state

    def _generate_ending(self, state: StoryState) -> StoryState:
        system_prompt = (
            "Create an epic conclusion for this " + state["story_genre"] + " story.\\n\\n"
            "STORY SUMMARY:\\n"
            "- Character: " + state["character_name"] + "\\n"
            "- Final traits: " + ", ".join(state["character_traits"]) + "\\n"
            "- Final inventory: " + ", ".join(state["inventory"]) + "\\n"
            "- Relationships: " + json.dumps(state["relationships"]) + "\\n"
            "- Key choices made: " + str([c["choice_text"] for c in state["choices_made"][-5:]]) + "\\n\\n"
            "Your response MUST be valid JSON:\\n"
            "{\\n"
            "    \"ending_narrative\": \"Epic conclusion that ties together the story elements\",\\n"
            "    \"final_character_state\": \"What the character has become\",\\n"
            "    \"story_resolution\": \"How the main conflicts were resolved\",\\n"
            "    \"epilogue\": \"What happens next for the character\"\\n"
            "}\\n\\n"
            "Make it satisfying and reflect the player\'s choices throughout the journey."
        )
        prompt = "Create an ending for the adventure of " + state["character_name"] + " based on their journey."
        response = self._call_gpt4o(prompt, system_prompt)
        ending_data = self._extract_json_from_response(response)
        if ending_data:
            ending_text = (
                "\\n🎭 **THE END** 🎭\\n\\n"
                + ending_data.get("ending_narrative", "Your adventure comes to an end...") + "\\n\\n"
                "**Final Character State:**\\n" + ending_data.get("final_character_state", "") + "\\n\\n"
                "**Story Resolution:**\\n" + ending_data.get("story_resolution", "") + "\\n\\n"
                "**Epilogue:**\\n" + ending_data.get("epilogue", "") + "\\n\\n"
                "**Your Journey:**\\n"
                "- Scenes Completed: " + str(state["story_progression"]) + "\\n"
                "- Choices Made: " + str(len(state["choices_made"])) + "\\n"
                "- Final Traits: " + ", ".join(state["character_traits"]) + "\\n"
                "- Final Inventory: " + ", ".join(state["inventory"])
            )
        else:
            ending_text = (
                "\\n🎭 **THE END** 🎭\\n\\n"
                "The adventure of " + state["character_name"] + " comes to a memorable conclusion.\\n\\n"
                "**Your Journey:**\\n"
                "- Scenes Completed: " + str(state["story_progression"]) + "\\n"
                "- Choices Made: " + str(len(state["choices_made"])) + "\\n"
                "- Final Inventory: " + ", ".join(state["inventory"])
            )
        state.update({
            "current_narrative": ending_text,
            "available_choices": [],
            "story_complete": True
        })
        return state

    def start_new_story(self, character_name: str, story_theme: str, story_genre: str) -> StoryState:
        initial_state = StoryState(
            story_id="story_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            character_name=character_name,
            story_theme=story_theme,
            story_genre=story_genre,
            current_scene="",
            story_context="",
            character_traits=[],
            inventory=[],
            relationships={},
            choices_made=[],
            story_progression=0,
            current_narrative="",
            available_choices=[],
            story_complete=False,
            mood="",
            world_state={}
        )
        return self.graph.invoke(initial_state)

    def continue_story_after_choice(self, state: StoryState, choice_id: str) -> StoryState:
        state["pending_choice"] = choice_id
        if state["story_progression"] >= 8:
            return self._generate_ending(state)
        state = self._process_choice(state)
        state = self._update_world_state(state)
        state = self._generate_scene(state)
        return state

# streamlit UI code below
# This connects to story generator class above

def main():
    st.title("🌟 AI-Powered Interactive Story Generator")
    st.markdown("*Experience dynamic stories powered by GPT-4o and LangGraph*")

    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("OpenRouter API Key", type="password")

        if not api_key:
            st.warning("Please enter your OpenRouter API key to begin!")
            st.stop()

        st.success("✅ API Key entered!")
        st.header("📖 Story Settings")
        character_name = st.text_input("Character Name", value="Hero")
        story_genre = st.selectbox("Story Genre", ["Fantasy", "Sci-Fi", "Mystery", "Horror", "Adventure", "Romance", "Thriller", "Western", "Cyberpunk", "Steampunk"])
        story_theme = st.text_input("Story Theme", value="A quest for redemption")
        new_story = st.button("🚀 Start New Story", type="primary")

        if "story_state" in st.session_state:
            st.header("📊 Progress")
            progress = st.session_state.story_state.get("story_progression", 0) / 10
            st.progress(progress)
            st.write("Scene " + str(st.session_state.story_state.get("story_progression", 0)) + "/10")

    if "generator" not in st.session_state:
        st.session_state.generator = AIStoryGenerator(api_key)

    if new_story:
        if not character_name.strip():
            st.error("Please enter a character name!")
            return
        if not story_theme.strip():
            st.error("Please enter a story theme!")
            return
        with st.spinner("🎭 Generating your unique story..."):
            try:
                st.session_state.story_state = st.session_state.generator.start_new_story(character_name, story_theme, story_genre)
                st.success("✨ Your story has been generated!")
            except Exception as e:
                st.error("Error generating story: " + str(e))
                return

    if "story_state" in st.session_state:
        story_state = st.session_state.story_state
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown("### 📚 Current Scene")
            st.markdown(story_state.get("current_narrative", ""))

            if story_state.get("available_choices") and not story_state.get("story_complete"):
                st.markdown("### 🤔 What do you choose?")
                choice_cols = st.columns(len(story_state["available_choices"]))
                for i, choice in enumerate(story_state["available_choices"]):
                    with choice_cols[i]:
                        if st.button(choice["text"], key="choice_" + str(i), help=choice.get("consequences", ""), use_container_width=True):
                            with st.spinner("🎲 Processing your choice..."):
                                try:
                                    st.session_state.story_state = st.session_state.generator.continue_story_after_choice(story_state, choice["id"])
                                    st.rerun()
                                except Exception as e:
                                    st.error("Error processing choice: " + str(e))

            elif story_state.get("story_complete"):
                st.success("🎉 Story Complete!")
                if st.button("📖 Start Another Adventure"):
                    del st.session_state.story_state
                    st.rerun()

        with col2:
            st.markdown("### 👤 Character")
            st.write("**Name:** " + story_state.get("character_name", ""))
            st.write("**Mood:** " + story_state.get("mood", ""))
            if story_state.get("character_traits"):
                st.markdown("**Traits:**")
                for trait in story_state["character_traits"]:
                    st.write("• " + trait)
            if story_state.get("inventory"):
                st.markdown("**Inventory:**")
                for item in story_state["inventory"]:
                    st.write("• " + item)
            if story_state.get("world_state"):
                st.markdown("### 🌍 World State")
                for key, value in story_state["world_state"].items():
                    st.write("**" + key.title() + ":** " + str(value))
            if story_state.get("choices_made"):
                st.markdown("### 📜 Recent Choices")
                for choice in reversed(story_state["choices_made"][-3:]):
                    with st.expander("Scene " + str(choice.get("scene", ""))):
                        st.write("**Choice:** " + choice["choice_text"])
                        if choice.get("consequence"):
                            st.write("**Result:** " + choice["consequence"])
    else:
        st.info("Configure your story in the sidebar and click Start New Story!")

if __name__ == "__main__":
    main()