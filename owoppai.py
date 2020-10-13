# -*- coding: utf-8 -*-

# note: this is only meant for use in gulag,
# i can't guarantee it'll work outside of that..
# atleast for now B)

import asyncio
import aiofiles
import aiohttp
import orjson
import os
import time

from constants.gamemodes import GameMode
from constants.mods import Mods

from console import plog, Ansi

__all__ = 'Owoppai',

class Owoppai:
    __slots__ = ('map_id', 'filename', 'mods',
                 'combo', 'nmiss', 'mode', 'acc',
                 'output')

    def __init__(self, map_id: int, **kwargs) -> None:
        self.map_id = map_id

        self.filename = f'.data/osu/{self.map_id}.osu'

        # TODO: perhaps make an autocalc mode w/ properties?
        self.mods: Mods = kwargs.pop('mods', Mods.NOMOD)
        self.combo: int = kwargs.pop('combo', 0)
        self.nmiss: int = kwargs.pop('nmiss', 0)
        self.mode: GameMode = kwargs.pop('mode', GameMode.vn_std)
        self.acc: float = kwargs.pop('acc', 100.00)

        # json output from oppai-ng
        self.output = {}

    async def __aenter__(self):
        if (not self.filename or not os.path.exists(self.filename)) and not await self.try_osuapi():
            plog(f'Could not find {self.filename}.', Ansi.LRED)
            return

        await self.calc()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return

    async def calc(self) -> None:
        st = time.time()
        # perform the calculations using current state
        args = [f'./pp/oppai {self.filename}']

        if self.mods > Mods.NOMOD:
            args.append(repr(self.mods))

        if self.combo:
            args.append(f'{self.combo}x')

        if self.nmiss:
            args.append(f'{self.nmiss}xM')

        if self.mode:
            mode_vn = self.mode.as_vanilla

            if mode_vn not in (0, 1):
                # oppai-ng only supports std & taiko
                self.output = {}
                return

            args.append(f'-m{mode_vn}')
            if mode_vn == GameMode.vn_taiko:
                args.append('-otaiko')

        if self.acc:
            args.append(f'{self.acc:.4f}%')

        # XXX: could probably use binary to save a bit
        # of time.. but in reality i should just write
        # some bindings lmao this is so cursed overall
        args.append('-ojson')

        proc = await asyncio.create_subprocess_shell(
            ' '.join(args),
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        output = orjson.loads(stdout.decode())
        self.output = output

        important = ('code', 'errstr', 'pp', 'stars')
        if any(i not in output for i in important) or output['code'] != 200:
            plog(f"oppai-ng error: {output['errstr']}", Ansi.LRED)

        await proc.wait() # wait for exit

    async def try_osuapi(self) -> bool:
        url = f'https://old.ppy.sh/osu/{self.map_id}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if not r or r.status != 200:
                    plog(f'Could not find map by id {self.map_id}!', Ansi.LRED)
                    return False

                content = await r.read()

        async with aiofiles.open(self.filename, 'wb') as f:
            await f.write(content)

        return True

    def _output(self, key: str, default):
        if key not in self.output:
            return default

        return self.output[key]

    @property
    def pp(self) -> float:
        return self._output('pp', 0.0)

    @property
    def acc_pp(self) -> float:
        return self._output('acc_pp', 0.0)

    @property
    def aim_pp(self) -> float:
        return self._output('aim_pp', 0.0)

    @property
    def speed_pp(self) -> float:
        return self._output('speed_pp', 0.0)

    @property
    def stars(self) -> float:
        return self._output('stars', 0.0)

    @property
    def acc_stars(self) -> float:
        return self._output('acc_stars', 0.0)

    @property
    def aim_stars(self) -> float:
        return self._output('aim_stars', 0.0)

    @property
    def speed_stars(self) -> float:
        return self._output('speed_stars', 0.0)