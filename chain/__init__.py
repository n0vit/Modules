from .messages_chain import MessagesChain, MessageChainStates
from .chain_model import ChainModel

__all__ = (MessagesChain,MessageChainStates,ChainModel)

from aiogram import __version__ as AIOGRAM_VERSION

AIOGRAM_VERSION = int(AIOGRAM_VERSION[0])
