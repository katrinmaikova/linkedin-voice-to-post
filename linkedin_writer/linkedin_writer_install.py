import asyncio
import base64
import json
from pathlib import Path

from flexus_client_kit import ckit_client, ckit_bot_install
from flexus_client_kit import ckit_cloudtool

from linkedin_writer import linkedin_writer_prompts

BOT_DESCRIPTION = """
## LinkedIn Post Writer - Your Personal Writing Assistant

Transform voice memos and ideas into polished LinkedIn posts that match your unique writing style.

**How It Works:**

1. **Learn Your Style** (One-time setup)
   - Paste your last 5 LinkedIn posts
   - Bot analyzes your tone, structure, and formatting
   - Review and approve the style profile

2. **Create Posts**
   - Send a voice memo or text with your ideas
   - Bot generates a draft matching your style
   - Edit and publish

3. **Refine Over Time**
   - Provide new sample posts to update your style
   - Bot adapts to your evolving voice

**Key Features:**
- **Voice-to-post**: Speak your thoughts, get polished text
- **Style matching**: Posts sound like YOU, not a generic bot
- **Persistent learning**: Style saved across sessions
- **Quick turnaround**: From idea to draft in seconds

**Perfect for:**
- Busy professionals who think faster than they type
- Content creators maintaining consistent voice
- Anyone wanting to post more consistently on LinkedIn

**Requirements:**
- OpenAI API key (for audio transcription)
"""

LINKEDIN_WRITER_SETUP_SCHEMA = [
    {
        "bs_name": "OPENAI_API_KEY",
        "bs_type": "string_long",
        "bs_default": "",
        "bs_group": "API Keys",
        "bs_order": 1,
        "bs_importance": 2,
        "bs_description": "OpenAI API key for audio transcription (Whisper API). Get one at https://platform.openai.com/api-keys",
    },
]


async def install(
    client: ckit_client.FlexusClient,
    ws_id: str,
    bot_name: str,
    bot_version: str,
    tools: list[ckit_cloudtool.CloudTool],
):
    bot_internal_tools = json.dumps([t.openai_style_tool() for t in tools])

    pic_big_path = Path(__file__).with_name("linkedin_writer-1024x1536.webp")
    pic_small_path = Path(__file__).with_name("linkedin_writer-256x256.webp")

    if pic_big_path.exists() and pic_small_path.exists():
        pic_big = base64.b64encode(open(pic_big_path, "rb").read()).decode("ascii")
        pic_small = base64.b64encode(open(pic_small_path, "rb").read()).decode("ascii")
    else:
        pic_big = ""
        pic_small = ""

    await ckit_bot_install.marketplace_upsert_dev_bot(
        client,
        ws_id=ws_id,
        marketable_name=bot_name,
        marketable_version=bot_version,
        marketable_accent_color="#0A66C2",
        marketable_title1="LinkedIn Post Writer",
        marketable_title2="Transform voice memos into LinkedIn posts matching your personal style",
        marketable_author="Flexus",
        marketable_occupation="Content Creation Assistant",
        marketable_description=BOT_DESCRIPTION,
        marketable_typical_group="Productivity / Content",
        marketable_github_repo="",
        marketable_run_this="python -m linkedin_writer.linkedin_writer_bot",
        marketable_setup_default=LINKEDIN_WRITER_SETUP_SCHEMA,
        marketable_featured_actions=[
            {"feat_question": "Help me set up my writing style", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Create a post from my latest idea", "feat_expert": "default", "feat_depends_on_setup": ["OPENAI_API_KEY"]},
        ],
        marketable_intro_message="Hi! I'm your LinkedIn Post Writer. I help you turn voice memos and ideas into polished posts that match your personal writing style.\n\nTo get started, I need to learn your writing style. Please paste your last 5 LinkedIn posts so I can analyze your tone, structure, and formatting.",
        marketable_preferred_model_default="grok-4-1-fast-non-reasoning",
        marketable_daily_budget_default=50_000,
        marketable_default_inbox_default=5_000,
        marketable_experts=[
            ("default", ckit_bot_install.FMarketplaceExpertInput(
                fexp_system_prompt=linkedin_writer_prompts.main_prompt,
                fexp_python_kernel="",
                fexp_block_tools="*setup*",
                fexp_allow_tools="",
                fexp_app_capture_tools=bot_internal_tools,
                fexp_description="Main conversational expert that learns writing style and generates LinkedIn posts from voice memos or text ideas.",
            )),
        ],
        marketable_tags=["LinkedIn", "Content Creation", "Voice-to-Text", "Writing Assistant"],
        marketable_picture_big_b64=pic_big,
        marketable_picture_small_b64=pic_small,
        marketable_schedule=[],
        marketable_forms=ckit_bot_install.load_form_bundles(__file__),
    )


if __name__ == "__main__":
    from linkedin_writer import linkedin_writer_bot
    args = ckit_bot_install.bot_install_argparse()
    client = ckit_client.FlexusClient("linkedin_writer_install")
    asyncio.run(install(client, ws_id=args.ws, bot_name=linkedin_writer_bot.BOT_NAME, bot_version=linkedin_writer_bot.BOT_VERSION, tools=linkedin_writer_bot.TOOLS))
