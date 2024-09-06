import asyncio
from msspeech import MSSpeech
from speech_generation.config_dao import config_dao


class Speech:
    def __init__(self) -> None:
        self.is_initialized = False
        self.mss = MSSpeech()

    async def __initialize(self):
        await self.mss.set_voice(config_dao.get_voice_name())
        await self.mss.set_pitch(config_dao.get_voice_pitch())
        await self.mss.set_volume(config_dao.get_voice_volume())
        await self.mss.set_rate(config_dao.get_voice_rate())
        self.is_initialized = True

    async def __generate(self, text: str, voice_file_name: str):
        if not self.is_initialized:
            await self.__initialize()

        await self.mss.synthesize(text, voice_file_name)

    def generate(self, text: str, voice_file_name: str):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.__generate(text, voice_file_name))
        finally:
            loop.close()
