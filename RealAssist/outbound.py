# import os
# import asyncio
# import logging
 
# from dotenv import load_dotenv
# from livekit import rtc
# from livekit.agents import (
#     AutoSubscribe,
#     JobContext,
#     JobProcess,
#     WorkerOptions,
#     cli,
#     llm,
#     metrics,
# )
# from livekit.agents.pipeline import VoicePipelineAgent
# from livekit.plugins import elevenlabs,deepgram, openai, silero, cartesia
# from livekit.plugins.deepgram import stt
# from livekit.plugins.elevenlabs import tts
# from livekit import api
# from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo
 
# load_dotenv(dotenv_path=".env.local")
 
# deepgram_stt = deepgram.stt.STT(
#     model="nova-2-general",
#     interim_results=True,
#     smart_format=True,
#     punctuate=True,
#     filler_words=True,
#     profanity_filter=False,
#     keywords=[("LiveKit", 1.5)],
#     language="hi",
# )
 
 
 
# elevenlabs_tts=elevenlabs.tts.TTS(
#     model="eleven_multilingual_v2",
#     voice=elevenlabs.tts.Voice(
#         id="vOfTZaTZQgdyQwy26jN9",
#         name="indianman",
#         category="professional",
#         settings=elevenlabs.tts.VoiceSettings(
#             stability=0.71,
#             similarity_boost=0.5,
#             style=0.0,
#             use_speaker_boost=True
#         ),
#     ),
#     #language="hi",
#     streaming_latency=4,
#     enable_ssml_parsing=False,
#     chunk_length_schedule=[80, 120, 200, 260],
# )
 
 
# logger = logging.getLogger("voice-assistant")
 
 
# def prewarm(proc: JobProcess):
#     proc.userdata["vad"] = silero.VAD.load()
 
 
# async def entrypoint(ctx: JobContext):
#     initial_ctx = llm.ChatContext().append(
#         role="system",
#         text=(
#             "Start by saying Namaste. Your name is Manish, you are an assistant at TumbleDry. Your interface with users will be voice. "
#             "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
#         ),
#     )
 
#     logger.info(f"connecting to room {ctx.room.name}")
#     await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
 
#     # wait for the first participant to connect
#     participant = await ctx.wait_for_participant()
#     logger.info(f"starting voice assistant for participant {participant.identity}")


#     dg_model = "nova-3-general"
#     if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
#         # use a model optimized for telephony
#         dg_model = "nova-2-phonecall"
 
#     agent = VoicePipelineAgent(
#         vad=ctx.proc.userdata["vad"],
#         stt=deepgram_stt,
#         llm=openai.LLM.with_azure(),
#         tts=elevenlabs_tts,
#         chat_ctx=initial_ctx,
#     )
 
#     agent.start(ctx.room, participant)
 
#     usage_collector = metrics.UsageCollector()
 
#     @agent.on("metrics_collected")
#     def _on_metrics_collected(mtrcs: metrics.AgentMetrics):
#         metrics.log_metrics(mtrcs)
#         usage_collector.collect(mtrcs)
 
#     async def log_usage():
#         summary = usage_collector.get_summary()
#         logger.info(f"Usage: ${summary}")
 
#     ctx.add_shutdown_callback(log_usage)
 
#     # listen to incoming chat messages, only required if you'd like the agent to
#     # answer incoming messages from Chat
#     chat = rtc.ChatManager(ctx.room)
 
#     async def answer_from_text(txt: str):
#         chat_ctx = agent.chat_ctx.copy()
#         chat_ctx.append(role="user", text=txt)
#         stream = agent.llm.chat(chat_ctx=chat_ctx)
#         await agent.say(stream)
 
#     @chat.on("message_received")
#     def on_chat_received(msg: rtc.ChatMessage):
#         if msg.message:
#             asyncio.create_task(answer_from_text(msg.message))
 
#     await agent.say("Hey, how can I help you today?", allow_interruptions=True)
 
 
# if __name__ == "__main__":
#     cli.run_app(
#         WorkerOptions(
#             entrypoint_fnc=entrypoint,
#             prewarm_fnc=prewarm,
#         ),
#     )
 
 
 
 
 
 
import asyncio

from livekit import api
from livekit.protocol.sip import CreateSIPOutboundTrunkRequest, SIPOutboundTrunkInfo

async def main():
  livekit_api = api.LiveKitAPI()

  trunk = SIPOutboundTrunkInfo(
    name = "LiveTrunk",
    address = "pstn.twilio.com",
    numbers = ['+919891398961'],
    auth_username = "nakshatra@propellergv.com",
    auth_password = "9cmBVf:Vq_P4NVU"
  )

  request = CreateSIPOutboundTrunkRequest(
    trunk = trunk
  )

  trunk = await livekit_api.sip.create_sip_outbound_trunk(request)

  print(f"Successfully created {trunk}")

  await livekit_api.aclose()

asyncio.run(main())

livekit_api = api.LiveKitAPI(api_key="your_livekit_key", api_secret="your_livekit_secret", host="https://your.livekit.server")
