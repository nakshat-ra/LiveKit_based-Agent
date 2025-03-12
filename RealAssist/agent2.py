import os
import asyncio
import logging
 
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import elevenlabs,deepgram, openai, silero, cartesia
from livekit.plugins.deepgram import stt
from livekit.plugins.elevenlabs import tts
from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo
 
load_dotenv(dotenv_path=".env.local")
# deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
# if not deepgram_api_key:
#     raise ValueError("DEEPGRAM_API_KEY is missing! Check your .env file.")
 

deepgram_stt = deepgram.stt.STT(
    model="nova-2-general",
    interim_results=True,
    smart_format=True,
    punctuate=True,
    filler_words=True,
    profanity_filter=False,
    keywords=[("LiveKit", 1.5)],
    language="hi",
)
 
 

# elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
# if not elevenlabs_api_key:
#     raise ValueError("ELEVENLABS_API_KEY is missing! Check your .env file.")
 
elevenlabs_tts=elevenlabs.tts.TTS(
    model="eleven_multilingual_v2",
    voice=elevenlabs.tts.Voice(
        id="pNInz6obpgDQGcFmaJgB",
        name="Indian Customer Service",
        category="professional",
        settings=elevenlabs.tts.VoiceSettings(
            stability=0.75,
            similarity_boost=0.85,
            style=0.40,
            use_speaker_boost=True
        ),
    ),
    language="hi-IN",
    streaming_latency=2,
    enable_ssml_parsing=True,
    chunk_length_schedule=[80, 120, 200, 260],
)
 
 
logger = logging.getLogger("voice-assistant")
 
 
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
 
 
async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You have an Indian English accent. Your name is Maanvi, you are an assistant at 'Tumble Dry'. You have to talk to the customer and solve their queries about the company 'tumble dry'. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. Talk like a fun person so that the customer finds you likeable"
            "If the customer talks in hindi, then reply in hindi only for the next one sentence, switch to english again for all other replies"
        ),
    )
 
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
 
    # wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")


    dg_model = "nova-3-general"
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        # use a model optimized for telephony
        dg_model = "nova-2-phonecall"
 
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram_stt,
        llm=openai.LLM.with_azure(),
        tts=elevenlabs_tts,
        chat_ctx=initial_ctx,
    )
 
    agent.start(ctx.room, participant)
 
    usage_collector = metrics.UsageCollector()
 
    @agent.on("metrics_collected")
    def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
        metrics.log_metrics(mtrcs)
        usage_collector.collect(mtrcs)
 
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: ${summary}")
 
    ctx.add_shutdown_callback(log_usage)
 
    # listen to incoming chat messages, only required if you'd like the agent to
    # answer incoming messages from Chat
    chat = rtc.ChatManager(ctx.room)
 
    async def answer_from_text(txt: str):
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = agent.llm.chat(chat_ctx=chat_ctx)
        await agent.say(stream)
 
    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))
 
    await agent.say(
        '<speak>'
        '<prosody rate="95%" pitch="+2st">'
        '<emphasis level="moderate">'
        'Namaste! This is Maanvi, your assistant at Tumble dry. '
        '</emphasis>'
        '<break time="300ms"/>'
        'How may i help you today?'
        '</prosody>'
        '</speak>',
        allow_interruptions=True
    )
 
 
if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
 
 
 
#  #For the GPT-4o model on Azure, here are the relevant token limits:
# Context window (total tokens per request): 4,096 tokens by default
# Rate limits: 100K TPM (tokens per minute) and 1K RPM (requests per minute)
# Monthly usage tier: 12 billion tokens before potential latency variability