import asyncio
import base64
import json
import logging
import os
from typing import Dict, Any, Optional

from elevenlabs.client import AsyncElevenLabs
from pymongo import AsyncMongoClient

from flexus_client_kit import ckit_client
from flexus_client_kit import ckit_cloudtool
from flexus_client_kit import ckit_bot_exec
from flexus_client_kit import ckit_shutdown
from flexus_client_kit import ckit_ask_model
from flexus_client_kit import ckit_mongo
from flexus_client_kit import ckit_kanban
from flexus_client_kit.integrations import fi_mongo_store
from flexus_client_kit.integrations import fi_pdoc
from linkedin_writer import linkedin_writer_install

logger = logging.getLogger("bot_linkedin_writer")

BOT_NAME = "linkedin_writer"
BOT_VERSION = "0.1.0"

TRANSCRIBE_AUDIO_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="transcribe_audio",
    description="Transcribe audio from the current message. Call this when the user sends a voice memo or audio file.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    },
)

ANALYZE_STYLE_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="analyze_style",
    description="Analyze sample LinkedIn posts to extract writing style patterns. Provide the posts as a single text with posts separated by '---'.",
    parameters={
        "type": "object",
        "properties": {
            "sample_posts": {"type": "string", "description": "Sample LinkedIn posts separated by '---'"},
        },
        "required": ["sample_posts"],
        "additionalProperties": False,
    },
)

GENERATE_POST_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="generate_post",
    description="Generate a LinkedIn post based on the content and learned style profile.",
    parameters={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The content/ideas to turn into a post"},
            "style_profile": {"type": "string", "description": "JSON string of the style profile to follow"},
        },
        "required": ["content", "style_profile"],
        "additionalProperties": False,
    },
)

TOOLS = [
    TRANSCRIBE_AUDIO_TOOL,
    ANALYZE_STYLE_TOOL,
    GENERATE_POST_TOOL,
    fi_mongo_store.MONGO_STORE_TOOL,
    fi_pdoc.POLICY_DOCUMENT_TOOL,
]


async def linkedin_writer_main_loop(fclient: ckit_client.FlexusClient, rcx: ckit_bot_exec.RobotContext) -> None:
    setup = ckit_bot_exec.official_setup_mixing_procedure(
        linkedin_writer_install.LINKEDIN_WRITER_SETUP_SCHEMA,
        rcx.persona.persona_setup,
    )

    mongo_conn_str = await ckit_mongo.mongo_fetch_creds(fclient, rcx.persona.persona_id)
    mongo = AsyncMongoClient(mongo_conn_str)
    dbname = rcx.persona.persona_id + "_db"
    mydb = mongo[dbname]
    personal_mongo = mydb["personal_mongo"]
    pdoc_integration = fi_pdoc.IntegrationPdoc(rcx, rcx.persona.ws_root_group_id)

    elevenlabs_api_key = setup.get("ELEVENLABS_API_KEY", os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_client = AsyncElevenLabs(api_key=elevenlabs_api_key) if elevenlabs_api_key else None

    @rcx.on_updated_message
    async def updated_message_in_db(msg: ckit_ask_model.FThreadMessageOutput):
        pass

    @rcx.on_updated_thread
    async def updated_thread_in_db(th: ckit_ask_model.FThreadOutput):
        pass

    @rcx.on_updated_task
    async def updated_task_in_db(t: ckit_kanban.FPersonaKanbanTaskOutput):
        pass

    @rcx.on_tool_call(TRANSCRIBE_AUDIO_TOOL.name)
    async def toolcall_transcribe_audio(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        if not elevenlabs_client:
            return "ERROR: ElevenLabs API key not configured. Please add your ElevenLabs API key in bot setup."

        try:
            thread = await ckit_ask_model.thread_get(fclient, toolcall.fcall_ft_id)
            if not thread or not thread.ft_messages:
                return "ERROR: Could not find the message with audio content."

            last_user_msg = None
            for msg in reversed(thread.ft_messages):
                if msg.m_role == "user":
                    last_user_msg = msg
                    break

            if not last_user_msg:
                return "ERROR: No user message found in this thread."

            audio_found = False
            audio_data = None
            audio_format = None

            if isinstance(last_user_msg.m_content, list):
                for item in last_user_msg.m_content:
                    if isinstance(item, dict):
                        m_type = item.get("m_type", "")
                        if "audio" in m_type.lower() or "ogg" in m_type.lower():
                            audio_found = True
                            audio_data = item.get("m_content", "")
                            audio_format = m_type
                            break

            if not audio_found:
                return "No audio content found in the message. If you sent text, I can work with that directly."

            audio_bytes = base64.b64decode(audio_data)

            response = await elevenlabs_client.speech_to_text.convert(
                audio=audio_bytes,
                model_id="scribe_v2",
            )

            transcript = response.text

            logger.info(f"Transcription successful: {len(transcript)} chars")
            return f"Audio transcribed successfully:\n\n{transcript}"

        except Exception as e:
            logger.exception("Transcription failed")
            return f"ERROR: Failed to transcribe audio: {str(e)}"

    @rcx.on_tool_call(ANALYZE_STYLE_TOOL.name)
    async def toolcall_analyze_style(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        sample_posts = model_produced_args["sample_posts"]
        posts = [p.strip() for p in sample_posts.split("---") if p.strip()]

        if len(posts) < 3:
            return "Please provide at least 3 sample posts for accurate style analysis."

        analysis = {
            "total_posts_analyzed": len(posts),
            "avg_length": sum(len(p) for p in posts) // len(posts),
            "length_range": {"min": min(len(p) for p in posts), "max": max(len(p) for p in posts)},
            "uses_emojis": any("😀" <= c <= "🙏" or "🌀" <= c <= "🗿" for p in posts for c in p),
            "uses_hashtags": any("#" in p for p in posts),
            "avg_paragraphs": sum(p.count("\n\n") + 1 for p in posts) / len(posts),
            "common_openings": [],
            "common_closings": [],
            "tone_indicators": {
                "questions": sum(p.count("?") for p in posts) / len(posts),
                "exclamations": sum(p.count("!") for p in posts) / len(posts),
                "personal_pronouns": sum(1 for p in posts if any(word in p.lower() for word in ["i ", "my ", "i'm ", "i've "])),
            },
            "sample_posts": posts[:2],
        }

        for post in posts:
            first_line = post.split("\n")[0][:50]
            analysis["common_openings"].append(first_line)

            lines = post.split("\n")
            last_line = [l for l in lines if l.strip()][-1][:50] if lines else ""
            analysis["common_closings"].append(last_line)

        result = "## Style Analysis Results\n\n"
        result += f"**Posts analyzed**: {analysis['total_posts_analyzed']}\n"
        result += f"**Average length**: {analysis['avg_length']} characters\n"
        result += f"**Length range**: {analysis['length_range']['min']} - {analysis['length_range']['max']} chars\n"
        result += f"**Average paragraphs**: {analysis['avg_paragraphs']:.1f}\n"
        result += f"**Uses emojis**: {'Yes' if analysis['uses_emojis'] else 'No'}\n"
        result += f"**Uses hashtags**: {'Yes' if analysis['uses_hashtags'] else 'No'}\n"
        result += f"**Personal tone**: {analysis['tone_indicators']['personal_pronouns']}/{len(posts)} posts use first person\n"
        result += f"**Questions per post**: {analysis['tone_indicators']['questions']:.1f}\n"
        result += f"**Exclamations per post**: {analysis['tone_indicators']['exclamations']:.1f}\n\n"
        result += "This profile will be saved and used to generate posts matching your style.\n\n"
        result += f"**Raw profile data**:\n```json\n{json.dumps(analysis, indent=2)}\n```"

        return result

    @rcx.on_tool_call(GENERATE_POST_TOOL.name)
    async def toolcall_generate_post(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        content = model_produced_args["content"]
        style_profile_str = model_produced_args["style_profile"]

        try:
            style_profile = json.loads(style_profile_str)
        except json.JSONDecodeError:
            return "ERROR: Invalid style profile format."

        guidance = f"""Generate a LinkedIn post based on this content: {content}

Follow this style profile:
- Average length: {style_profile.get('avg_length', 500)} characters
- Paragraphs: {style_profile.get('avg_paragraphs', 2):.0f}
- Use emojis: {style_profile.get('uses_emojis', False)}
- Use hashtags: {style_profile.get('uses_hashtags', False)}
- Questions per post: {style_profile.get('tone_indicators', {}).get('questions', 0):.0f}
- Personal tone: {'Use first person' if style_profile.get('tone_indicators', {}).get('personal_pronouns', 0) > 0 else 'Professional third person'}

Match the style of these sample openings: {', '.join(style_profile.get('common_openings', [])[:2])}

Generate ONLY the LinkedIn post text, nothing else."""

        return f"DRAFT POST:\n\n{guidance}"

    @rcx.on_tool_call(fi_mongo_store.MONGO_STORE_TOOL.name)
    async def toolcall_mongo_store(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await fi_mongo_store.handle_mongo_store(
            rcx.workdir,
            personal_mongo,
            toolcall,
            model_produced_args,
        )

    @rcx.on_tool_call(fi_pdoc.POLICY_DOCUMENT_TOOL.name)
    async def toolcall_pdoc(toolcall: ckit_cloudtool.FCloudtoolCall, model_produced_args: Dict[str, Any]) -> str:
        return await pdoc_integration.called_by_model(toolcall, model_produced_args)

    try:
        while not ckit_shutdown.shutdown_event.is_set():
            await rcx.unpark_collected_events(sleep_if_no_work=10.0)

    finally:
        logger.info("%s exit" % (rcx.persona.persona_id,))
        if mongo:
            mongo.close()


def main():
    scenario_fn = ckit_bot_exec.parse_bot_args()
    fclient = ckit_client.FlexusClient(ckit_client.bot_service_name(BOT_NAME, BOT_VERSION), endpoint="/v1/jailed-bot")

    asyncio.run(ckit_bot_exec.run_bots_in_this_group(
        fclient,
        marketable_name=BOT_NAME,
        marketable_version_str=BOT_VERSION,
        bot_main_loop=linkedin_writer_main_loop,
        inprocess_tools=TOOLS,
        scenario_fn=scenario_fn,
        install_func=linkedin_writer_install.install,
    ))


if __name__ == "__main__":
    main()
